#!/bin/sh
export FLASK_APP=./app.py
source $(pip --venv)/bin/activate
flask run -h 0.0.0.0