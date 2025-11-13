import ollama
from ollama import Client
from ollama import chat
from ollama import ChatResponse
import timeout_decorator
from logger_config import get_logger

logger = get_logger(__name__)

print(ollama.list())

instructions = """

    You are a mutator designed to enhance fuzzing input for a program, aiming to maximize code coverage. Your task is to mutate a hexadecimal string (converted from a Python byte string) while preserving the plausibility of the original file format. Follow these steps:

    1. **Analyze the Input Buffer**:
    - Decode the hexadecimal string into bytes and identify structural or syntactic patterns, including:
        - Key fields (e.g., headers, delimiters, or magic numbers).
        - Regions constrained by specific values or patterns (e.g., checksums, length fields).
        - Known positional or structural dependencies based on provided library information.
    - Note areas critical to format validity and regions suitable for mutation.

    2. **Select Mutation Targets**:
    - Identify byte sequences likely to trigger alternate execution paths when altered, focusing on:
        - Conditional values or length fields.
        - Regions with less strict format constraints.
    - Prioritize mutations that are likely to explore untested code paths while keeping the file format plausible.

    3. **Apply Mutations**:
    - Mutate the identified bytes strategically to maximize code coverage.
    - Ensure the mutated byte string remains consistent with the overall structural requirements of the original file format.

    ### Required Output Format:
    - **Analysis**: Provide a brief analysis of the input buffer.
    - **Final Output**: Return the mutated buffer as a single Python hexadecimal string. No additional code, comments, or text should accompany it. The final output should be in the exact format of "Final Output" in the example output.

    ### Example Output:
    #### Analysis:
    <Concise analysis of the input buffer and mutation strategy>
    #### Final Output:
    <mutated buffer hexadecimal>


    """

example1 = f"""
 
    ### Example 1:
    
    input buffer: 1050982bef7f0000374c030000000000f758946700000000fc69
    library info: jsoncpp_jsoncpp_fuzzer
    
    #### Your analysis process:
    The input buffer `1050982bef7f0000374c030000000000f758946700000000fc69` appears to be a JSON file in binary format. Upon decoding the hexadecimal string into bytes, we notice that it starts with a magic number `10 50 98 2b`, which could indicate the beginning of a JSON object. The presence of `7f 00 00 03` and `74 58 94 67` suggests potential key fields or delimiters within the JSON structure.

    Given the library information `jsoncpp_jsoncpp_fuzzer`, we can infer that this binary data is intended to be parsed by the JsonCpp library. The mutation strategy should focus on altering conditional values, length fields, and regions with less strict format constraints while maintaining the overall structural integrity of the JSON file.

    To maximize code coverage, mutations will target these areas to simulate various parsing scenarios without violating the JSON format's basic structural requirements.

    #### Final Output:
    1050982bf77f0000374c0301000000f75894670000000ffc69


"""

example2 = f"""

    ### Example 2:
    
    input buffer: 10a0484ad47f0000c541000000000000a5
    library info: openh264_decoder_fuzzer

    #### Analysis:
    The input buffer `10a0484ad47f0000c541000000000000a5` appears to be a binary file related to video decoding, given the library information `openh264_decoder_fuzzer`. Upon examining the hexadecimal string, we notice it starts with `10 a0 48 4a`, which might represent a header or magic number specific to H.264 video format. The sequence `d4 7f 00 00` could indicate a delimiter or a marker within the file structure, while `c5 41 00 00` may signify a length field or another form of metadata.

    Considering the library is designed for fuzzing an H.264 decoder, our mutation strategy should aim at modifying bytes that could influence parsing decisions without rendering the file completely invalid. This includes altering potential length fields, conditional values, and areas with less strict format constraints to explore different execution paths in the decoder.

    #### Final Output:
    10a0484ad47f0000c541010000000000a5
    
"""

example3 = f"""
    
    ### Example 3:
    
    input buffer: 10808c5e3a7f000021e100000000000010cd3e02000000001080000000000000b30e00000000000064000000000000009511966700000000102202000000000080000000000000001003490200000000100000000000000080abd4663a7f000020cd3e0200000000008000000000000028cd3e0200010000800c0000040000000008000000000000b30e000000000000d8479f663a7f00008b05000000000000000000000000000010209f663a7f0000ffffffff00000000184d3e0200000000810e000000000000810e00000000000010209f663a7f00005c224300
    library info: freetype2_ftfuzzer

    #### Analysis:
    The input buffer appears to be a binary file format, potentially related to font files given the association with `freetype2_ftfuzzer`. Upon decoding the hexadecimal string into bytes, several key fields and patterns are identified:

    - **Magic Numbers**: Specific byte sequences that could indicate the start of particular sections or data types within the file.
    - **Length Fields**: Areas that specify the size of subsequent data blocks, which are crucial for parsing and interpreting the file correctly.
    - **Checksums or Validation Bytes**: Although not explicitly identified, regions with seemingly random or calculated values might serve as integrity checks.

    Given this analysis, mutation targets include conditional values (e.g., length fields), regions with less strict format constraints, and areas that could potentially trigger alternate execution paths when altered. The strategy involves modifying these targets to explore untested code paths while maintaining the file's overall structural integrity.

    #### Final Output:
    10808c5e3a7f000021e100000000000010cd3e02000000001080000000000000b30e00000000000064000000000000009511966700000000102202000000000080000000000000001003490200000000100000000000000080abd4663a7f000020cd3e0200000000008000000000000028cd3e0200010000800c0000040000000008000000000000b30e000000000000d8479f663a7f00008b05000000000000000000000000000010209f663a7f0000ffffffff00000000184d3e0200000000810e000000000000810e00000000000010209f663a7f00005c224300000000000000000
    
    """

instructions_system = """

    You are a mutator designed to enhance fuzzing input for a program, aiming to maximize code coverage. Your task is to mutate a hexadecimal string (converted from a Python byte string) while preserving the plausibility of the original file format. Follow these steps:
    
    1. **Analyze the Input Buffer**:
    - Decode the hexadecimal string into bytes and identify structural or syntactic patterns, including:
        - Key fields (e.g., headers, delimiters, or magic numbers).
        - Regions constrained by specific values or patterns (e.g., checksums, length fields).
        - Known positional or structural dependencies based on provided library information.
    - Note areas critical to format validity and regions suitable for mutation.

    2. **Select Mutation Targets**:
    - Identify byte sequences likely to trigger alternate execution paths when altered, focusing on:
        - Conditional values or length fields.
        - Regions with less strict format constraints.
    - Prioritize mutations that are likely to explore untested code paths while keeping the file format plausible.

    
    3. **Apply Mutations**:
    - Mutate the identified bytes strategically to maximize code coverage.
    - Ensure the mutated byte string remains consistent with the overall structural requirements of the original file format.
    
    ### **Strict Output Formatting Requirements**:
    - **Analysis (Required)**: 
        - Before producing the final output, provide a **brief analysis** of the input buffer.
    - **Final Output must strictly follow this format:** 
        - must always begin with exactly **four (`####`) hash symbols**.
        - must contain **only** the mutated buffer as a valid **plain text hexadecimal**
        - **MUST NOT** wrap the output in backticks (`) or markdown
        - **MUST NOT** use any code blocks or additional formatting.
        - **MUST NOT** provide any analysis, explanations, comments, or descriptions.
    
    If the response does not meet above formatting requirements, it is **incorrect**.
      
    """

examples = [example1, example2, example3]
    
def load_model(server, port, model):
    if model is None or not model:
        model = 'llama3.3'
    try:
        client = Client(host=f'http://{server}:{port}')
        client.show(model)
    except Exception as err:
        print(f"Exception encountered: {err}. Attempting to pull the model...")
        client = Client(host=f'http://{server}:{port}')
        client.pull(model)
        print(f"Successfully loaded model: {model}")
    return client, model


@timeout_decorator.timeout(600, timeout_exception=StopIteration)
def ask_ollama(server, port, hex_msg, library_info, model, shot=0):
    print(f"server: {server}, port: {port}, message: {hex_msg}, library_info: {library_info}, model: {model}, shot: {shot}")
    logger.info(f"server: {server}, port: {port}, message: {hex_msg}, library_info: {library_info}, model: {model}, shot: {shot}")
    if shot == 0:
        response: ChatResponse = Client(
                host=f'http://{server}:{port}'
            ).chat(model=model, 
            options = {
                'temperature': 0
            }, 
            messages=[
            {
                'role': 'system',
                'content': instructions,
            },
            {
                'role': 'user',
                'content': f"input_buffer: {hex_msg}, library_info: {library_info}"
            }],
            # stream=True,
        )
    else:
        example_intro = "Here is an example mutation:\n" if shot == 1 else "Here are some examples for mutation:\n"
        example_texts = example_intro.join(examples[:shot])

        instructions_user = f"""
            
            {example_texts}
            
            Now, mutate the following input:
            
            input buffer: {hex_msg}
            library info: {library_info}
            
            #### Your analysis process:
            <Here, the model generates analysis>
            
            #### Final Output:
            <Here, the model should only return the mutated buffer as plain text hexadecimal>

    
            ### **Strict Requirement**:
            - The **####Analysis section is required** before `#### Final Output`
            - If your final output contains **explanations, comments, formatting, or extra words**, it is **incorrect**.
            - The **only acceptable response** after `#### Final Output:` is **the mutated hexadecimal string**.

        """
        response: ChatResponse = Client(
                host=f'http://{server}:{port}'
            ).chat(model=model,  
            options = {
                'temperature': 0
            }, 
            messages=[
            {
                'role': 'system',
                'content': instructions_system,
            },
            {
                'role': 'user',
                'content': instructions_user,
            }],
            # stream=True,
        )

    if not response:
        logger.info(f"No response for messasge: {hex_msg}")
        return None
    if 'error' in response:
        logger.info(f"Error in response for message: {hex_msg}")
        return f"Error: {response['error']}"    
    # print(f"response: {response['message']['content']}")
    return response['message']['content']

if __name__ == "__main__":
    input_buffer=b'\x06\x00\x00\x00utf16lebom.xml\\\n<\\\n'
    hex_msg = input_buffer.hex()
    client = load_model('127.0.0.1', 11434, 'llama3.3')
    response = ask_ollama('127.0.0.1', 11434, hex_msg, library_info, 'llama3.3')
    print(f"response: {response}")

