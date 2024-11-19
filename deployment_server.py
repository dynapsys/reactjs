#!/usr/bin/python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import os
import base64
import tempfile
import traceback
import shutil
from urllib.parse import urlparse
import re
import logging
import sys
from datetime import datetime

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/reactjs/logs/deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class DeploymentHandler(BaseHTTPRequestHandler):
    def clone_git_repo(self, git_url, target_dir):
        """Klonuje repozytorium git do wskazanego katalogu"""
        try:
            logging.info(f"Rozpoczynam klonowanie repo: {git_url} do {target_dir}")

            if os.path.exists(target_dir):
                logging.info(f"Usuwanie istniejącego katalogu: {target_dir}")
                shutil.rmtree(target_dir)

            # Klonowanie repozytorium z wyświetlaniem output
            process = subprocess.Popen(
                ['git', 'clone', git_url, target_dir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                logging.info("Git clone zakończony sukcesem")
                return True
            else:
                logging.error(f"Błąd git clone: {stderr.decode()}")
                return False

        except subprocess.CalledProcessError as e:
            logging.error(f"Git clone error: {str(e)}\n{traceback.format_exc()}")
            return False

    def build_react_project(self, project_dir):
        """Buduje projekt React"""
        try:
            logging.info(f"Rozpoczynam build projektu w: {project_dir}")

            # Sprawdź czy package.json istnieje
            if not os.path.exists(os.path.join(project_dir, 'package.json')):
                logging.error("Brak package.json w projekcie")
                return False

            # Instalacja zależności z wyświetlaniem output
            logging.info("Instalacja zależności npm...")
            process = subprocess.Popen(
                ['npm', 'install'],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                logging.error(f"Błąd npm install: {stderr.decode()}")
                return False

            # Build projektu
            logging.info("Uruchamianie npm build...")
            process = subprocess.Popen(
                ['npm', 'run', 'build'],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                logging.info("Build zakończony sukcesem")
                return True
            else:
                logging.error(f"Błąd build: {stderr.decode()}")
                return False

        except subprocess.CalledProcessError as e:
            logging.error(f"Build error: {str(e)}\n{traceback.format_exc()}")
            return False

    def update_cloudflare_dns(self, domain, cf_token):
        """Aktualizuje DNS w Cloudflare"""
        try:
            logging.info(f"Aktualizacja DNS dla domeny: {domain}")

            # Pobierz publiczny IP serwera
            ip_process = subprocess.Popen(
                ['curl', '-s', 'http://ipv4.icanhazip.com'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            ip_stdout, ip_stderr = ip_process.communicate()
            ip = ip_stdout.decode().strip()

            logging.info(f"Pobrano IP: {ip}")

            # Pobierz Zone ID
            logging.info("Pobieranie Zone ID z Cloudflare...")
            zone_cmd = [
                'curl', '-s', '-X', 'GET',
                f'https://api.cloudflare.com/client/v4/zones?name={domain}',
                '-H', f'Authorization: Bearer {cf_token}',
                '-H', 'Content-Type: application/json'
            ]
            zone_process = subprocess.Popen(zone_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            zone_stdout, zone_stderr = zone_process.communicate()

            try:
                zone_response = json.loads(zone_stdout.decode())
                zone_id = zone_response['result'][0]['id']
                logging.info(f"Pobrano Zone ID: {zone_id}")
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                logging.error(f"Błąd pobierania Zone ID: {str(e)}\nResponse: {zone_stdout.decode()}")
                return False

            # Aktualizuj rekord A
            logging.info("Aktualizacja rekordu A...")
            dns_data = {
                'type': 'A',
                'name': domain,
                'content': ip,
                'ttl': 1,
                'proxied': True
            }

            dns_cmd = [
                'curl', '-s', '-X', 'POST',
                f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records',
                '-H', f'Authorization: Bearer {cf_token}',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(dns_data)
            ]

            dns_process = subprocess.Popen(dns_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            dns_stdout, dns_stderr = dns_process.communicate()

            if dns_process.returncode == 0:
                logging.info("DNS zaktualizowany pomyślnie")
                return True
            else:
                logging.error(f"Błąd aktualizacji DNS: {dns_stderr.decode()}")
                return False

        except Exception as e:
            logging.error(f"Cloudflare DNS update error: {str(e)}\n{traceback.format_exc()}")
            return False

    def setup_pm2(self, domain, project_dir):
        """Konfiguruje PM2 dla aplikacji"""
        try:
            logging.info(f"Konfiguracja PM2 dla domeny: {domain}")

            # Zatrzymanie istniejącej instancji
            logging.info("Zatrzymywanie istniejącej instancji PM2...")
            subprocess.run(['pm2', 'delete', domain], stderr=subprocess.DEVNULL)

            # Start nowej instancji
            logging.info("Uruchamianie nowej instancji PM2...")
            process = subprocess.Popen(
                ['pm2', 'start', 'npm', '--name', domain, '--', 'start'],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                logging.error(f"Błąd startu PM2: {stderr.decode()}")
                return False

            # Zapisanie konfiguracji PM2
            logging.info("Zapisywanie konfiguracji PM2...")
            save_process = subprocess.Popen(
                ['pm2', 'save'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            save_stdout, save_stderr = save_process.communicate()

            if save_process.returncode == 0:
                logging.info("Konfiguracja PM2 zapisana pomyślnie")
                return True
            else:
                logging.error(f"Błąd zapisu PM2: {save_stderr.decode()}")
                return False

        except subprocess.CalledProcessError as e:
            logging.error(f"PM2 setup error: {str(e)}\n{traceback.format_exc()}")
            return False

    def is_valid_git_url(self, url):
        """Sprawdza czy URL jest poprawnym adresem Git"""
        git_patterns = [
            r'^https?://github\.com/[\w-]+/[\w.-]+(?:\.git)?$',
            r'^git@github\.com:[\w-]+/[\w.-]+(?:\.git)?$',
            r'^https?://gitlab\.com/[\w-]+/[\w.-]+(?:\.git)?$',
            r'^https?://bitbucket\.org/[\w-]+/[\w.-]+(?:\.git)?$'
        ]
        is_valid = any(re.match(pattern, url) for pattern in git_patterns)
        logging.info(f"Sprawdzanie URL git: {url} - {'poprawny' if is_valid else 'niepoprawny'}")
        return is_valid

    def do_POST(self):
        try:
            logging.info(f"Otrzymano żądanie POST od {self.client_address[0]}")

            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                logging.error("Otrzymano puste żądanie")
                self.send_error(400, "Empty request")
                return

            post_data = self.rfile.read(content_length).decode('utf-8')

            try:
                params = json.loads(post_data)
                logging.info(f"Otrzymane parametry: {json.dumps(params, indent=2)}")
            except json.JSONDecodeError as e:
                logging.error(f"Błąd parsowania JSON: {str(e)}\nDane: {post_data}")
                self.send_error(400, f"Invalid JSON: {str(e)}")
                return

            # Sprawdzenie wymaganych parametrów
            required_params = ['domain', 'cf_token', 'source']
            missing_params = [param for param in required_params if param not in params]
            if missing_params:
                logging.error(f"Brak wymaganych parametrów: {missing_params}")
                self.send_error(400, f"Missing required parameters: {', '.join(missing_params)}")
                return

            domain = params['domain']
            cf_token = params['cf_token']
            source = params['source']

            # Katalog docelowy dla projektu
            project_dir = f"/opt/reactjs/sites/{domain}"
            logging.info(f"Katalog docelowy: {project_dir}")

            # Obsługa różnych typów źródeł
            if self.is_valid_git_url(source):
                if not self.clone_git_repo(source, project_dir):
                    self.send_error(500, "Git clone failed")
                    return
            elif source.startswith('data:application/tar+gz;base64,'):
                logging.info("Przetwarzanie danych base64")
                try:
                    base64_data = source.replace('data:application/tar+gz;base64,', '')
                    with tempfile.TemporaryDirectory() as temp_dir:
                        archive_path = os.path.join(temp_dir, 'source.tar.gz')
                        logging.info(f"Zapisywanie archiwum do: {archive_path}")

                        with open(archive_path, 'wb') as f:
                            f.write(base64.b64decode(base64_data))

                        if os.path.exists(project_dir):
                            logging.info(f"Usuwanie istniejącego katalogu: {project_dir}")
                            shutil.rmtree(project_dir)

                        logging.info(f"Kopiowanie plików do: {project_dir}")
                        shutil.copytree(temp_dir, project_dir)
                except Exception as e:
                    logging.error(f"Błąd przetwarzania danych base64: {str(e)}\n{traceback.format_exc()}")
                    self.send_error(500, "Error processing source data")
                    return
            else:
                logging.error(f"Nieprawidłowy format źródła: {source[:100]}...")
                self.send_error(400, "Invalid source format")
                return

            # Build projektu
            if not self.build_react_project(project_dir):
                self.send_error(500, "Build failed")
                return

            # Konfiguracja DNS
            if not self.update_cloudflare_dns(domain, cf_token):
                self.send_error(500, "DNS update failed")
                return

            # Konfiguracja PM2
            if not self.setup_pm2(domain, project_dir):
                self.send_error(500, "PM2 setup failed")
                return

            # Sukces
            response = {
                "status": "success",
                "message": "Deployment completed successfully",
                "domain": domain,
                "project_dir": project_dir,
                "timestamp": datetime.now().isoformat()
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())

            logging.info(f"Deployment zakończony sukcesem: {json.dumps(response, indent=2)}")

        except Exception as e:
            error_msg = f"Błąd deploymentu: {str(e)}\n{traceback.format_exc()}"
            logging.error(error_msg)
            self.send_error(500, error_msg)

def run_server():
    try:
        server_address = ('0.0.0.0', 8000)
        httpd = HTTPServer(server_address, DeploymentHandler)
        logging.info("Uruchamianie serwera deploymentu na porcie 8000...")
        print("Deployment server running on port 8000...")
        httpd.serve_forever()
    except Exception as e:
        logging.error(f"Błąd uruchomienia serwera: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    # Upewnij się, że katalog logów istnieje
    os.makedirs('/opt/reactjs/logs', exist_ok=True)
    run_server()

# systemctl status reactjs --no-pager
# systemctl restart reactjs
# systemctl status reactjs --no-pager
