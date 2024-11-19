# reactjs
reactjs.dynapsys.com
Zaloguj sie na serwer
```bash
cd ~
git clone https://github.com/dynapsys/reactjs.git
cd reactjs
```

zainstaluj
skonfiguruj domene
```bash
chmod +x install.sh domain.sh
sudo ./install.sh
sudo ./domain.sh
```
Kompleksowe rozwiązanie do automatycznego deploymentu aplikacji React z konfiguracją Caddy i Cloudflare.

1. Najpierw należy zainstalować wszystkie zależności:
```bash
chmod +x /opt/reactjs/scripts/install_dependencies.sh
/opt/reactjs/scripts/install_dependencies.sh
```

```bash
npx create-react-app test-react
```        

2. Aby zdeployować aplikację, możesz użyć curl:
```bash
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "react-test.dynapsys.com",
    "cf_token": "twoj-cloudflare-token",
    "source": "https://github.com/dynapsys/react-test.git"
  }'
```

Rozwiązanie zawiera:

1. Serwer HTTP na porcie 8000 obsługujący żądania deploymentu
2. Automatyczną konfigurację Caddy jako serwera proxy
3. Integrację z Cloudflare API do zarządzania DNS
4. Automatyczny build aplikacji React
5. System logowania
6. Zabezpieczenia i optymalizacje serwera

Główne funkcje:
- Obsługa deploymentu z Git URL lub lokalnych plików
- Automatyczna konfiguracja HTTPS przez Caddy
- Automatyczna konfiguracja DNS w Cloudflare
- Kompresja Gzip
- Podstawowe nagłówki bezpieczeństwa
- Logi w formacie JSON


## deployment dla domeny reactjs.dynapsys.com na porcie 8000.

konfigurację dla domeny reactjs.dynapsys.com.

1. Dodanie dedykowanej konfiguracji Caddy dla reactjs.dynapsys.com
2. Skonfigurowanie reverse proxy dla portu 8000
3. Dodanie zarządzania procesami Node.js przez PM2
4. Obsługa CORS i nagłówków bezpieczeństwa
5. Automatyczna konfiguracja SSL przez Caddy
6. Logowanie w formacie JSON


```bash
curl -X POST http://reactjs.dynapsys.com:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "reactjs.dynapsys.com",
    "cf_token": "twoj-cloudflare-token",
    "source": "url-do-twojego-repo-git"
  }'
```

