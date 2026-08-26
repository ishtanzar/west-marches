FROM python:3.12-slim AS content-builder

RUN apt-get update && apt-get install -y --no-install-recommends unzip ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pyyaml requests

WORKDIR /opt/foundry-build

COPY docker/foundry/modules.yml /opt/foundry-build/modules.yml
COPY docker/foundry/install_foundry_content.py /opt/foundry-build/install_foundry_content.py

RUN python /opt/foundry-build/install_foundry_content.py \
  --output /opt/foundry-content

FROM felddy/foundryvtt:13.351

USER root

COPY --from=content-builder /opt/foundry-content /opt/foundry-content

RUN chown -R 421:421 /opt/foundry-content

USER foundry
