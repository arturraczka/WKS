#!/bin/bash
#copy or create certs in dir where this script exists

SCRIPT_PATH_DIR=$(dirname "$(readlink -f "${0}")")
CERTS_DIR_PATH=$1
NGINX_CERTS_DIR_PATH=${SCRIPT_PATH_DIR}/../../parameters

if [[ -z "${CERTS_DIR_PATH}" ]]; then
  echo "You have to provide CERTS_DIR_PATH as first parameter of script"
  exit
fi

if test -e ${CERTS_DIR_PATH}/website.crt && test -e ${CERTS_DIR_PATH}/website.key ; then #check if files exists if not create certs
  echo "copy cert files for nginx"
  cp  ${CERTS_DIR_PATH}/website.crt  ${NGINX_CERTS_DIR_PATH}/website.crt
  cp  ${CERTS_DIR_PATH}/website.key  ${NGINX_CERTS_DIR_PATH}/website.key
else
  echo "create dummy cert for nginx"
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 -subj "/C=PE/ST=Lima/L=Lima/O=Acme Inc. /OU=IT Department/CN=localhost" -keyout ${NGINX_CERTS_DIR_PATH}/website.key -out ${NGINX_CERTS_DIR_PATH}/website.crt
fi
