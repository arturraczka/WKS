#!/bin/bash

#TODO check if data in database first if not restoer or if force

if [ -z "$1" ]; then
    echo "Error: Please provide pg_dump file path"
    exit 1
else
    echo "pg_dump provided path: $1"
    docker exec -i koop_form-backend-1 psql -U postgres -d koop_db < $1
fi