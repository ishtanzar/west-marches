# syntax = docker/dockerfile:1.2
FROM python:3.10-slim

WORKDIR /opt/wm-discord-workaround

LABEL updated_at="202210220900"

RUN apt update && apt install -y gcc libev-dev npm

RUN npm install pm2 -g

COPY wm-discord-workaround/requirements.txt ./
COPY wm-discord-workaround/dev-requirements.txt ./

#COPY wm-management-api-client/ ./wm-management-api-client

RUN pip install --no-cache-dir -r dev-requirements.txt

CMD ["python", "./__main__.py"]
