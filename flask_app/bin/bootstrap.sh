#!/bin/sh

#export FLASK_APP=./app.py
#source $(pip --venv)/bin/activate
#cd ../
gunicorn wsgi:app --bind 0.0.0.0:5000 --workers=4