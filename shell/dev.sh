docker compose --env-file backend/.env --profile production down
sleep 5
docker compose --env-file backend/.env --profile development up -d
