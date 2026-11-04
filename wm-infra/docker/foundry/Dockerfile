# syntax=docker/dockerfile:1

ARG FOUNDRY_VERSION=13.351

FROM python:3.12-slim AS foundry-fetcher

ARG FOUNDRY_VERSION
ARG FOUNDRY_S3_BUCKET=caveduroliste-westmarches

RUN pip install --no-cache-dir awscli

RUN --mount=type=secret,id=aws_access_key_id,env=AWS_ACCESS_KEY_ID,required=true \
    --mount=type=secret,id=aws_secret_access_key,env=AWS_SECRET_ACCESS_KEY,required=true \
    mkdir -p /opt/foundry-cache \
    && aws s3 cp \
      "s3://${FOUNDRY_S3_BUCKET}/private/foundryvtt/foundryvtt-${FOUNDRY_VERSION}.zip" \
      "/opt/foundry-cache/foundryvtt-${FOUNDRY_VERSION}.zip" \
      --region eu-west-3 \
      --only-show-errors

FROM python:3.12-slim AS content-builder

ARG APT_REFRESH=initial

RUN echo "APT refresh: ${APT_REFRESH}" \
  && apt-get update && apt-get install -y --no-install-recommends unzip ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pyyaml requests

WORKDIR /opt/foundry-build

COPY docker/foundry/modules.yml /opt/foundry-build/modules.yml
COPY docker/foundry/install_foundry_content.py /opt/foundry-build/install_foundry_content.py

RUN python /opt/foundry-build/install_foundry_content.py \
  --output /opt/foundry-content

FROM felddy/foundryvtt:${FOUNDRY_VERSION}

USER root

ENV CONTAINER_CACHE=/opt/foundry-cache

COPY --from=foundry-fetcher /opt/foundry-cache /opt/foundry-cache
COPY --from=content-builder /opt/foundry-content /opt/foundry-content

RUN chown -R 421:421 /opt/foundry-cache /opt/foundry-content

USER 421:421
