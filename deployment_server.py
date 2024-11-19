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
import traceback

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,  # Zmieniono na DEBUG dla bardziej szczegółowych logów
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('/opt/reactjs/logs/deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class DeploymentHandler(BaseHTTPRequestHandler):
    def send_json_response(self, status_code, data):
        """Wysyła odpowiedź JSON"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = json.dumps(data, indent=2).encode('utf-8')
        self.wfile.write(response)

    def check_git_installation(self):
        """Sprawdza czy git jest zainstalowany i dostępny"""
        try:
            version = subprocess.check_output(['git', '--version']).decode().strip()
            logging.info(f"Git version: {version}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Git not found: {str(e)}")
            return False
        except FileNotFoundError:
            logging.error("Git command not found")
            return False

    def clone_git_repo(self, git_url, target_dir):
        """Klonuje repozytorium git do wskazanego katalogu"""
        try:
            # Sprawdź instalację git
            if not self.check_git_installation():
                raise Exception("Git is not installed")

            logging.info(f"Starting git clone: {git_url} -> {target_dir}")

            # Upewnij się, że katalog docelowy jest pusty
            if os.path.exists(target_dir):
                logging.info(f"Removing existing directory: {target_dir}")
                subprocess.run(['rm', '-rf', target_dir], check=True)

            # Tworzenie katalogu nadrzędnego
            os.makedirs(os.path.dirname(target_dir), exist_ok=True)

            # Sprawdź uprawnienia do katalogu
            parent_dir = os.path.dirname(target_dir)
            logging.info(f"Checking permissions for {parent_dir}")
            if not os.access(parent_dir, os.W_OK):
                logging.error(f"No write permission to {parent_dir}")
                raise Exception(f"No write permission to {parent_dir}")

            # Klonowanie z pełnym logowaniem
            logging.info(f"Executing git clone {git_url}")
            process = subprocess.Popen(
                ['git', 'clone', git_url, target_dir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Czytanie output w czasie rzeczywistym
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    logging.info(f"Git output: {output.strip()}")

            # Pobierz stderr po zakończeniu
            _, stderr = process.communicate()
            if stderr:
                logging.error(f"Git stderr: {stderr}")

            # Sprawdź kod wyjścia
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, 'git clone')

            # Sprawdź czy katalog został utworzony i zawiera pliki
            if not os.path.exists(target_dir) or not os.listdir(target_dir):
                raise Exception("Git clone completed but directory is empty")

            # Wyświetl zawartość sklonowanego repozytorium
            logging.info(f"Repository contents: {os.listdir(target_dir)}")

            return True

        except subprocess.CalledProcessError as e:
            logging.error(f"Git clone failed: {str(e)}\nCommand output: {e.output if hasattr(e, 'output') else 'No output'}")
            return False
        except Exception as e:
            logging.error(f"Error during git clone: {str(e)}\n{traceback.format_exc()}")
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

            # Wyciągnij główną domenę
            domain_parts = domain.split('.')
            if len(domain_parts) > 2:
                main_domain = '.'.join(domain_parts[-2:])
                logging.info(f"Subdomena wykryta. Główna domena: {main_domain}")
            else:
                main_domain = domain

            # Pobierz publiczny IP serwera
            ip_process = subprocess.Popen(
                ['curl', '-s', 'http://ipv4.icanhazip.com'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            ip_stdout, ip_stderr = ip_process.communicate()

            if ip_process.returncode != 0:
                logging.error(f"Błąd pobierania IP: {ip_stderr.decode()}")
                return False

            ip = ip_stdout.decode().strip()
            logging.info(f"Pobrano IP: {ip}")

            # Pobierz Zone ID
            logging.info(f"Pobieranie Zone ID z Cloudflare dla domeny: {main_domain}")
            zone_cmd = [
                'curl', '-s', '-X', 'GET',
                f'https://api.cloudflare.com/client/v4/zones?name={main_domain}',
                '-H', f'Authorization: Bearer {cf_token}',
                '-H', 'Content-Type: application/json'
            ]
            zone_process = subprocess.Popen(zone_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            zone_stdout, zone_stderr = zone_process.communicate()

            try:
                zone_response = json.loads(zone_stdout.decode())

                if not zone_response.get('success', False):
                    errors = zone_response.get('errors', [])
                    logging.error(f"Błąd API Cloudflare: {errors}")
                    return False

                if not zone_response.get('result', []):
                    logging.error(f"Nie znaleziono domeny {main_domain} w Cloudflare")
                    return False

                zone_id = zone_response['result'][0]['id']
                logging.info(f"Pobrano Zone ID: {zone_id}")

                # Sprawdź istniejące rekordy DNS
                existing_record_cmd = [
                    'curl', '-s', '-X', 'GET',
                    f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=A&name={domain}',
                    '-H', f'Authorization: Bearer {cf_token}',
                    '-H', 'Content-Type: application/json'
                ]

                record_process = subprocess.Popen(existing_record_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                record_stdout, record_stderr = record_process.communicate()
                record_response = json.loads(record_stdout.decode())

                dns_data = {
                    'type': 'A',
                    'name': domain,
                    'content': ip,
                    'ttl': 1,
                    'proxied': True
                }

                if record_response.get('result', []):
                    # Aktualizuj istniejący rekord
                    record_id = record_response['result'][0]['id']
                    logging.info(f"Znaleziono istniejący rekord DNS {record_id}, aktualizacja...")

                    update_cmd = [
                        'curl', '-s', '-X', 'PUT',
                        f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}',
                        '-H', f'Authorization: Bearer {cf_token}',
                        '-H', 'Content-Type: application/json',
                        '-d', json.dumps(dns_data)
                    ]

                    update_process = subprocess.Popen(update_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    update_stdout, update_stderr = update_process.communicate()
                    update_response = json.loads(update_stdout.decode())

                    if not update_response.get('success', False):
                        logging.error(f"Błąd aktualizacji rekordu DNS: {update_response.get('errors', [])}")
                        return False
                else:
                    # Utwórz nowy rekord
                    logging.info("Tworzenie nowego rekordu DNS...")
                    create_cmd = [
                        'curl', '-s', '-X', 'POST',
                        f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records',
                        '-H', f'Authorization: Bearer {cf_token}',
                        '-H', 'Content-Type: application/json',
                        '-d', json.dumps(dns_data)
                    ]

                    create_process = subprocess.Popen(create_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    create_stdout, create_stderr = create_process.communicate()
                    create_response = json.loads(create_stdout.decode())

                    if not create_response.get('success', False):
                        logging.error(f"Błąd tworzenia rekordu DNS: {create_response.get('errors', [])}")
                        return False

                logging.info("DNS zaktualizowany pomyślnie")
                return True

            except json.JSONDecodeError as e:
                logging.error(f"Błąd parsowania odpowiedzi JSON: {str(e)}\nResponse: {zone_stdout.decode()}")
                return False
            except (IndexError, KeyError) as e:
                logging.error(f"Błąd w strukturze odpowiedzi: {str(e)}\nResponse: {zone_stdout.decode()}")
                return False
            except Exception as e:
                logging.error(f"Nieoczekiwany błąd: {str(e)}\n{traceback.format_exc()}")
                return False

        except Exception as e:
            logging.error(f"Cloudflare DNS update error: {str(e)}\n{traceback.format_exc()}")
            return False

        finally:
            logging.info("Zakończono proces aktualizacji DNS")


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
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_json_response(400, {"error": "Empty request"})
                return

            post_data = self.rfile.read(content_length).decode('utf-8')
            logging.info(f"Received POST data: {post_data}")

            try:
                params = json.loads(post_data)
            except json.JSONDecodeError as e:
                logging.error(f"JSON parse error: {str(e)}")
                self.send_json_response(400, {"error": f"Invalid JSON: {str(e)}"})
                return

            # Sprawdzenie wymaganych pól
            if not all(key in params for key in ['domain', 'cf_token', 'source']):
                self.send_json_response(400, {"error": "Missing required fields"})
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
            self.send_json_response(200, {
                "status": "success",
                "message": "Deployment completed successfully",
                "domain": domain,
                "project_dir": project_dir,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logging.error(f"Server error: {str(e)}\n{traceback.format_exc()}")
            self.send_json_response(500, {
                "error": "Server error",
                "details": str(e)
            })

def run_server(port=8000):
    try:
        server_address = ('', port)
        httpd = HTTPServer(server_address, DeploymentHandler)
        logging.info(f'Starting deployment server on port {port}...')
        httpd.serve_forever()
    except Exception as e:
        logging.error(f"Server error: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == '__main__':
    # Upewnij się, że katalogi istnieją
    os.makedirs('/opt/reactjs/logs', exist_ok=True)
    os.makedirs('/opt/reactjs/sites', exist_ok=True)

    # Sprawdź uprawnienia
    for dir_path in ['/opt/reactjs/logs', '/opt/reactjs/sites']:
        if not os.access(dir_path, os.W_OK):
            print(f"Warning: No write permission to {dir_path}")

    run_server()

# systemctl status reactjs --no-pager
# systemctl restart reactjs
# systemctl status reactjs --no-pager
# lsof -t -i tcp:8000 | xargs kill -9

