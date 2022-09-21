# syntax = docker/dockerfile:1.2
FROM ubuntu:20.04

WORKDIR /opt/redbot

LABEL updated_at="202209160900"

RUN apt update && \
  DEBIAN_FRONTEND=noninteractive TZ=Europe/Paris apt install -y build-essential python3.8 python3-pip libcudart10.1 locales npm

RUN locale-gen fr_FR.UTF-8

RUN npm install pm2 -g

COPY dev-requirements.txt ./
COPY requirements.txt ./

RUN --mount=type=cache,target=/root/.cache/pip pip install -r dev-requirements.txt

CMD ["redbot"]
