# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y libpq-dev && apt-get install python3-dev -y && apt-get install build-essential -y

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY ./api app/api
COPY ./bin app/bin
COPY ./classifiers app/classifiers
COPY wsgi.py app/wsgi.py

WORKDIR /app

EXPOSE 5000
ENTRYPOINT ["bash", "/app/bin/bootstrap.sh"]