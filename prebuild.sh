#!/bin/bash

echo "prebuild.sh: Installing Python dependencies"
python --version
python -m venv env
source env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
