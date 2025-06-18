#!/bin/sh

docker build -t steggy .
docker run --rm -p 5000:5000 -it steggy
