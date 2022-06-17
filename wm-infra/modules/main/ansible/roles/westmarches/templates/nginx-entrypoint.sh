#!/usr/bin/env bash

if [[ -f /etc/letsencrypt/live/{{ foundry_fqdn }}-0001/cert.pem ]]; then
  ln -nsf /etc/nginx/02-ssl.conf.new /etc/nginx/conf.d/custom.conf
else
  ln -nsf /etc/nginx/01-custom.conf.new /etc/nginx/conf.d/custom.conf
fi


