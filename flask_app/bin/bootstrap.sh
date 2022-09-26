#!/bin/sh

#export FLASK_APP=./app.py
#source $(pip --venv)/bin/activate


gunicorn wsgi:app --bind 0.0.0.0:8080 --workers=4