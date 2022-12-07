FROM python:3.10-slim

WORKDIR /opt/wm-discord-workaround

LABEL updated_at="202210220900"

COPY ./wm-discord-workaround/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY ./wm-discord-workaround/src ./

CMD ["python", "__main__.py"]
