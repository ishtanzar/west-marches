FROM python:3.10-slim

WORKDIR /opt/wm-worker

LABEL updated_at="202210231200"

RUN apt update && apt install -y gcc libev-dev git

COPY wm-worker/common-requirements.txt ./
COPY wm-worker/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./

CMD ["python", "./__main__.py"]
