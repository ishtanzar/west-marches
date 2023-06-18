FROM felddy/foundryvtt:9.269

RUN npm install \
    prom-client@^13.1.0 \
    override-require@^1.1.1 \
    express-handlebars@^6.0.1 \
    jsonwebtoken@^8.5.1 \
    cookie@^0.4.1 \
    morgan@^1.10.0 \
    jasmine@^5.0.2 \
    winston-elasticsearch@^0.17.2

RUN npm install -g pm2

RUN apk add python3 unzip
