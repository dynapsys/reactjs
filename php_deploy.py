#!/usr/bin/python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import os
import logging
import sys
import traceback
from datetime import datetime
import shutil

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('/opt/php-deploy/logs/deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


class PHPDeploymentHandler(BaseHTTPRequestHandler):
    def setup_caddy_config(self, domain, php_root):
        """Konfiguruje Caddy dla PHP"""
        try:
            config = f"""
{domain} {{
    root * {php_root}
    php_fastcgi unix//run/php/php8.2-fpm.sock
    file_server
    encode gzip

    log {{
        output file /var/log/caddy/{domain}.log {{
            roll_size 10mb
            roll_keep 5
        }}
        format json
    }}

    header {{
        # Security headers
        Strict-Transport-Security "max-age=31536000;"
        X-XSS-Protection "1; mode=block"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"

        # Remove server tokens
        -Server
        -X-Powered-By
    }}

    # PHP file handling
    @phpfiles {{
        path_regexp \.php$
    }}
    handle @phpfiles {{
        php_fastcgi unix//run/php/php8.2-fpm.sock
    }}

    # Prevent access to sensitive files
    @sensitive {{
        path /vendor/* /composer.* /.git/* /.env
    }}
    handle @sensitive {{
        respond 404
    }}
}}
"""
            # Dodaj konfigurację do Caddyfile
            with open('/etc/caddy/Caddyfile', 'a') as f:
                f.write(config)

            # Przeładuj Caddy
            subprocess.run(['systemctl', 'reload', 'caddy'], check=True)
            logging.info(f"Konfiguracja Caddy zaktualizowana dla {domain}")
            return True
        except Exception as e:
            logging.error(f"Błąd konfiguracji Caddy: {str(e)}")
            return False

    def setup_php_fpm_pool(self, domain):
        """Tworzy dedykowany pool PHP-FPM"""
        try:
            pool_config = f"""[{domain}]
user = www-data
group = www-data
listen = /run/php/{domain}.sock
listen.owner = www-data
listen.group = www-data
pm = dynamic
pm.max_children = 5
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 3
"""
            with open(f'/etc/php/8.2/fpm/pool.d/{domain}.conf', 'w') as f:
                f.write(pool_config)

            subprocess.run(['systemctl', 'restart', 'php8.2-fpm'], check=True)
            return True
        except Exception as e:
            logging.error(f"Błąd konfiguracji PHP-FPM: {str(e)}")
            return False

    def deploy_php_app(self, domain, git_url):
        """Deployuje aplikację PHP"""
        try:
            base_dir = '/var/www'
            app_dir = os.path.join(base_dir, domain)

            # Usuń istniejący katalog
            if os.path.exists(app_dir):
                shutil.rmtree(app_dir)

            # Klonuj repozytorium
            subprocess.run(['git', 'clone', git_url, app_dir], check=True)

            # Uprawnienia
            subprocess.run(['chown', '-R', 'www-data:www-data', app_dir])
            subprocess.run(['chmod', '-R', '755', app_dir])

            # Sprawdź czy istnieje composer.json
            if os.path.exists(os.path.join(app_dir, 'composer.json')):
                logging.info("Instalacja zależności Composer...")
                subprocess.run(['composer', 'install', '--no-dev'], cwd=app_dir, check=True)

            # Utwórz i skonfiguruj .env jeśli potrzebne
            env_example = os.path.join(app_dir, '.env.example')
            env_file = os.path.join(app_dir, '.env')
            if os.path.exists(env_example) and not os.path.exists(env_file):
                shutil.copy2(env_example, env_file)

            # Konfiguracja Caddy
            if not self.setup_caddy_config(domain, app_dir):
                raise Exception("Błąd konfiguracji Caddy")

            # Konfiguracja PHP-FPM
            if not self.setup_php_fpm_pool(domain):
                raise Exception("Błąd konfiguracji PHP-FPM")

            logging.info(f"Aplikacja PHP zdeployowana pomyślnie: {domain}")
            return True

        except Exception as e:
            logging.error(f"Błąd deploymentu PHP: {str(e)}\n{traceback.format_exc()}")
            return False

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')

            try:
                params = json.loads(post_data)
                logging.info(f"Otrzymano żądanie: {json.dumps(params, indent=2)}")
            except json.JSONDecodeError as e:
                self.send_error(400, f"Invalid JSON: {str(e)}")
                return

            # Sprawdzenie wymaganych pól
            if not all(key in params for key in ['domain', 'git_url']):
                self.send_error(400, "Wymagane pola: domain, git_url")
                return

            # Deploy aplikacji
            if self.deploy_php_app(params['domain'], params['git_url']):
                response = {
                    "status": "success",
                    "message": "PHP app deployed successfully",
                    "domain": params['domain'],
                    "timestamp": datetime.now().isoformat()
                }
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response, indent=2).encode())
            else:
                self.send_error(500, "Deployment failed")

        except Exception as e:
            logging.error(f"Server error: {str(e)}\n{traceback.format_exc()}")
            self.send_error(500, f"Server error: {str(e)}")


def run_server(port=8001):
    server_address = ('', port)
    httpd = HTTPServer(server_address, PHPDeploymentHandler)
    logging.info(f'Starting PHP deployment server on port {port}...')
    httpd.serve_forever()


if __name__ == '__main__':
    os.makedirs('/opt/php-deploy/logs', exist_ok=True)
    run_server()