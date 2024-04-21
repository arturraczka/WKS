#!/bin/bash

DOCKER_COMPOSE_COMMAND=${DOCKER_COMPOSE_COMMAND:="docker compose"}
COMPOSE_FILE_PATH=$1
if [[ -z "${COMPOSE_FILE_PATH}" ]]; then
  echo "You have to provide COMPOSE_FILE_PATH as first parameter of script"
  exit
fi
ENV_FILE_PATH=$(dirname "$(readlink -f "${COMPOSE_FILE_PATH}")")/../parameters/compose-envs

${DOCKER_COMPOSE_COMMAND} version
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "The previous command failed (exit code: $RESULT)."
  echo "there is no command: $DOCKER_COMPOSE_COMMAND"
  exit
fi



if [[ -z "$(${DOCKER_COMPOSE_COMMAND} -f ${COMPOSE_FILE_PATH} ps -q)" ]]; then
  echo "no docker compose running"
  echo "START docker compose running"
  ${DOCKER_COMPOSE_COMMAND} -f ${COMPOSE_FILE_PATH} --env-file ${ENV_FILE_PATH} up -d
else
  echo "docker compose running is already running"
  echo "RESTART docker compose running"
  ${DOCKER_COMPOSE_COMMAND} -f ${COMPOSE_FILE_PATH} --env-file ${ENV_FILE_PATH} up -d #up when compose.yaml change
  sleep 2 #arbitral sleep helps before restart
  ${DOCKER_COMPOSE_COMMAND} -f ${COMPOSE_FILE_PATH} --env-file ${ENV_FILE_PATH} restart #when compose.yaml does not change but other things must be reinit
fi

