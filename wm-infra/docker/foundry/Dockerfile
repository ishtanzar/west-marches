FROM felddy/foundryvtt:9.269

COPY package.json package-custom.json

RUN jq -r '.dependencies | to_entries[] | .key + "@" + .value' package-custom.json | xargs npm install

RUN npm install -g pm2

RUN apk add python3 unzip
