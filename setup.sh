#!/bin/bash
app="object-detection"

docker build -t ${app} .
docker run -p 56733:80 ${app}