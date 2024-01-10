#!/bin/bash

# set this to the directory of the script
path=

if [ ! -d "$path/venv" ]; then
  python3 -m venv $path/venv
  source $path/venv/bin/activate
  pip install -r $path/requirements.txt
else
  source $path/venv/bin/activate
fi

$path/venv/bin/python $path/app/main.py

deactivate