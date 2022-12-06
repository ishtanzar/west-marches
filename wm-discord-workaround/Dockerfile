FROM ubuntu:20.04

WORKDIR /opt/discord-bot

RUN apt update && \
  DEBIAN_FRONTEND=noninteractive TZ=Europe/Paris apt install -y build-essential python3.8 python3-pip libcudart10.1 locales

RUN locale-gen fr_FR.UTF-8

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src /opt/discord-bot

CMD ["python", "__main__.py"]
