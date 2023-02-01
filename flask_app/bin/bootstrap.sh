#!/bin/sh

#export FLASK_APP=./app.py
#source $(pip --venv)/bin/activate

# cd ../  #uncomment this only to run from wsgi.py. This should remain commented when containerized
gunicorn wsgi:app --bind 0.0.0.0:5000 --workers=4
