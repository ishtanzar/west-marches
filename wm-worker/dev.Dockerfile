# syntax = docker/dockerfile:1.2
FROM python:3.10-slim

WORKDIR /opt/wm-worker

LABEL updated_at="202307060800"

RUN apt update && apt install -y gcc libev-dev npm

RUN npm install pm2 -g

COPY ./wm-utils /opt/project/wm-utils
COPY ./wm-worker /opt/project/wm-worker

RUN pip install --no-cache-dir -r /opt/project/wm-worker/dev-requirements.txt

CMD ["python", "./__main__.py"]
