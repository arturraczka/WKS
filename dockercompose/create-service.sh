SERVICE_PATH=$1
APP_PATH=$2


cat >${SERVICE_PATH} <<EOL
[Unit]
Description=Docker Compose Application Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${APP_PATH}
User=root
Environment=DOCKER_COMPOSE_COMMAND="/usr/local/bin/docker-compose"
ExecStart=${APP_PATH}/compose-run.sh ${APP_PATH}/compose.yaml

[Install]
WantedBy=multi-user.target
EOL

