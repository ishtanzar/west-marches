FROM python:3-slim

WORKDIR /opt/manager-api

COPY requirements.txt ./

RUN apt update && apt install -y gcc libev-dev
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./

CMD ["python", "./__main__.py"]
