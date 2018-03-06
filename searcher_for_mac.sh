#!/usr/bin/env bash

set -e

category=$1
terms=$2
marketplace=$3

mkdir -p /Users/$USER/Documents/amazon_mws

docker run -v /Users/$USER/Documents/amazon_mws:/mnt/amazon_mws aws_searcher:latest \
     python3.6 --category $category --terms $terms --market $marketplace
