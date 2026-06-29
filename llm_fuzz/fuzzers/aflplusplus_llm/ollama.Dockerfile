FROM ollama/ollama:0.5.7

COPY ./run_ollama.sh /tmp/run_ollama.sh

WORKDIR /tmp

RUN chmod +x run_ollama.sh

EXPOSE 11434