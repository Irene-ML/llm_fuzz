
Start llm service: 
```
cd fuzzers/aflplusplus_llm/
// set LLM model
export LLM_MODEL=llama3.3
docker compose up --build
```

Run aflplusplus_llm fuzzer (In a separate window):
```
// Go back to the ancestor directory
./run_benchmarks.sh
```

Variables in ./run_benchmarks.sh:
1. Set benchmarks `benchmarks`
2. Set prompt shots `PROMPT_SHOTS`
3. Set experiment name `experiment_name`

