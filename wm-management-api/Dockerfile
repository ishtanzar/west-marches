FROM python:3.10-slim

WORKDIR /opt/wm-management-api

LABEL updated_at="202209151200"

RUN apt update && apt install -y gcc libev-dev

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./

CMD ["python", "./__main__.py"]
