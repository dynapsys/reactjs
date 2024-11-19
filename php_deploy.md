System do automatycznego deploymentu aplikacji PHP pod Caddy.

```bash
php_deploy.py php.dynapsys.com https://github.com/dynapsys/php.git
python3 php_deploy.py php.dynapsys.com https://github.com/dynapsys/php.git
```


```bash
# Sprawdź wersję PHP
php -v

# Sprawdź status PHP-FPM
systemctl status php8.3-fpm

# Sprawdź status Caddy
systemctl status caddy
```


Aby użyć systemu:

1. Zainstaluj:
```bash
chmod +x php-deploy-setup.sh
sudo ./php-deploy-setup.sh
```

2. Deployuj aplikację PHP:
```bash
# Używając skryptu pomocniczego
python3 php_deploy.py 

# Lub bezpośrednio przez curl
curl -X POST http://localhost:8001 \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "php-test.dynapsys.com",
    "git_url": "https://github.com/dynapsys/php.git"
  }'
```

System oferuje:

1. Automatyczną konfigurację:
   - Caddy z obsługą PHP
   - PHP-FPM z osobnymi poolami
   - HTTPS przez Caddy

2. Zabezpieczenia:
   - Izolacja aplikacji
   - Security headers
   - Blokowanie dostępu do wrażliwych plików

3. Deployment:
   - Klonowanie z Git
   - Instalacja Composer
   - Konfiguracja .env
   - Uprawnienia plików

4. Monitoring:
   - Logi dla każdej domeny
   - Logi PHP-FPM
   - Logi deploymentu

Chcesz, żebym dodał jakieś dodatkowe funkcje? Na przykład:
- Backup przed deploymentem
- Rollback w przypadku błędu
- Monitoring zasobów
- SSL certyfikaty