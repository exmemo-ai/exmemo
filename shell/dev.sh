docker-compose --env-file backend/.env --profile production stop
docker-compose --env-file backend/.env --profile development up -d
