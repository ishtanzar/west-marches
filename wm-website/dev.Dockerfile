FROM php:8.1-fpm

RUN apt-get update &&  \
    apt-get install -y --no-install-recommends liblmdb-dev

RUN docker-php-ext-configure dba  --with-lmdb && \
    docker-php-ext-install -j$(nproc) dba

RUN pecl install xdebug

RUN docker-php-ext-enable xdebug