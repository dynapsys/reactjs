#!/bin/bash

# Kolory
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Naprawa konfiguracji Caddy...${NC}"

# Backup aktualnej konfiguracji
backup_file="/etc/caddy/Caddyfile.backup_$(date +%Y%m%d_%H%M%S)"
cp /etc/caddy/Caddyfile "$backup_file"
echo "Utworzono backup: $backup_file"

# Podstawowa konfiguracja
cat > /etc/caddy/Caddyfile << 'EOF'
{
    admin off
    log {
        output file /var/log/caddy/access.log
        format json
    }
}

php-test.dynapsys.com {
    root * /var/www/php-test.dynapsys.com
    php_fastcgi unix//run/php/php8.3-fpm.sock
    file_server
    encode gzip

    log {
        output file /var/log/caddy/php-test.dynapsys.com.log {
            roll_size 10mb
            roll_keep 5
        }
        format json
    }

    header {
        # Security headers
        Strict-Transport-Security "max-age=31536000;"
        X-XSS-Protection "1; mode=block"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
        # Remove server tokens
        -Server
        -X-Powered-By
    }

    # PHP file handling
    handle *.php {
        php_fastcgi unix//run/php/php8.3-fpm.sock
    }

    # Prevent access to sensitive files
    @sensitive {
        path /vendor/* /composer.* /.git/* /.env
    }
    handle @sensitive {
        respond 404
    }

    # Default try_files
    try_files {path} /index.php?{query}
}
EOF

# Formatowanie konfiguracji
echo -e "\n${YELLOW}Formatowanie konfiguracji...${NC}"
caddy fmt --overwrite /etc/caddy/Caddyfile

# Walidacja
echo -e "\n${YELLOW}Sprawdzanie konfiguracji...${NC}"
if caddy validate --config /etc/caddy/Caddyfile; then
    echo -e "${GREEN}Konfiguracja jest poprawna${NC}"

    # Restart Caddy
    echo -e "\n${YELLOW}Restart Caddy...${NC}"
    systemctl restart caddy
    sleep 2

    # Sprawdź status
    if systemctl is-active --quiet caddy; then
        echo -e "${GREEN}Caddy działa poprawnie${NC}"
    else
        echo -e "${RED}Błąd: Caddy nie uruchomił się${NC}"
        echo "Przywracanie backup..."
        cp "$backup_file" /etc/caddy/Caddyfile
        systemctl restart caddy
    fi
else
    echo -e "${RED}Błąd: Nieprawidłowa konfiguracja${NC}"
    echo "Przywracanie backup..."
    cp "$backup_file" /etc/caddy/Caddyfile
    systemctl restart caddy
fi

# Sprawdź PHP-FPM
echo -e "\n${YELLOW}Sprawdzanie PHP-FPM...${NC}"
if [ -S /run/php/php8.3-fpm.sock ]; then
    echo -e "${GREEN}Socket PHP-FPM istnieje${NC}"
else
    echo -e "${RED}Brak socketu PHP-FPM!${NC}"
    echo "Restart PHP-FPM..."
    systemctl restart php8.3-fpm
fi

echo -e "\n${YELLOW}Logi Caddy:${NC}"
tail -n 10 /var/log/caddy/access.log