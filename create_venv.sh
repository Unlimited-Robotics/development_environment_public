#!/bin/bash

sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update
sudo apt-get install -y python3.10 python3-virtualenv

rm -rf ./venv

virtualenv venv --python="python3.10" --prompt="ur_dev_env"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    source venv/local/bin/activate
fi

pip3 install -r requirements.txt
