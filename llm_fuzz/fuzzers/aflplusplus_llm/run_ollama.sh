#!/bin/bash

export CUDA_VISIBLE_DEVICES=6,7

echo "Starting ollama server..."
ollama serve &

echo "Waiting for ollama server to be active..."
while [ "$(ollama list | grep 'NAME')" == "" ]; do
  sleep 1
done

echo "Loading llama3.3"
ollama run llama3.3

echo "Llama3.3 is loaded!"

