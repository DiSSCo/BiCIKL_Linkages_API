#!/bin/sh

#export FLASK_APP=./app.py
#source $(pip --venv)/bin/activate

gunicorn wsgi:app --bind 0.0.0.0:5000 --workers=4