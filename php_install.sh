#!/bin/bash

# Kolory
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Instalacja systemu deploymentu PHP...${NC}"

# 1. Dodanie repozytorium PHP
echo -e "\n${YELLOW}1. Konfiguracja repozytoriów PHP...${NC}"
apt-get update
apt-get install -y software-properties-common
add-apt-repository -y ppa:ondrej/php
apt-get update

# 2. Instalacja PHP 8.3 (najnowsza wersja dla Ubuntu 24.04)
echo -e "\n${YELLOW}2. Instalacja PHP i zależności...${NC}"
apt-get install -y \
    php8.3-fpm \
    php8.3-cli \
    php8.3-common \
    php8.3-mysql \
    php8.3-curl \
    php8.3-gd \
    php8.3-mbstring \
    php8.3-xml \
    php8.3-zip \
    php8.3-bcmath \
    php8.3-intl \
    curl \
    git \
    python3 \
    unzip

# 3. Instalacja Composer
echo -e "\n${YELLOW}3. Instalacja Composer...${NC}"
curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# 4. Tworzenie struktury katalogów
echo -e "\n${YELLOW}4. Tworzenie katalogów...${NC}"
mkdir -p /opt/php-deploy/{logs,scripts}
mkdir -p /var/www
chmod 755 /var/www

# 5. Konfiguracja PHP-FPM
echo -e "\n${YELLOW}5. Konfiguracja PHP-FPM...${NC}"
cat > /etc/php/8.3/fpm/php-fpm.conf << 'EOF'
[global]
pid = /run/php/php8.3-fpm.pid
error_log = /var/log/php8.3-fpm.log
include=/etc/php/8.3/fpm/pool.d/*.conf
EOF

# 6. Konfiguracja bazowego poola PHP-FPM
cat > /etc/php/8.3/fpm/pool.d/www.conf << 'EOF'
[www]
user = www-data
group = www-data
listen = /run/php/php8.3-fpm.sock
listen.owner = www-data
listen.group = www-data
pm = dynamic
pm.max_children = 5
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 3
EOF

# 7. Aktualizacja konfiguracji Caddy dla PHP 8.3
cat > /etc/caddy/Caddyfile << 'EOF'
{
    admin off
    log {
        output file /var/log/caddy/access.log
        format json
    }
}

# Przykładowa konfiguracja PHP
# example.com {
#     root * /var/www/example.com
#     php_fastcgi unix//run/php/php8.3-fpm.sock
#     file_server
# }
EOF

# 8. Tworzenie service dla deployment serwera
cat > /etc/systemd/system/php-deploy.service << 'EOF'
[Unit]
Description=PHP Deployment Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/php-deploy
ExecStart=/usr/bin/python3 /opt/php-deploy/php_deployment_server.py
Restart=always
StandardOutput=append:/opt/php-deploy/logs/deployment.log
StandardError=append:/opt/php-deploy/logs/deployment.log

[Install]
WantedBy=multi-user.target
EOF

# 9. Aktualizacja konfiguracji PHP
echo -e "\n${YELLOW}6. Konfiguracja PHP...${NC}"
cat > /etc/php/8.3/fpm/conf.d/custom.ini << 'EOF'
upload_max_filesize = 64M
post_max_size = 64M
memory_limit = 256M
max_execution_time = 180
max_input_vars = 3000
date.timezone = UTC
EOF

# 10. Uprawnienia i czyszczenie
echo -e "\n${YELLOW}7. Konfiguracja uprawnień...${NC}"
chown -R www-data:www-data /var/www
chmod -R 755 /var/www
mkdir -p /var/log/caddy
chown -R caddy:caddy /var/log/caddy

# 11. Restart usług
echo -e "\n${YELLOW}8. Restart usług...${NC}"
systemctl daemon-reload
systemctl enable php8.3-fpm
systemctl restart php8.3-fpm
systemctl restart caddy

# 12. Tworzenie skryptu pomocniczego
cat > /usr/local/bin/deploy-php << 'EOF'
#!/bin/bash
if [ "$#" -ne 2 ]; then
    echo "Użycie: $0 <domena> <git-url>"
    exit 1
fi

curl -X POST http://localhost:8001 \
    -H "Content-Type: application/json" \
    -d "{
        \"domain\": \"$1\",
        \"git_url\": \"$2\"
    }"
EOF

chmod +x /usr/local/bin/deploy-php

# 13. Sprawdzenie instalacji
echo -e "\n${YELLOW}9. Sprawdzanie instalacji...${NC}"
PHP_VER=$(php -v | head -n 1)
COMPOSER_VER=$(composer --version)
PHP_FPM_STATUS=$(systemctl is-active php8.3-fpm)
CADDY_STATUS=$(systemctl is-active caddy)

echo -e "\nZainstalowane komponenty:"
echo -e "PHP: ${GREEN}$PHP_VER${NC}"
echo -e "Composer: ${GREEN}$COMPOSER_VER${NC}"
echo -e "PHP-FPM Status: ${GREEN}$PHP_FPM_STATUS${NC}"
echo -e "Caddy Status: ${GREEN}$CADDY_STATUS${NC}"

# 14. Sprawdzenie soketu PHP-FPM
if [ -S /run/php/php8.3-fpm.sock ]; then
    echo -e "PHP-FPM socket: ${GREEN}OK${NC}"
else
    echo -e "PHP-FPM socket: ${RED}Missing${NC}"
fi

echo -e "\n${GREEN}Instalacja zakończona!${NC}"
echo -e "\nMożesz teraz deployować aplikacje PHP używając:"
echo -e "${YELLOW}deploy-php example.com https://github.com/user/repo.git${NC}"

# Wyświetl informacje o błędach, jeśli wystąpiły
if [ -f /var/log/php8.3-fpm.log ]; then
    echo -e "\nOstatnie błędy PHP-FPM:"
    tail -n 5 /var/log/php8.3-fpm.log
fi