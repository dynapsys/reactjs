#!/bin/bash

# deploy-zip.sh
if [ "$#" -lt 3 ]; then
    echo "Użycie: $0 <ścieżka-do-projektu> <domena> <cloudflare-token>"
    exit 1
fi

source .
#PROJECT_PATH=$1
#DOMAIN=$2
#CF_TOKEN=$3
#DEPLOY_URL="https://reactjs.dynapsys.com:8000"

# Sprawdzenie czy katalog istnieje
if [ ! -d "$PROJECT_PATH" ]; then
    echo "Błąd: Katalog $PROJECT_PATH nie istnieje!"
    exit 1
fi

echo "Pakowanie projektu..."
FILE_CONTENT=$(tar czf - -C $(dirname "$PROJECT_PATH") $(basename "$PROJECT_PATH") | base64 -w 0)

echo "Wysyłanie do serwera deploymentu..."
curl -X POST "$DEPLOY_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"domain\": \"$DOMAIN\",
    \"cf_token\": \"$CF_TOKEN\",
    \"source\": \"data:application/tar+gz;base64,$FILE_CONTENT\"
  }"

echo -e "\nDeployment rozpoczęty!"