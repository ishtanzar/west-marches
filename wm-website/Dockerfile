FROM composer:2.4 as composer

WORKDIR /opt/sources

COPY ./composer.json ./
COPY ./composer.lock ./

RUN composer install

FROM php:8.1-fpm

WORKDIR /opt/sources

RUN apt-get update &&  \
    apt-get install -y --no-install-recommends liblmdb-dev rsync && \
    docker-php-ext-configure dba  --with-lmdb && \
    docker-php-ext-install -j$(nproc) dba

COPY --from=composer /opt/sources/vendor ./vendor
COPY ./public ./public
COPY ./views ./views
COPY ./fpm-entrypoint.sh /fpm-entrypoint.sh

RUN chmod +x /fpm-entrypoint.sh

ENTRYPOINT /fpm-entrypoint.sh