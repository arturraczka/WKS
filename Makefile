DOCKERFILE = Dockerfile
IMAGE_NAME=koop_form
APP_VERSION=1.0.1a3
IMAGE_ENVS_FILE=env
ENVS_FILE=./.myenv
IMAGE_ALLOW_HOSTS_FILE=local_hosts
ALLOW_HOSTS_FILE=./local_hosts
#include .privatemakefileenvs

# Build the Docker image
build-image:
	docker build -t $(IMAGE_NAME):$(APP_VERSION) .

push-image:
	docker tag  $(IMAGE_NAME):$(APP_VERSION) $(ECR_IMAGE_NAME):$(APP_VERSION)
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker push $(ECR_IMAGE_NAME):$(APP_VERSION)

# Run the container with mounted files (unsafe)
run-only-docker:
	docker run -it --rm \
    -v "$(ENVS_FILE)":/$(IMAGE_ENVS_FILE) \
    -v "$(ALLOW_HOSTS_FILE)":/$(IMAGE_ALLOW_HOSTS_FILE) \
    -e ENV_CONFIG_PATH=/$(IMAGE_ENVS_FILE) \
    -e ALLOWED_HOSTS_CONFIG_PATH=/$(IMAGE_ALLOW_HOSTS_FILE) \
    -e DJANGO_SETTINGS_MODULE=config.settings.dev \
    --network host \
    "$(IMAGE_NAME):$(APP_VERSION)"

#remove later, find container with  docker ps -a
run-only-database:
	docker-compose -f dockercompose_template/main/compose.yaml run -p 5432:5432 database

#could be docker-compose instead of docker compose

compose-run-start-logs:
	docker compose -f dockercompose_template/main/compose.yaml --env-file dockercompose_template/parameters/compose-envs up

compose-run-start:
	DOCKER_COMPOSE_COMMAND="docker-compose" dockercompose_template/main/scripts/compose-run.sh dockercompose_template/main/compose.yaml


compose-run-stop:
	docker-compose -f ./dockercompose_template/main/compose.yaml down

compose-run-migrate:
	sleep 10
	docker exec -i koop_form-webapp-1 python koop_form/manage.py migrate

compose-run-create-superusper:
	docker exec -it koop_form-webapp-1 python koop_form/manage.py createsuperuser

compose-run-restore-database:
	./dockercompose_template/main/scripts/restore_database.sh -f ./koop_form/db_dump_test

remove-compose-db-volume:
	docker volume rm koop_form_db-data

start-all-compose: build-image compose-run-start compose-run-migrate compose-run-create-superusper
