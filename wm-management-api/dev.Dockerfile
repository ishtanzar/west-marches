# syntax = docker/dockerfile:1.2
FROM python:3-slim

WORKDIR /opt/wm-management-api

LABEL updated_at="202209151200"

RUN apt update && apt install -y npm ca-certificates curl gnupg && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo \
        "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
        "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null

RUN apt update && apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

RUN npm install pm2 -g

COPY ./wm-utils /opt/project/wm-utils
COPY ./wm-management-api /opt/project/wm-management-api

RUN --mount=type=cache,target=/root/.cache/pip pip install -r /opt/project/wm-management-api/dev-requirements.txt

CMD ["python", "./__main__.py"]
