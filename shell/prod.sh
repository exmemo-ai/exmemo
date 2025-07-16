docker compose --env-file backend/.env --profile production down
docker compose --env-file backend/.env --profile development down
sleep 5
docker compose --env-file backend/.env --profile production up -d
