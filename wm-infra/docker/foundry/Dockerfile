FROM felddy/foundryvtt:13.351

COPY package.json package-custom.json

USER root

RUN chown -R 1000:1000 "/home/node/.npm"

#RUN jq -r '.dependencies | to_entries[] | .key + "@" + .value' package-custom.json | xargs npm install

RUN npm install -g pm2

RUN apt update && apt install -y python3 unzip

USER node
