#!/bin/bash

# export CUDA_VISIBLE_DEVICES=5,6,7

echo "Starting ollama server..."
ollama serve &

SERVER_PID=$!

echo "Waiting for ollama server to be active..."
while [ "$(ollama list | grep 'NAME')" == "" ]; do
  sleep 1
done

echo "Ollama server is active. Proceeding with loading the model."

echo "Loading llama3.3"
ollama run llama3.3

echo "Llama3.3 is loaded!"

wait $SERVER_PID
