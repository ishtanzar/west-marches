FROM composer:2.4 as composer

WORKDIR /opt/sources

COPY ./composer.json ./
COPY ./composer.lock ./

RUN composer install

FROM php:8.1-fpm-alpine

WORKDIR /opt/sources

COPY --from=composer /opt/sources/vendor ./vendor
COPY ./public ./public
