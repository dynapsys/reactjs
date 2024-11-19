#!/bin/bash

echo "Naprawa serwera deploymentu..."

# 1. Zatrzymanie istniejących procesów na porcie 8000
echo "Zatrzymywanie procesów na porcie 8000..."
sudo fuser -k 8000/tcp 2>/dev/null

# 2. Restart usługi
echo "Restart usługi reactjs..."
sudo systemctl restart reactjs

# 3. Sprawdzenie i otwarcie portu w firewallu
echo "Konfiguracja firewalla..."
sudo ufw allow 8000/tcp

# 4. Sprawdzenie uprawnień
echo "Sprawdzanie uprawnień..."
sudo chown -R root:root /opt/reactjs
sudo chmod -R 755 /opt/reactjs
sudo chmod +x /opt/reactjs/scripts/*.sh
sudo chmod +x /opt/reactjs/deployment_server.py

# 5. Utworzenie katalogu logów jeśli nie istnieje
echo "Sprawdzanie katalogów..."
sudo mkdir -p /opt/reactjs/logs
sudo chmod 755 /opt/reactjs/logs

# 6. Restart Pythona jeśli potrzebny
echo "Restart serwera Python..."
pkill -f "python.*8000"
cd /opt/reactjs
nohup python3 deployment_server.py > /opt/reactjs/logs/deployment.log 2>&1 &

# 7. Sprawdzenie czy serwer działa
echo "Sprawdzanie czy serwer nasłuchuje..."
sleep 2
if netstat -tuln | grep ":8000" > /dev/null; then
    echo "Serwer działa poprawnie na porcie 8000"
else
    echo "BŁĄD: Serwer nie nasłuchuje na porcie 8000"
fi

# 8. Test połączenia
echo -e "\nTestowanie połączenia..."
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"test":"connection"}' \
  --max-time 5