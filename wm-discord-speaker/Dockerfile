FROM ubuntu:groovy

WORKDIR /opt/redbot

RUN apt update && \
  DEBIAN_FRONTEND=noninteractive TZ=Europe/Paris apt install -y build-essential python3.8 python3-pip libcudart11.0

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["redbot"]
