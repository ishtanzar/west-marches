# syntax = docker/dockerfile:1.2
FROM python:3-slim

WORKDIR /opt/wm-manager-api

RUN apt update && apt install -y gcc libev-dev

COPY requirements.txt ./

RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

CMD ["python", "./__main__.py"]
