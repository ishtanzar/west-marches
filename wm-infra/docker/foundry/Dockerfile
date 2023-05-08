FROM felddy/foundryvtt:10.291

RUN npm install \
    prom-client@^13.1.0 \
    override-require@^1.1.1 \
    express-handlebars@^6.0.6 \
    jsonwebtoken@^8.5.1 \
    cookie@^0.5.0 \
    morgan@^1.10.0

RUN npm install -g pm2

RUN apk add python3 unzip
