#!/bin/bash

# Kolory dla lepszej czytelności
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Naprawa uprawnień i portów dla Caddy...${NC}"

# 1. Zatrzymanie wszystkich usług używających portu 443
echo "1. Szukanie i zatrzymywanie procesów na porcie 443..."
sudo lsof -i :443
sudo fuser -k 443/tcp
sleep 2

# 2. Naprawa uprawnień dla katalogów Caddy
echo "2. Naprawa uprawnień..."
sudo mkdir -p /var/log/caddy
sudo mkdir -p /var/lib/caddy/.local/share/caddy
sudo mkdir -p /var/lib/caddy/.config/caddy

sudo chown -R caddy:caddy /var/log/caddy
sudo chown -R caddy:caddy /var/lib/caddy
sudo chown -R caddy:caddy /etc/caddy

sudo chmod 755 /var/log/caddy
sudo chmod 755 /var/lib/caddy
sudo chmod 755 /etc/caddy
sudo chmod 644 /etc/caddy/Caddyfile

# 3. Formatowanie Caddyfile
echo "3. Formatowanie Caddyfile..."
sudo caddy fmt --overwrite /etc/caddy/Caddyfile

# 4. Aktualizacja konfiguracji Caddy
echo "4. Aktualizacja konfiguracji..."
cat > /etc/caddy/Caddyfile << 'EOF'
{
    admin off
    log {
        output file /var/log/caddy/access.log
        format json
    }
    servers {
        protocols h1 h2 h2c
    }
}

reactjs.dynapsys.com {
    reverse_proxy localhost:8000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }

    log {
        output file /var/log/caddy/reactjs.dynapsys.com.log {
            roll_size 10mb
            roll_keep 5
        }
        format json
    }

    encode gzip
    tls {
        protocols tls1.2 tls1.3
    }
}
EOF

# 5. Sprawdzenie konfiguracji systemd
echo "5. Aktualizacja konfiguracji systemd..."
cat > /etc/systemd/system/caddy.service << 'EOF'
[Unit]
Description=Caddy
Documentation=https://caddyserver.com/docs/
After=network.target network-online.target
Requires=network-online.target

[Service]
Type=notify
User=caddy
Group=caddy
ExecStart=/usr/bin/caddy run --environ --config /etc/caddy/Caddyfile
ExecReload=/usr/bin/caddy reload --config /etc/caddy/Caddyfile
TimeoutStopSec=5s
LimitNOFILE=1048576
LimitNPROC=512
PrivateTmp=true
ProtectSystem=full
AmbientCapabilities=CAP_NET_BIND_SERVICE
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ReadWritePaths=/var/log/caddy /var/lib/caddy /etc/caddy
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
RestrictNamespaces=true
RestrictRealtime=true
RestrictSUIDSGID=true
ProtectClock=true
ProtectHostname=true
ProtectKernelLogs=true
ProtectKernelModules=true
ProtectKernelTunables=true
ProtectControlGroups=true
PrivateDevices=true
LockPersonality=true
MemoryDenyWriteExecute=true

[Install]
WantedBy=multi-user.target
EOF

# 6. Resetowanie i restart usług
echo "6. Resetowanie i restart usług..."
sudo systemctl daemon-reload
sudo systemctl stop caddy
sudo systemctl stop apache2 2>/dev/null
sudo systemctl stop nginx 2>/dev/null

# 7. Sprawdzenie czy porty są wolne
echo "7. Sprawdzanie portów..."
if sudo lsof -i :443 >/dev/null; then
    echo -e "${RED}Port 443 wciąż jest zajęty! Próba wymuszenia zamknięcia...${NC}"
    sudo fuser -k 443/tcp
    sleep 2
fi

# 8. Start Caddy z debugowaniem
echo "8. Uruchamianie Caddy..."
sudo systemctl start caddy
sleep 2

# 9. Sprawdzenie statusu
echo "9. Sprawdzanie statusu..."
sudo systemctl status caddy --no-pager
echo -e "\nSprawdzanie portów:"
sudo netstat -tuln | grep -E ':80|:443'
echo -e "\nSprawdzanie logów:"
sudo tail -n 5 /var/log/caddy/access.log 2>/dev/null

# 10. Test połączenia
echo -e "\n10. Test połączenia..."
curl -v https://reactjs.dynapsys.com 2>&1

echo -e "\n${GREEN}Zakończono naprawę. Sprawdź logi powyżej.${NC}"