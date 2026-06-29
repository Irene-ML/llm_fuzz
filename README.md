# Semantic-Aware LLM Fuzzing
Semantic-aware LLM fuzzing is a framework that connects AFL++ to off-the-shelf reasoning LLMs via Redis and Docker, effectively harmonizing CPU- and GPU-driven components without fine-tuning. It is packaged for automated deployment on Google's [Fuzzbench](https://github.com/google/fuzzbench), enabling reproducible and large-scale evaluation across diverse binary targets.

It supports the following features:
* Integrates LLM inference directly into the fuzzing pipeline.
* Enables asynchronous communication between the decoupled LLM and fuzzer components.
* Automates fuzzer deployment on Google's FuzzBench framework.

Paper: https://arxiv.org/pdf/2509.19533

## Overview
This framework investigates whether reasoning-capable LLMs can leverage their pretrained knowledge to recognize input formats, infer structural constraints, generate semantically meaningful mutations and improve fuzzing effectiveness through prompt engineering.

The framework integrates:
* AFL++
* Google FuzzBench
* Ollama
* Redis
* Open-source reasoning LLMs
through a scalable microservices architecture.

### File Structure
The `llm_fuzz` directory in the root folder is cloned from FuzzBench at commit `4efcb5aa6ae51a7b1a298387597c2b0c42d5ac12`. From this FuzzBench version, we temporarily fixed a report generation bug ([google#1896](https://github.com/google/fuzzbench/issues/1896)) and a Python version conflict encountered during the Docker image build. Then, we integrated our LLM-guided fuzzer, `aflplusplus_llm`, into `llm_fuzz/fuzzers/`.

For automated deployment, we added `test_run.yml` file to the `/local_experiment` directory to manage required local experiment configurations such as running trials, duration and locations to save results. Additionally, we provided a `run_benchmark.sh` script to ease the deployment by allowing users to customize the deployment parameters (e.g., setting the experiment name, prompt shot count, selected fuzzers and targeted benchmarks for running). 

Finally, the `/artifacts` directory contains generated experiment artifacts, such as CSV files used for data analysis.

Our major modifications to FuzzBench are located in the following directories:

```
llm_fuzz/
│
├──llm_fuzz/
│    ├── fuzzers/
│    │      └── aflplusplus_llm/
│    │                     
│    ├── local_experiment
│    │      └── test_run.yml
│    │
│    └── run_benchmarks.sh
│
├──artifacts/
│
└── README.md
```

## Environment Settings
We have conducted running on a high-performance server __Ubuntu 20.04.2 LTS__, equipped with an __Intel Xeon Gold 5218 CPU (64 cores)__, 754 GiB of RAM, 3 TB of disk storage, and two __NVIDIA Quadro RTX 6000 GPUs__ (24 GiB VRAM each).

Compatible software versions:
* Docker: 20.10.21
* Ollama: 0.5.7
* Redis: 7.0.x

### Configuration Customizations
1. Go to `local_experiment/test_run.yml`, required to set the following variables:

| Variables | Description | Value
|---------|---------|---------|
| `trials` | The number of trials of a fuzzer-benchmark pair | `3`/`5` |
| `max_total_time` | The amount of time in seconds that each trial is run for. 1 day = 24 * 60 * 60 = 86400 | `3600`/`14400`/`86400`/`259200`  |
| `experiment_filestore` | The local experiment folder that will store most of the experiment data. Use an absolute path.  | `/path/to/save/test-result/experiment-data`|
| `report_filestore` | The local report folder where HTML reports and summary data will be stored. Use an absolute path.| `/path/to/save/test-result/report-data` |

2. Go to `run_benchmarks.sh`, change the following values for variables:

| Variables | Description | Value | Required |
|---------|---------|---------|---------|
| `PROMPT_SHOTS` | Prompt shot integer for LLM prompt generation  | `0`/`1`/`3` | Yes |
| `benchmarks` | Target benchmarks to fuzz; supports running multiple benchmarks in one experiment | `["freetype2_ftfuzzer", "mbedtls_fuzz_dtlsclient_7c6b0e"]` | Yes |
| `TEST_NUMBER` | Retry counter integer for the experiment name: `0` = no suffix, `1` = "-retry", `>1` = "-retry<N>"  | `0`/`1`/`2`...| Optional |
| `experiment_name`  | Unique name for your experiment. Must be ≤ 30 characters long. Allowed characters: lowercase letters (a-z), numbers (0–9), and hyphens (-). No underscores (_). | `f"exp-{time_interval_str}{PROMPT_SHOTS}s{trial_tag}-{first_half}{crash_suffix}{retry_suffix}"` | Optional |

3. (OPTIONAL) Go to `fuzzers/aflplusplus_llm/AFLplusplus/custom_mutators/aflppllm/aflpp.c` change the `REDIS_HOST` to your server IP if the fuzzer couldn't connect to Redis.
```
#define REDIS_HOST "127.0.0.1" # Change to your server IP
```


## Usage
### 1. Setup `llm_fuzz`  
1. Download this github repo locally: `git clone git@github.com:Irene-ML/llm_fuzz.git`
2. Set up Docker environment according to [FuzzBench's documentation](https://google.github.io/fuzzbench/getting-started/prerequisites/#docker).
3. Follow the "Make" steps below instead of the instructions in the FuzzBench documentation.
```
sudo apt-get install python3.10-dev python3.10-venv
sudo apt-get install build-essential

# additional:
sudo apt-get install ffmpeg libsm6 libxext6  -y

# For windows deployment only:
git config --global core.autocrlf false

cd llm_fuzz/llm_fuzz

source .venv/bin/activate
make install-dependencies

# headless QT error
export QT_QPA_PLATFORM=offscreen
make presubmit
# if any pytest error, run this to see more logs:
# python3 -m pytest -vvv -x -s 
```
### 2. Docker Image Build
Before building images, you may want to clean up the docker cache using `docker builder prune`.
Update base image: 
```
make base-image
```
### 3. Deployment
1. In a separate window, start the LLM component (Ollama, Redis and `llm_fuzz` microservices) in Docker:
```
# Go to this project's path containing LLM, absolute path: `<HomeLocation>/llm_fuzz/llm_fuzz/fuzzers/aflplusplus_llm`
cd llm_fuzz/llm_fuzz/fuzzers/aflplusplus_llm 

export LLM_MODEL=llama3.3
docker-compose up -d --build
```
2. Sanity check:
```
# Check llm_fuzz log:
docker logs -f aflplusplus_llm_llm_fuzz
# Check Ollama log:
docker logs -f aflplusplus_llm_llm_service
```
**Note:** When seeing `Starting message consumer...` or `Queue is empty after 50s timeout. Waiting...` in the `aflplusplus_llm_llm_fuzz` log, move to the next step. 

3. Change or review your configuration setups in `test_run.yml` and `run_benchmarks.sh`. Refer to "[Configuration Customizations](#configuration-customizations)"

4. Deploy fuzzer component using `run_benchmark.sh`. 
Do the following in the original window where you built images:
```
# Go to this project's path and make sure you are in the python virtual environment:
# cd llm_fuzz/llm_fuzz
# source .venv/bin/activate

./run_benchmarks.sh
```

## Model Versions
| Model | Ollama Tag | Size
|---------|---------|---------|
| Llama3.3 | llama3.3:70b | 43GiB |
| DeepSeek-R1-Distill-Llama | deepseek-r1:70b | 43GiB |
| QwQ-32B | qwq | 20GiB |
| Gemma3-27B | gemma3:27b | 17GiB |


## Experimental Artifacts
Contains experimental results, statistical analysis tables and log analysis csv files.
```
artifacts/
├── fuzzbench-tests-table*.csv
├── stats/
│    └── *stats.csv
└── log-analysis-table.csv
```