#!/usr/bin/env python3

import subprocess, os
import redis

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = 'password'
REDIS_KEY = 'current_benchmark'
REDIS_KEY2 = 'prompt_shot'
PROMPT_SHOTS = 1

# Benchmarks and other configurations
# Set benchmarks
benchmarks = ["freetype2_ftfuzzer", "proj4_proj_crs_to_crs_fuzzer", "libpng_libpng_read_fuzzer", "curl_curl_fuzzer_http", "libpcap_fuzz_both", "openh264_decoder_fuzzer", "openthread_ot-ip6-send-fuzzer"]
fuzzer = "aflplusplus_llm"
experiment_config = "local_experiment/test_run.yml"

# Connect to Redis with password authentication
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

# redis_client.set(REDIS_KEY, "freetype2_ftfuzzer")

def clear_redis_queues():
    """Clears all relevant Redis queues after each benchmark."""
    redis_queues = ["C2P", "P2C"]  # Add more keys if needed
    for queue in redis_queues:
        redis_client.delete(queue)
        print(f"Cleared Redis queue: {queue}")

os.environ['PYTHONPATH'] = '.'
allow_uncommitted_changes = '--allow-uncommitted-changes'

# Set prompt shots
redis_client.set(REDIS_KEY2, PROMPT_SHOTS)

# Loop over each benchmark
for benchmark in benchmarks:
    # Record the current benchmark in Redis
    redis_client.set(REDIS_KEY, benchmark)
    print(f"Recorded benchmark '{benchmark}' in Redis.")

    # Run the benchmark experiment 
    first_half = benchmark.split("_")[0].split("-")[0]
    # set experiment_name
    #experiment_name = f"exp-1h3s-{first_half}"
    experiment_name = f"qwq-1h1s-{first_half}"
    print(f"Experiment_name: {experiment_name}")
    
    # Build image
    build_command = ["make", f"build-{fuzzer}-{benchmark}"]
    subprocess.run(build_command, check=True)
    
    command = [
        "python3", "experiment/run_experiment.py",
        "--experiment-config", experiment_config,
        "--benchmarks", benchmark,
        "--experiment-name", experiment_name,
        "--fuzzers", fuzzer,
        "--concurrent-builds", '1',
        allow_uncommitted_changes
    ]

    print(f"Running benchmark: {benchmark}")
    subprocess.run(command, check=True)

    # Clear Redis queues after the benchmark run
    clear_redis_queues()
    print(f"Finished benchmark: {benchmark}, Redis queues cleared.\n")

    # copy logs
    log_location = './fuzzers/aflplusplus_llm/logs'
    copy_command = ["cp", f"{log_location}/mutation_logs.txt", f"{log_location}/1new_mutation_logs_{experiment_name}.txt"]
    subprocess.run(copy_command, check=True)
    print(f"Copied mutation logs, location: {log_location}/1new_mutation_logs_{experiment_name}.txt")

    # clear built images and cache
    clean_cache_command = ["docker", "builder", "prune", "-f"]
    subprocess.run(clean_cache_command, check=True)
    print(f"Cleaned docker build cache.")




