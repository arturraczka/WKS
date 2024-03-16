DOCKERFILE = Dockerfile
IMAGE_NAME=koop_form
APP_VERSION=0.1.0a1
IMAGE_ENVS_FILE=env
ENVS_FILE=./.myenv
IMAGE_ALLOW_HOSTS_FILE=local_hosts
ALLOW_HOSTS_FILE=./local_hosts
include .privatemakefileenvs

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

#could be docker-compose instead of docker compose
compose-run-start:
	docker compose -f ./dockercompose/compose.yaml up -d

compose-run-stop:
	docker compose -f ./dockercompose/compose.yaml down

compose-run-migrate:
	sleep 10
	docker exec -i koop_form-frontend-1 python koop_form/manage.py migrate

compose-run-create-superusper:
	docker exec -it koop_form-frontend-1 python koop_form/manage.py createsuperuser

compose-run-restore-database:
	./dockercompose/restore_database.sh ./koop_form/db_dump_test

remove-compose-db-volume:
	docker volume rm koop_form_db-data

start-all-compose: build-image compose-run-start compose-run-migrate compose-run-create-superusper
