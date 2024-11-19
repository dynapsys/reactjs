#!/bin/bash

# Struktura katalogów
mkdir -p /opt/reactjs/{scripts,sites,logs}
cd /opt/reactjs

# Główny skrypt deploymentu (deploy.sh)
cat > scripts/deploy.sh << 'EOF'
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

# Konfiguracja Caddy
cat > /etc/caddy/Caddyfile << CADDYEOF
${DOMAIN} {
    root * ${DEPLOY_DIR}/build
    file_server
    encode gzip
    try_files {path} /index.html

    header {
        Access-Control-Allow-Origin *
        Strict-Transport-Security "max-age=31536000;"
        X-XSS-Protection "1; mode=block"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
    }

    log {
        output file ${LOG_FILE}
        format json
    }
}
CADDYEOF

# Aktualizacja DNS w Cloudflare
IP=$(curl -s http://ipv4.icanhazip.com)
ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=${DOMAIN}" \
    -H "Authorization: Bearer ${CF_TOKEN}" \
    -H "Content-Type: application/json" | jq -r '.result[0].id')

curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
    -H "Authorization: Bearer ${CF_TOKEN}" \
    -H "Content-Type: application/json" \
    --data "{
        \"type\": \"A\",
        \"name\": \"${DOMAIN}\",
        \"content\": \"${IP}\",
        \"ttl": 1,
        \"proxied\": true
    }"

# Restart Caddy
systemctl reload caddy

log "Deployment zakończony pomyślnie!"
EOF

# Nadanie uprawnień wykonywania
chmod +x scripts/deploy.sh

# Skrypt instalacyjny zależności (install_dependencies.sh)
cat > scripts/install_dependencies.sh << 'EOF'
#!/bin/bash

# Instalacja Caddy
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update
apt install -y caddy

# Instalacja pozostałych zależności
apt install -y nodejs npm jq curl git

# Konfiguracja firewalla
ufw allow 80,443/tcp

# Utworzenie usługi systemd
cat > /etc/systemd/system/reactjs.service << 'SERVICEEOF'
[Unit]
Description=React Deployment Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/reactjs
ExecStart=/usr/bin/python3 /opt/reactjs/deployment_server.py
Restart=always

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Serwer deploymentu (deployment_server.py)
cat > /opt/reactjs/deployment_server.py << 'PYTHONEOF'
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import os
from urllib.parse import parse_qs

class DeploymentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = json.loads(post_data)

        required_fields = ['domain', 'cf_token', 'source']
        if not all(field in params for field in required_fields):
            self.send_error(400, "Missing required fields")
            return

        try:
            subprocess.run([
                '/opt/reactjs/scripts/deploy.sh',
                params['domain'],
                params['cf_token'],
                params['source']
            ], check=True)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())
        except subprocess.CalledProcessError as e:
            self.send_error(500, f"Deployment failed: {str(e)}")

httpd = HTTPServer(('0.0.0.0', 8000), DeploymentHandler)
print("Deployment server running on port 8000...")
httpd.serve_forever()
PYTHONEOF

# Aktywacja i start usługi
systemctl enable reactjs
systemctl start reactjs

echo "Instalacja zakończona pomyślnie!"
EOF

chmod +x scripts/install_dependencies.sh
EOF