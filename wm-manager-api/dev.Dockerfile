# syntax = docker/dockerfile:1.2
FROM python:3-slim

WORKDIR /opt/wm-manager-api

LABEL updated_at="202209151200"

RUN apt update && apt install -y gcc libev-dev npm

RUN npm install pm2 -g

COPY requirements.txt ./
COPY dev-requirements.txt ./

RUN --mount=type=cache,target=/root/.cache/pip pip install -r dev-requirements.txt

CMD ["python", "./__main__.py"]
