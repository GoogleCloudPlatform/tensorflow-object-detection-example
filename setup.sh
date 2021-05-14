#!/bin/bash
MODEL_PATH="$1"
LABEL_PATH="$2"
DETECTION_THRESHOLD="$3"

app="object-detection"

docker build -t ${app} .
docker run -p 80:80 ${app} \
    -m ${MODEL_PATH} \
    -l ${LABEL_PATH} \
    -t ${DETECTION_THRESHOLD}