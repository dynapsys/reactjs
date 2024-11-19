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
            logging.info(f"Konfiguracja Caddy dla {domain} w {php_root}")

            # Backup aktualnej konfiguracji
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"/etc/caddy/Caddyfile.backup_{current_time}"
            shutil.copy2('/etc/caddy/Caddyfile', backup_path)
            logging.info(f"Utworzono backup konfiguracji: {backup_path}")

            # Przygotuj bazową konfigurację
            base_config = """{
        admin off
        log {
            output file /var/log/caddy/access.log
            format json
        }
    }
    """
            # Konfiguracja dla domeny
            domain_config = f"""
    {domain} {{
        root * {php_root}
        php_fastcgi unix//run/php/php8.3-fpm.sock
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
        handle *.php {{
            php_fastcgi unix//run/php/php8.3-fpm.sock
        }}

        # Prevent access to sensitive files
        @sensitive {{
            path /vendor/* /composer.* /.git/* /.env
        }}
        handle @sensitive {{
            respond 404
        }}

        # Default try_files
        try_files {{path}} /index.php?{{query}}
    }}
    """
            # Odczytaj aktualną konfigurację
            current_domains = set()
            with open('/etc/caddy/Caddyfile', 'r') as f:
                current_content = f.read()
                # Znajdź wszystkie skonfigurowane domeny
                for line in current_content.split('\n'):
                    if '{' in line and not line.strip().startswith('#') and not line.strip().startswith('{'):
                        domain_in_config = line.split('{')[0].strip()
                        current_domains.add(domain_in_config)

            # Stwórz nową konfigurację
            new_config = base_config
            # Dodaj konfiguracje dla wszystkich domen oprócz aktualnej
            for existing_domain in current_domains:
                if existing_domain != domain:
                    # Znajdź i dodaj istniejącą konfigurację domeny
                    domain_start = current_content.find(f"{existing_domain} {{")
                    if domain_start != -1:
                        domain_end = current_content.find("}", domain_start)
                        if domain_end != -1:
                            existing_config = current_content[domain_start:domain_end + 1]
                            new_config += f"\n{existing_config}\n"

            # Dodaj nową/zaktualizowaną domenę
            new_config += domain_config

            # Zapisz nową konfigurację
            with open('/etc/caddy/Caddyfile', 'w') as f:
                f.write(new_config)

            # Walidacja konfiguracji
            validate_cmd = ['caddy', 'validate', '--config', '/etc/caddy/Caddyfile']
            validation = subprocess.run(validate_cmd, capture_output=True, text=True)

            if validation.returncode != 0:
                logging.error(f"Błąd walidacji konfiguracji Caddy: {validation.stderr}")
                shutil.copy2(backup_path, '/etc/caddy/Caddyfile')
                raise Exception(f"Błąd walidacji Caddy: {validation.stderr}")

            # Formatowanie Caddyfile
            format_cmd = ['caddy', 'fmt', '--overwrite', '/etc/caddy/Caddyfile']
            subprocess.run(format_cmd, check=True)

            # Przeładuj Caddy
            reload_cmd = ['systemctl', 'reload', 'caddy']
            reload = subprocess.run(reload_cmd, capture_output=True, text=True)

            if reload.returncode != 0:
                logging.error(f"Błąd przeładowania Caddy: {reload.stderr}")
                shutil.copy2(backup_path, '/etc/caddy/Caddyfile')
                raise Exception(f"Błąd przeładowania Caddy: {reload.stderr}")

            logging.info(f"Konfiguracja Caddy zaktualizowana dla {domain}")
            return True

        except Exception as e:
            logging.error(f"Błąd konfiguracji Caddy: {str(e)}\n{traceback.format_exc()}")
            if 'backup_path' in locals():
                shutil.copy2(backup_path, '/etc/caddy/Caddyfile')
                logging.info("Przywrócono backup konfiguracji Caddy")
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

            logging.info(f"Rozpoczynam deployment PHP dla {domain} z {git_url}")

            # Backup istniejącej aplikacji jeśli istnieje
            if os.path.exists(app_dir):
                backup_dir = f"{app_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.move(app_dir, backup_dir)
                logging.info(f"Utworzono backup aplikacji: {backup_dir}")

            # Klonuj repozytorium
            logging.info("Klonowanie repozytorium...")
            clone_cmd = ['git', 'clone', git_url, app_dir]
            clone = subprocess.run(clone_cmd, capture_output=True, text=True)

            if clone.returncode != 0:
                logging.error(f"Błąd klonowania: {clone.stderr}")
                raise Exception(f"Błąd klonowania: {clone.stderr}")

            # Uprawnienia
            logging.info("Ustawianie uprawnień...")
            subprocess.run(['chown', '-R', 'www-data:www-data', app_dir])
            subprocess.run(['chmod', '-R', '755', app_dir])

            # Sprawdź composer.json
            composer_file = os.path.join(app_dir, 'composer.json')
            if os.path.exists(composer_file):
                logging.info("Instalacja zależności Composer...")
                composer_cmd = ['composer', 'install', '--no-dev', '--optimize-autoloader']
                subprocess.run(composer_cmd, cwd=app_dir, check=True)

            # Konfiguracja .env
            env_example = os.path.join(app_dir, '.env.example')
            env_file = os.path.join(app_dir, '.env')
            if os.path.exists(env_example) and not os.path.exists(env_file):
                shutil.copy2(env_example, env_file)
                logging.info("Utworzono plik .env z przykładu")

            # Upewnij się, że index.php istnieje
            index_file = os.path.join(app_dir, 'index.php')
            if not os.path.exists(index_file):
                logging.warning("Brak index.php, tworzę przykładowy plik")
                with open(index_file, 'w') as f:
                    f.write("<?php\nphpinfo();")

            # Konfiguracja Caddy
            if not self.setup_caddy_config(domain, app_dir):
                raise Exception("Błąd konfiguracji Caddy")

            logging.info(f"Aplikacja PHP zdeployowana pomyślnie: {domain}")
            return True

        except Exception as e:
            logging.error(f"Błąd deploymentu PHP: {str(e)}\n{traceback.format_exc()}")
            if 'backup_dir' in locals():
                # Przywróć backup w przypadku błędu
                if os.path.exists(app_dir):
                    shutil.rmtree(app_dir)
                shutil.move(backup_dir, app_dir)
                logging.info("Przywrócono backup aplikacji")
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