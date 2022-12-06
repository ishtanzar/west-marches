# syntax = docker/dockerfile:1.2
FROM ubuntu:20.04

LABEL updated_at="202210220900"

RUN apt update && \
  DEBIAN_FRONTEND=noninteractive TZ=Europe/Paris apt install -y build-essential python3.8 python3-pip libcudart10.1 locales npm

RUN locale-gen fr_FR.UTF-8

RUN npm install pm2 -g

COPY wm-discord-workaround/ ./wm-discord-workaround
COPY wm-management-api-client/ ./wm-management-api-client

RUN --mount=type=cache,target=/root/.cache/pip pip install -r ./wm-discord-workaround/dev-requirements.txt
