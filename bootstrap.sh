#!/bin/sh
export FLASK_APP=./index.py
source $(pip --venv)/bin/activate
flask run -h 0.0.0.0