1. Zapisz jako `status.sh` i nadaj uprawnienia:
```bash
chmod +x status.sh
```

2. Przykłady użycia:

```bash
# Pokaż wszystkie logi
./status.sh -a

# Śledź logi deploymentu
./status.sh -d -f

# Pokaż ostatnie 100 linii logów PM2
./status.sh -p -n 100

# Śledź logi Caddy
./status.sh -c -f

# Pokaż logi usługi systemd
./status.sh -s
```

3. Szybki podgląd wszystkich logów:
```bash
./status.sh
```

Skrypt oferuje:

1. Różne źródła logów:
    - Logi deploymentu
    - Logi usługi systemd
    - Logi PM2
    - Logi Caddy

2. Opcje wyświetlania:
    - Śledzenie w czasie rzeczywistym (-f)
    - Wybór liczby linii (-n)
    - Kolorowe formatowanie
    - Timestampy

3. Status usług:
    - Status reactjs
    - Status Caddy
    - Lista procesów PM2

4. Dodatkowe funkcje:
    - Automatyczne sprawdzanie istnienia plików
    - Obsługa błędów
    - Pomoc i przykłady użycia

Chcesz, żebym dodał jakieś dodatkowe funkcje do skryptu logów?