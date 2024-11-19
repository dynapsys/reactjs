# FIX

Aby sprawdzić i naprawić serwer:

1. Najpierw uruchom test:
```bash
chmod +x test-server.sh
./test-server.sh
```

2. Jeśli test wykaże problemy, uruchom skrypt naprawczy:
```bash
chmod +x fix.sh
sudo ./fix.sh
```

3. Możesz też ręcznie sprawdzić najważniejsze elementy:

```bash
# Sprawdź czy proces Python działa
ps aux | grep "python.*8000"

# Sprawdź port
netstat -tuln | grep ":8000"

# Test prostego żądania
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"test":"connection"}'

# Sprawdź logi
tail -f /opt/reactjs/logs/deployment.log
```

Najczęstsze problemy i rozwiązania:

1. Port 8000 zajęty:
```bash
sudo fuser -k 8000/tcp
sudo systemctl restart reactjs
```

2. Problem z uprawnieniami:
```bash
sudo chown -R root:root /opt/reactjs
sudo chmod -R 755 /opt/reactjs
```

3. Firewall blokuje port:
```bash
sudo ufw allow 8000/tcp
```

4. Usługa nie działa:
```bash
sudo systemctl restart reactjs
sudo systemctl status reactjs
```

Czy któryś z testów wykazał problemy? Mogę pomóc ze szczegółowym rozwiązaniem konkretnego problemu.