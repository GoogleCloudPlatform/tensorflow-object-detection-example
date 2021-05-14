#!/bin/bash
MODEL_PATH="$1"
LABEL_PATH="$2"
THRESHOLD="$3"

app="object-detection"

docker build -t ${app} .
docker run -p 56733:80 ${app} \
    -m ${MODEL_PATH} \
    -l ${LABEL_PATH} \
    -t ${THRESHOLD}