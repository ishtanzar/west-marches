# syntax = docker/dockerfile:1.2
FROM ubuntu:20.04

WORKDIR /opt/redbot

RUN apt update && \
  DEBIAN_FRONTEND=noninteractive TZ=Europe/Paris apt install -y build-essential python3.8 python3-pip libcudart10.1 locales

RUN locale-gen fr_FR.UTF-8

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

CMD ["redbot"]
