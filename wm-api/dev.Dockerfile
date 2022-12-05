FROM node:18.9-alpine

WORKDIR /opt/wm-websocket-server

LABEL updated_at="202209211000"

ENV HEXMAP_CONFIG=/opt/hexmap/hexMap-config.mjs

RUN npm install pm2 -g
