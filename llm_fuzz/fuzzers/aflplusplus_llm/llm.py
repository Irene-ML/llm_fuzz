import redis
import llm_ollama
import json, re
import traceback
import os
from ollama import Client
from logger_config import get_logger

logger = get_logger(__name__)

MAX_QUEUE_SIZE = 30 
MAX_MESSAGE_SIZE = 2000
REDIS_KEY = 'current_benchmark'
REDIS_KEY2 = 'prompt_shot'

# load env variable
library_info = os.environ.get('BENCHMARK_NAME')
print(f"Loaded library info: {library_info}")
model = os.environ.get('LLM_MODEL')
print(f"Loaded LLM model name: {model}")

# Connect to Ollama
service_host = 'localhost'
service_port = 11434

ollama_client, model = llm_ollama.load_model(service_host, service_port, model)

# Connect to Redis
redisdb = redis.Redis(host='localhost', port=6379, password='password', decode_responses=False)

# # load library_info for LLM
# with open("library_info.json", "r") as file:
#     library_info = json.dumps(json.load(file))

# extract the mutated buffer from LLM response
def parse_response(response):
    # pattern = r"\$([0-9a-fA-F]+)"
    pattern = r'#### Final Output:\s*(.*)'

    match = re.search(pattern, response, re.DOTALL)
    if match:
        hex_mutated_buffer = match.group(1).strip()
        print(f"hex mutated_buffer: {hex_mutated_buffer}, type: {type(hex_mutated_buffer)}")
        logger.info(f"hex mutated_buffer: {hex_mutated_buffer}")

        try:
            mutated_buffer = bytes.fromhex(hex_mutated_buffer)
            logger.info(f"mutated_buffer: {mutated_buffer}")
            print(f"mutated_buffer: {mutated_buffer}")
            return mutated_buffer
        except Exception as err:
            print(f"Exception encountered: {err}. hex cannot be converted to bytes. hex: {hex_mutated_buffer}. hex length: {len(hex_mutated_buffer)}")
            if len(hex_mutated_buffer) % 2 != 0:
                hex_mutated_buffer = hex_mutated_buffer+'0'
                mutated_buffer = bytes.fromhex(hex_mutated_buffer)
                logger.info(f"Exception encountered, converted mutated_buffer: {mutated_buffer}")
                print(f"Converted mutated_buffer: {mutated_buffer}")
                return mutated_buffer
            return None
    else:
        return None

# Consume messages from Redis
def consume_messages():

    message_count=0
    while True:
        try:
            consumed_message = redisdb.blpop('C2P', timeout=30)
        except:
            consumed_message = repr(consumed_message)
            print(f"Decoded consumed message: {consumed_message}")

        if consumed_message:
            # message is in tupple for blpop.
            print(f"Consumed: {consumed_message}, message type: {type(consumed_message)}")
            redisdb.ltrim('C2P', -MAX_QUEUE_SIZE, -1)
            message_count+=1

            # PONG
            redisdb.ltrim('P2C', -MAX_QUEUE_SIZE, -1)

            # ask LLM model
            message = consumed_message[1]
            logger.info(f"Consumed_message: {message}")

            mutate_message = message[:MAX_MESSAGE_SIZE]
            rest_message = message[MAX_MESSAGE_SIZE:]
            print(f"mutate_message: {mutate_message} \nrest_message: {rest_message}")
            
            mutate_result = None
            try:
                hex_msg = mutate_message.hex()
                
                try:
                    library_info = redisdb.get(REDIS_KEY)
                    if library_info is None:
                        print("Error: Could not retrieve library info from Redis.")
                        return "Error: Could not retrieve library info from Redis."
                    library_info = library_info.decode('utf-8') 
                    prompt_shot = redisdb.get(REDIS_KEY2)
                    if prompt_shot is None:
                        print("Error: Could not retrieve prompt shot from Redis.")
                        return "Error: Could not retrieve prompt shot from Redis."
                    prompt_shot = int(prompt_shot.decode('utf-8'))
                except redis.RedisError as e:
                    print(f"Error: Failed to connect to Redis or retrieve key: {str(e)}")
                    return f"Error: Failed to connect to Redis or retrieve key: {str(e)}"

                response = llm_ollama.ask_ollama(service_host, service_port, hex_msg, library_info, model, prompt_shot)
                print(f"### ollama response: {response}")
                logger.info(f"### ollama response: {response}, library_info: {library_info}")
            except Exception as err:
                print(f"Response timed out. Exception encountered: {err}.")
                logger.error(f"Response timed out exception: {err}. library_info: {library_info}")
            
            try:
                mutate_result = parse_response(response)
            except Exception as err:
                print(f"Parsing issue. Exception encountered: {err}.")
                logger.error(f"Parsing exception: {err}. library_info: {library_info}")

            # send the message back to fuzzer
            if (mutate_result):
                mutate_result = mutate_result + rest_message
                print(f"mutated result: {mutate_result}")
                logger.info(f"mutated_result: {mutate_result}")
                redisdb.rpush('P2C', mutate_result)

        else:
            print("Queue is empty after 30s timeout. Waiting...")

if __name__ == "__main__":
    print("Starting message consumer...")
    consume_messages() 
    
