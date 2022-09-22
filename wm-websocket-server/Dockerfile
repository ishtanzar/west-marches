FROM node:18.9-alpine

WORKDIR /opt/wm-websocket-server

LABEL updated_at="202209211000"

COPY package.json ./
COPY src ./

RUN npm install

CMD ["node", "./main.js"]