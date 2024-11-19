#!/bin/bash

# Kolory dla lepszej czytelności
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Sprawdzanie statusu aplikacji deployment ===\n${NC}"

# 1. Sprawdzenie struktury katalogów
echo -e "${YELLOW}1. Struktura katalogów:${NC}"
tree -L 2 /opt/reactjs 2>/dev/null || {
    echo -e "${RED}Komenda tree niedostępna. Używam ls:${NC}"
    ls -R /opt/reactjs
}

# 2. Sprawdzenie procesów
echo -e "\n${YELLOW}2. Uruchomione procesy:${NC}"
echo "Python deployment server:"
ps aux | grep "python.*reactjs" | grep -v grep
echo -e "\nProcesy Node/PM2:"
pm2 list

# 3. Status usług
echo -e "\n${YELLOW}3. Status usług:${NC}"
echo "Deployment service:"
systemctl status reactjs --no-pager
echo -e "\nCaddy status:"
systemctl status caddy --no-pager

# 4. Sprawdzenie portów
echo -e "\n${YELLOW}4. Otwarte porty:${NC}"
echo "Port 8000 (deployment server):"
netstat -tuln | grep ":8000"
echo -e "\nPort 80/443 (Caddy):"
netstat -tuln | grep -E ":80|:443"

# 5. Test curl dla różnych endpointów
echo -e "\n${YELLOW}5. Test curl:${NC}"

# Test deployment servera
echo -e "\n${YELLOW}Testing deployment server:${NC}"
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "reactjs.dynapsys.com",
    "cf_token": "test-token",
    "source": "test"
  }' \
  -v \
  2>&1

# 6. Sprawdzenie logów
echo -e "\n${YELLOW}6. Ostatnie logi:${NC}"
echo -e "\nDeployment logs:"
tail -n 10 /opt/reactjs/logs/deployment.log 2>/dev/null || echo "Brak logów deployment"
echo -e "\nCaddy logs:"
tail -n 10 /var/log/caddy/access.log 2>/dev/null || echo "Brak logów Caddy"

# 7. Sprawdzenie konfiguracji
echo -e "\n${YELLOW}7. Konfiguracja:${NC}"
echo -e "\nCaddy config:"
cat /etc/caddy/Caddyfile

# 8. Test DNS
echo -e "\n${YELLOW}8. Test DNS dla domeny:${NC}"
dig reactjs.dynapsys.com || nslookup reactjs.dynapsys.com

# 9. Sprawdzenie użycia zasobów
echo -e "\n${YELLOW}9. Użycie zasobów:${NC}"
echo "Użycie CPU i RAM dla procesów deployment:"
top -b -n 1 | head -n 12
echo -e "\nUżycie dysku:"
df -h /opt/reactjs

# 10. Test podstawowych zależności
echo -e "\n${YELLOW}10. Zainstalowane zależności:${NC}"
echo "Node.js: $(node -v)"
echo "NPM: $(npm -v)"
echo "PM2: $(pm2 -v)"
echo "Python: $(python3 --version)"
echo "Caddy: $(caddy version)"

# Funkcja do testowania curl z różnymi payload'ami
test_deployment() {
    echo -e "\n${YELLOW}Testing deployment with sample React app${NC}"

    # Przykładowy kod React
    SAMPLE_REACT='{
        "name": "test-app",
        "version": "1.0.0",
        "dependencies": {
            "react": "^17.0.2",
            "react-dom": "^17.0.2"
        },
        "scripts": {
            "start": "react-scripts start",
            "build": "react-scripts build"
        }
    }'

    # Zakodowanie w base64
    ENCODED_CONTENT=$(echo "$SAMPLE_REACT" | base64)

    # Test z przykładowym kodem
    curl -X POST http://localhost:8000 \
      -H "Content-Type: application/json" \
      -d "{
        \"domain\": \"reactjs.dynapsys.com\",
        \"cf_token\": \"test-token\",
        \"source\": \"data:application/tar+gz;base64,$ENCODED_CONTENT\"
      }" \
      -v
}

# Wykonanie testu deploymentu
test_deployment

echo -e "\n${GREEN}=== Zakończono sprawdzanie statusu ====${NC}"