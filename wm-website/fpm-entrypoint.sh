#!/usr/bin/env bash

rsync -av --delete /opt/sources/ /var/www/html/

exec "$@"