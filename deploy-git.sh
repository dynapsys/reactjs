#!/bin/bash

# test-server.sh
echo "Testowanie serwera deploymentu na localhost:8000..."

# Test 1: Proste zapytanie CURL
echo -e "\nTest 1: Podstawowy test połączenia"
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"test": "connection"}' \
  -v \
  --max-time 5 \
  2>&1

# Test 2: Pełne żądanie deploymentu
echo -e "\nTest 2: Test pełnego żądania deploymentu"
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "test.local",
    "cf_token": "test-token",
    "source": "test-source"
  }' \
  -v \
  --max-time 5 \
  2>&1

# Test 3: Test portu netstat
echo -e "\nTest 3: Sprawdzanie czy port 8000 jest otwarty"
netstat -tuln | grep ":8000"

# Test 4: Test procesu Python
echo -e "\nTest 4: Sprawdzanie procesu Python na porcie 8000"
ps aux | grep "python.*8000" | grep -v grep

# Sprawdzenie statusu usługi
echo -e "\nTest 5: Status usługi reactjs"
systemctl status reactjs 2>&1

# Sprawdzenie logów
echo -e "\nTest 6: Ostatnie logi"
tail -n 20 /opt/reactjs/logs/deployment.log 2>/dev/null || echo "Brak pliku logów"

# Sprawdzenie firewalla
echo -e "\nTest 7: Reguły firewalla dla portu 8000"
sudo ufw status | grep 8000 || echo "Port 8000 nie znaleziony w regułach firewalla"