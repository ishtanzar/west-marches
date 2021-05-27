FROM ubuntu:groovy

WORKDIR /opt/redbot

COPY requirements.txt ./

RUN apt update && \
  DEBIAN_FRONTEND=noninteractive TZ=Europe/Paris apt install -y build-essential python3.8 python3-pip libcudart11.0
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./

CMD ["python3", "./__main__.py"]
