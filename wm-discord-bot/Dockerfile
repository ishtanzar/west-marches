FROM ubuntu:22.04

WORKDIR /opt/redbot

LABEL updated_at="202309120900"

RUN apt update && \
    apt -y install software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    DEBIAN_FRONTEND=noninteractive TZ=Europe/Paris apt install -y git build-essential python3.9 python3.9-dev python3.9-venv python3-pip locales

RUN locale-gen fr_FR.UTF-8

COPY wm-discord-bot/requirements.txt ./

ENV VIRTUAL_ENV=/opt/venv

RUN python3.9 -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --no-cache-dir -r requirements.txt

COPY wm-discord-bot/src /opt/redbot/cogs

CMD ["redbot"]
