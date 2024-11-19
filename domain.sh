#!/bin/bash

# Aktualizacja konfiguracji Caddy dla reactjs.dynapsys.com
cat > /etc/caddy/Caddyfile << 'EOF'
reactjs.dynapsys.com {
    reverse_proxy localhost:8000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }

    encode gzip

    header {
        Access-Control-Allow-Origin *
        Access-Control-Allow-Methods "GET, POST, OPTIONS"
        Access-Control-Allow-Headers "Content-Type"
        Strict-Transport-Security "max-age=31536000;"
        X-XSS-Protection "1; mode=block"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        # Bezpieczeństwo dla API deploymentu
        -Server
        -X-Powered-By
    }

    log {
        output file /opt/reactjs/logs/reactjs.dynapsys.com.log
        format json
    }
}
EOF

# Aktualizacja skryptu deploymentu
cat > /opt/reactjs/scripts/deploy.sh << 'EOF'
#!/bin/bash

# Sprawdzenie wymaganych argumentów
if [ "$#" -lt 3 ]; then
    echo "Użycie: $0 <domena> <cloudflare_token> <git_url/file_path>"
    exit 1
fi

DOMAIN=$1
CF_TOKEN=$2
SOURCE=$3
DEPLOY_DIR="/opt/reactjs/sites/${DOMAIN}"
LOG_FILE="/opt/reactjs/logs/${DOMAIN}.log"

# Funkcja logowania
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Utworzenie katalogu dla domeny
mkdir -p "$DEPLOY_DIR"

# Pobranie kodu źródłowego
if [[ $SOURCE == http* ]]; then
    log "Klonowanie repozytorium git..."
    git clone "$SOURCE" "$DEPLOY_DIR/temp"
    mv "$DEPLOY_DIR/temp"/* "$DEPLOY_DIR/"
    rm -rf "$DEPLOY_DIR/temp"
else
    log "Kopiowanie plików lokalnych..."
    cp -r "$SOURCE"/* "$DEPLOY_DIR/"
fi

# Instalacja zależności i build
cd "$DEPLOY_DIR"
log "Instalacja zależności npm..."
npm install

log "Budowanie aplikacji..."
npm run build

# Konfiguracja dla konkretnej domeny
log "Konfiguracja serwera dla ${DOMAIN}..."

# Aktualizacja DNS w Cloudflare
IP=$(curl -s http://ipv4.icanhazip.com)
ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=${DOMAIN}" \
    -H "Authorization: Bearer ${CF_TOKEN}" \
    -H "Content-Type: application/json" | jq -r '.result[0].id')

# Sprawdzenie czy rekord A już istnieje
RECORD_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records?type=A&name=${DOMAIN}" \
    -H "Authorization: Bearer ${CF_TOKEN}" \
    -H "Content-Type: application/json" | jq -r '.result[0].id')

if [ "$RECORD_ID" != "null" ]; then
    # Aktualizacja istniejącego rekordu
    curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records/${RECORD_ID}" \
        -H "Authorization: Bearer ${CF_TOKEN}" \
        -H "Content-Type: application/json" \
        --data "{
            \"type\": \"A\",
            \"name\": \"${DOMAIN}\",
            \"content\": \"${IP}\",
            \"ttl\": 1,
            \"proxied\": true
        }"
else
    # Utworzenie nowego rekordu
    curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
        -H "Authorization: Bearer ${CF_TOKEN}" \
        -H "Content-Type: application/json" \
        --data "{
            \"type\": \"A\",
            \"name\": \"${DOMAIN}\",
            \"content\": \"${IP}\",
            \"ttl\": 1,
            \"proxied\": true
        }"
fi

# Ustawienie portu dla React aplikacji
cat > "$DEPLOY_DIR/.env" << ENVEOF
PORT=8000
ENVEOF

# Restart serwera Node
pm2 delete ${DOMAIN} 2>/dev/null || true
cd "$DEPLOY_DIR"
pm2 start npm --name "${DOMAIN}" -- start

log "Deployment zakończony pomyślnie!"
EOF

# Instalacja PM2 do zarządzania procesami Node.js
npm install -g pm2

# Uprawnienia dla skryptu
chmod +x /opt/reactjs/scripts/deploy.sh

# Restart Caddy
systemctl reload caddy

echo "Konfiguracja zakończona. Możesz teraz deployować na reactjs.dynapsys.com:8000"
