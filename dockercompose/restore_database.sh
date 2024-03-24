#!/bin/bash

#TODO check if data in database first if not restoer or if force
#!/bin/bash
FORCE=0
case "$1" in
    -f|--force)
        # Force flag is set, proceed without checking database emptiness
        echo "Force restore enabled"
        FORCE=1
        shift  # Remove the force flag from arguments
        ;;
    -h|--help)
        # Add help message here if needed
        echo "Usage: $0 [-f|--force] <pg_dump_file_path>"
        exit 0
        ;;
    *)
        # Check if first argument is the pg_dump file path
        ;;
esac

# Check if database is empty (optional for force flag)
if [[ "${FORCE}" -eq 0 ]]; then
    DB_EMPTY=$(docker exec -i koop_form-database-1 psql -U postgres -d koop_db -t -c "\dt" | wc -l)
    echo ${DB_EMPTY}
    if [[ "${DB_EMPTY}" -gt 0 ]]; then
        echo "Database is not empty. Use -f flag to force restore."
        exit 1
    fi
else
  echo "clear db"
  #have to add simple FOR in postgress to execut drop table 
  DROP_TABLES=$(cat <<EOF
DO \$\$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = (SELECT CURRENT_SCHEMA))
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END \$\$;
EOF
)
  echo ${DROP_TABLES}
  docker exec -i koop_form-database-1 psql -U postgres -d koop_db -t -c "${DROP_TABLES}"
fi


if [ -z "$1" ]; then
    echo "Error: Please provide pg_dump file path"
    exit 1
else
    echo "pg_dump provided path: $1"
    docker exec -i koop_form-database-1 psql -U postgres -d koop_db < $1
fi