# syntax = docker/dockerfile:1.2
FROM python:3.10-slim

WORKDIR /opt/wm-worker

LABEL updated_at="202210231200"

RUN apt update && apt install -y gcc libev-dev npm

RUN npm install pm2 -g

COPY ./ ./

RUN --mount=type=cache,target=/root/.cache/pip pip install -r dev-requirements.txt

CMD ["python", "./__main__.py"]
