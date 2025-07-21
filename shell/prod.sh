docker compose --profile production down
docker compose --profile development down
sleep 5
docker compose --profile production up -d
