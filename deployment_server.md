1. Zapisz i uruchom skrypty:
```bash
# Deployment server
sudo mv deployment_server.py /opt/reactjs/
sudo chmod +x /opt/reactjs/deployment_server.py

# Service manager
chmod +x deployment-service-manager.sh
sudo ./deployment-service-manager.sh
```

2. Testowanie:
```bash
# Test podstawowy
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"test": "connection"}'

# Test deploymentu
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "react-test.dynapsys.com",
    "cf_token": "test-token",
    "source": "https://github.com/username/repo.git"
  }'
```

Główne zmiany:

1. Serwer deploymentu:
    - Poprawiona obsługa błędów
    - Szczegółowe logowanie
    - Prawidłowe zamykanie połączeń
    - Walidacja Content-Type
    - Obsługa pustych żądań

2. Service manager:
    - Właściwe uprawnienia
    - Automatyczny restart
    - Logowanie do pliku
    - Monitoring w czasie rzeczywistym

3. Diagnostyka:
    - Szczegółowe logi
    - Monitorowanie statusu
    - Testy połączenia

Czy chcesz, żebym dodał jakieś dodatkowe funkcje lub zabezpieczenia?