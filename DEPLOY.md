Pokażę jak zrobić deployment używając lokalnego pliku z kodem React.

1. Najpierw możemy zakodować zawartość pliku w base64, aby bezpiecznie przesłać przez API. Oto pełny skrypt:

```bash
# Test połączenia
curl -X POST https://reactjs.dynapsys.com \
  -H "Content-Type: application/json" \
  -d '{"test": "connection"}' \
  -v
```
```bash
# Zakodowanie pliku w base64
FILE_CONTENT=$(tar czf - twoj-katalog-react | base64 -w 0)

# Wysłanie żądania z zawartością pliku
curl -X POST https://reactjs.dynapsys.com \
  -H "Content-Type: application/json" \
  -d "{
    \"domain\": \"reactjs.dynapsys.com\",
    \"cf_token\": \"twoj-cloudflare-token\",
    \"source\": \"data:application/tar+gz;base64,${FILE_CONTENT}\"
  }"
```



Teraz możesz użyć tego na trzy sposoby:

1. Używając skryptu pomocniczego:
```bash
chmod +x deploy-zip.sh
./deploy-zip.sh ./twoj-projekt-react reactjs.dynapsys.com twoj-cloudflare-token
./deploy-zip.sh ./twoj-projekt-react reactjs.dynapsys.com twoj-cloudflare-token
```

2. Bezpośrednio przez curl (dla pojedynczego pliku):
```bash
FILE_CONTENT=$(tar czf - ./twoj-projekt-react | base64 -w 0)
curl -X POST https://reactjs.dynapsys.com \
  -H "Content-Type: application/json" \
  -d "{
    \"domain\": \"reactjs.dynapsys.com\",
    \"cf_token\": \"twoj-cloudflare-token\",
    \"source\": \"data:application/tar+gz;base64,${FILE_CONTENT}\"
  }"
```

3. Dla konkretnego pliku lub katalogu:
```bash
# Dla pojedynczego pliku
base64 plik.js | curl -X POST https://reactjs.dynapsys.com:8000 \
  -H "Content-Type: application/json" \
  -d "{
    \"domain\": \"reactjs.dynapsys.com\",
    \"cf_token\": \"twoj-cloudflare-token\",
    \"source\": \"data:application/javascript;base64,$(cat -)\"
  }"
```

Skrypt obsługuje:
- Pakowanie całego projektu React
- Kodowanie w base64
- Bezpieczne przesyłanie na serwer
- Automatyczne rozpakowanie i deployment
- Obsługę błędów
- Logowanie procesu

Czy potrzebujesz dodatkowych wyjaśnień dotyczących któregoś z elementów?