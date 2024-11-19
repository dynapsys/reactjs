#!/bin/bash
# fix-deployment.sh

#!/bin/bash

echo "Weryfikacja środowiska..."

# 1. Sprawdzenie portów
echo "Używane porty:"
sudo lsof -i :80
sudo lsof -i :443
sudo lsof -i :8000

# 2. Sprawdzenie procesów
echo -e "\nProcesy:"
ps aux | grep -E 'caddy|python|node'

# 3. Sprawdzenie DNS
echo -e "\nKonfiguracja DNS:"
dig reactjs.dynapsys.com

# 4. Sprawdzenie certyfikatów SSL
echo -e "\nCertyfikaty SSL:"
sudo ls -la /var/lib/caddy/.local/share/caddy/certificates/

# 5. Test deployment service
echo -e "\nTest deployment service:"
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"test":"connection"}' \
  -v

# 6. Sprawdzenie logów systemowych
echo -e "\nLogi systemowe:"
sudo journalctl -u caddy --no-pager -n 10
sudo journalctl -u reactjs --no-pager -n 10


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
netstat -tuln | grep -E ':80|:443|:8000'

echo "Naprawa zakończona. Testowanie połączenia..."

# Test połączenia
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"test": "connection"}' \
  -v

