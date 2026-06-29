#!/usr/bin/env python3

import subprocess, os, re
import redis

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6380
REDIS_PASSWORD = 'password'
REDIS_KEY = 'current_benchmark'
REDIS_KEY2 = 'prompt_shot'
PROMPT_SHOTS = 1

# Retry counter for the experiment name: 0 = no suffix, 1 = "-retry", >1 = "-retry<N>"
TEST_NUMBER = 0

# Benchmarks and other configurations
# Set benchmarks
benchmarks = ["freetype2_ftfuzzer"]
fuzzer = "aflplusplus_llm"
experiment_config = "local_experiment/test_run.yml"
crash_benchmarks = ["php_php-fuzz-parser_0dbedb", "mbedtls_fuzz_dtlsclient_7c6b0e", "libxml2_xml_e85b9b", "harfbuzz_hb-shape-fuzzer_17863b", "bloaty_fuzz_target_52948c"]

## ------- Helper functions to create unique test names -------
def get_max_total_time(config_path):
    """Read the active (uncommented) max_total_time from the experiment config."""
    with open(config_path) as f:
        for line in f:
            m = re.match(r'\s*max_total_time\s*:\s*(\d+)', line)
            if m:
                print(f"found time={m.group(1)}")
                return int(m.group(1))
    raise ValueError(f"max_total_time not found in {config_path}")

def get_trials(config_path):
    """Read the active (uncommented) trials count from the experiment config."""
    with open(config_path) as f:
        for line in f:
            m = re.match(r'\s*trials\s*:\s*(\d+)', line)
            if m:
                print(f"found trials={m.group(1)}")
                return int(m.group(1))
    raise ValueError(f"trials not found in {config_path}")
# Derive the run length in hours from the experiment config so the two stay in sync.
MAX_TOTAL_TIME = get_max_total_time(experiment_config)
# Read trials so the experiment name can encode non-default trial counts.
TRIALS = get_trials(experiment_config)
is_hour = True if MAX_TOTAL_TIME >= 3600 else False
TIME_INTERVAL = MAX_TOTAL_TIME // 3600 if is_hour else MAX_TOTAL_TIME // 60
print(f"max_total_time={MAX_TOTAL_TIME}s -> TIME_INTERVAL={TIME_INTERVAL}, is_hour={is_hour}")
if MAX_TOTAL_TIME % 3600:
    print(f"WARNING: max_total_time={MAX_TOTAL_TIME} is not a whole number of hours; TIME_INTERVAL={TIME_INTERVAL}")

## ------- Redis Configuration -------
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

## ------ Main Loop to Run Benchmarks -------
# Loop over each benchmark
for benchmark in benchmarks:
    # Record the current benchmark in Redis
    redis_client.set(REDIS_KEY, benchmark)
    print(f"Recorded benchmark '{benchmark}' in Redis.")

    # Run the benchmark experiment 
    first_half = benchmark.split("_")[0].split("-")[0]
    # set experiment_name
    #experiment_name = f"exp-1h3s-{first_half}"
    time_interval_str = f"{TIME_INTERVAL}h" if is_hour else f"{TIME_INTERVAL}m"
    trial_tag = "" if TRIALS == 3 else f"{TRIALS}t"
    crash_suffix = "-crash" if benchmark in crash_benchmarks else ""
    if TEST_NUMBER == 0:
        retry_suffix = ""
    elif TEST_NUMBER == 1:
        retry_suffix = "-rt"
    else:
        retry_suffix = f"-rt{TEST_NUMBER-1}"
    experiment_name = f"exp-{time_interval_str}{PROMPT_SHOTS}s{trial_tag}-{first_half}{crash_suffix}{retry_suffix}"
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




