#!/bin/bash
# fix-deployment.sh

echo "Naprawa problemów z deploymentem..."

# 1. Instalacja PM2
echo "1. Instalacja PM2..."
sudo npm install -g pm2

# 2. Zwolnienie portu 80 dla Caddy
echo "2. Sprawdzanie i zwalnianie portu 80..."
sudo lsof -i :80
sudo fuser -k 80/tcp
sleep 2

# 3. Naprawa usługi Caddy
echo "3. Naprawa usługi Caddy..."
sudo systemctl stop caddy
sudo systemctl disable caddy
sudo systemctl enable caddy
sudo systemctl start caddy

# 4. Uprawnienia dla katalogów
echo "4. Naprawa uprawnień..."
sudo chown -R root:root /opt/reactjs
sudo chmod -R 755 /opt/reactjs
sudo mkdir -p /opt/reactjs/logs
sudo chmod 755 /opt/reactjs/logs

# 5. Aktualizacja service file
echo "5. Aktualizacja pliku usługi..."
cat > /etc/systemd/system/reactjs.service << 'EOF'
[Unit]
Description=React Deployment Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/reactjs
ExecStart=/usr/bin/python3 /opt/reactjs/deployment_server.py
Restart=always
StandardOutput=append:/opt/reactjs/logs/deployment.log
StandardError=append:/opt/reactjs/logs/deployment.log

[Install]
WantedBy=multi-user.target
EOF

# 6. Aktualizacja deployment_server.py aby naprawić błąd JSON
echo "6. Aktualizacja serwera deploymentu..."
cat > /opt/reactjs/deployment_server.py << 'EOF'
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import os
import base64
import tempfile
import traceback

class DeploymentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')

            try:
                params = json.loads(post_data)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {str(e)}\nData: {post_data}")
                self.send_error(400, f"Invalid JSON: {str(e)}")
                return

            # Logowanie żądania
            with open('/opt/reactjs/logs/deployment.log', 'a') as log:
                log.write(f"\nNew deployment request: {json.dumps(params, indent=2)}\n")

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())

        except Exception as e:
            print(f"Error: {str(e)}\n{traceback.format_exc()}")
            self.send_error(500, f"Internal error: {str(e)}")

if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', 8000), DeploymentHandler)
    print("Deployment server running on port 8000...")
    server.serve_forever()
EOF

# 7. Restart usług
echo "7. Restart usług..."
sudo systemctl daemon-reload
sudo systemctl restart reactjs
sudo systemctl restart caddy

# 8. Sprawdzenie statusu
echo "8. Sprawdzanie statusu..."
sleep 2
echo "Status reactjs service:"
sudo systemctl status reactjs
echo "Status Caddy:"
sudo systemctl status caddy
echo "Porty nasłuchujące:"
netstat -tuln | grep -E ':80|:8000'

echo "Naprawa zakończona. Testowanie połączenia..."

# Test połączenia
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"test": "connection"}' \
  -v

