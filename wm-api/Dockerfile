FROM node:18.9-alpine

WORKDIR /opt/wm-api

LABEL updated_at="202209211000"

RUN apk add git

COPY wm-website/public/wm-scripts/hexmap.mjs /opt/hexmap/hexmap.mjs
COPY wm-api/package.json ./
COPY wm-api/src ./

RUN npm install --arch=x64 --platform=linux --libc=musl

ENV HEXMAP_CONFIG=/opt/hexmap/hexMap-config.mjs

CMD ["node", "./main.mjs"]