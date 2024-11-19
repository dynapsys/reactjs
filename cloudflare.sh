#!/bin/bash

# Kolory
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Sprawdź argumenty
if [ "$#" -lt 2 ]; then
    echo "Użycie: $0 <domena> <cloudflare_token>"
    echo "Przykład: $0 dynapsys.com your-cf-token"
    exit 1
fi

DOMAIN=$1
CF_TOKEN=$2

echo -e "${YELLOW}Sprawdzanie konfiguracji Cloudflare dla domeny ${DOMAIN}...${NC}"

# 1. Sprawdź Zone ID
echo -e "\n${YELLOW}1. Sprawdzanie Zone ID:${NC}"
ZONE_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=${DOMAIN}" \
    -H "Authorization: Bearer ${CF_TOKEN}" \
    -H "Content-Type: application/json")

echo "Odpowiedź Cloudflare:"
echo $ZONE_RESPONSE | python3 -m json.tool

if echo $ZONE_RESPONSE | grep -q '"success":true'; then
    if echo $ZONE_RESPONSE | grep -q '"result":\[\]'; then
        echo -e "${RED}Domena nie jest skonfigurowana w Cloudflare!${NC}"
        echo "Musisz dodać domenę do swojego konta Cloudflare."
    else
        ZONE_ID=$(echo $ZONE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['result'][0]['id'])")
        echo -e "${GREEN}Zone ID znalezione: ${ZONE_ID}${NC}"

        # 2. Sprawdź rekordy DNS
        echo -e "\n${YELLOW}2. Sprawdzanie rekordów DNS:${NC}"
        DNS_RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
            -H "Authorization: Bearer ${CF_TOKEN}" \
            -H "Content-Type: application/json")

        echo "Aktualne rekordy DNS:"
        echo $DNS_RESPONSE | python3 -m json.tool
    fi
else
    echo -e "${RED}Błąd autoryzacji lub API!${NC}"
    echo "Sprawdź czy token jest prawidłowy i ma odpowiednie uprawnienia."
fi

# 3. Sprawdź status proxy
echo -e "\n${YELLOW}3. Sprawdzanie statusu proxy:${NC}"
curl -s -I "https://${DOMAIN}" | head -n 1
if curl -s -I "https://${DOMAIN}" | grep -q "Server: cloudflare"; then
    echo -e "${GREEN}Domena jest poprawnie obsługiwana przez Cloudflare proxy${NC}"
else
    echo -e "${RED}Domena nie jest obsługiwana przez Cloudflare proxy${NC}"
fi

# 4. Podsumowanie i sugestie
echo -e "\n${YELLOW}4. Podsumowanie:${NC}"
if [ ! -z "$ZONE_ID" ]; then
    echo -e "- ${GREEN}Domena jest w Cloudflare${NC}"
    echo "- Zone ID: $ZONE_ID"
else
    echo -e "- ${RED}Domena nie jest w Cloudflare${NC}"
    echo "Aby naprawić:"
    echo "1. Dodaj domenę do Cloudflare"
    echo "2. Zaktualizuj NS rekordy u rejestratora domeny"
    echo "3. Poczekaj na propagację DNS (może zająć do 24h)"
fi