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

class DeploymentHandler(BaseHTTPRequestHandler):
    def clone_git_repo(self, git_url, target_dir):
        """Klonuje repozytorium git do wskazanego katalogu"""
        try:
            # Usuń stary katalog jeśli istnieje
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)

            # Klonowanie repozytorium
            subprocess.run(['git', 'clone', git_url, target_dir], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Git clone error: {str(e)}")
            return False

    def build_react_project(self, project_dir):
        """Buduje projekt React"""
        try:
            # Instalacja zależności
            subprocess.run(['npm', 'install'], cwd=project_dir, check=True)

            # Build projektu
            subprocess.run(['npm', 'run', 'build'], cwd=project_dir, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Build error: {str(e)}")
            return False

    def update_cloudflare_dns(self, domain, cf_token):
        """Aktualizuje DNS w Cloudflare"""
        try:
            # Pobierz publiczny IP serwera
            ip = subprocess.check_output(['curl', '-s', 'http://ipv4.icanhazip.com']).decode().strip()

            # Pobierz Zone ID
            zone_cmd = [
                'curl', '-s', '-X', 'GET',
                f'https://api.cloudflare.com/client/v4/zones?name={domain}',
                '-H', f'Authorization: Bearer {cf_token}',
                '-H', 'Content-Type: application/json'
            ]
            zone_response = json.loads(subprocess.check_output(zone_cmd).decode())
            zone_id = zone_response['result'][0]['id']

            # Aktualizuj rekord A
            dns_cmd = [
                'curl', '-s', '-X', 'POST',
                f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records',
                '-H', f'Authorization: Bearer {cf_token}',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps({
                    'type': 'A',
                    'name': domain,
                    'content': ip,
                    'ttl': 1,
                    'proxied': True
                })
            ]
            subprocess.run(dns_cmd, check=True)
            return True
        except Exception as e:
            print(f"Cloudflare DNS update error: {str(e)}")
            return False

    def setup_pm2(self, domain, project_dir):
        """Konfiguruje PM2 dla aplikacji"""
        try:
            # Zatrzymanie istniejącej instancji
            subprocess.run(['pm2', 'delete', domain], stderr=subprocess.DEVNULL)

            # Start nowej instancji
            subprocess.run([
                'pm2', 'start', 'npm', '--name', domain,
                '--', 'start'
            ], cwd=project_dir, check=True)

            # Zapisanie konfiguracji PM2
            subprocess.run(['pm2', 'save'], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"PM2 setup error: {str(e)}")
            return False

    def log_message(self, message):
        """Zapisuje wiadomość do logu"""
        with open('/opt/reactjs/logs/deployment.log', 'a') as log:
            log.write(f"[{self.log_date_time_string()}] {message}\n")

    def is_valid_git_url(self, url):
        """Sprawdza czy URL jest poprawnym adresem Git"""
        git_patterns = [
            r'^https?://github\.com/[\w-]+/[\w.-]+(?:\.git)?$',
            r'^git@github\.com:[\w-]+/[\w.-]+(?:\.git)?$',
            r'^https?://gitlab\.com/[\w-]+/[\w.-]+(?:\.git)?$',
            r'^https?://bitbucket\.org/[\w-]+/[\w.-]+(?:\.git)?$'
        ]
        return any(re.match(pattern, url) for pattern in git_patterns)

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')

            try:
                params = json.loads(post_data)
                self.log_message(f"Received deployment request: {json.dumps(params, indent=2)}")
            except json.JSONDecodeError as e:
                self.log_message(f"Error parsing JSON: {str(e)}\nData: {post_data}")
                self.send_error(400, f"Invalid JSON: {str(e)}")
                return

            # Sprawdzenie wymaganych parametrów
            required_params = ['domain', 'cf_token', 'source']
            if not all(param in params for param in required_params):
                self.send_error(400, "Missing required parameters")
                return

            domain = params['domain']
            cf_token = params['cf_token']
            source = params['source']

            # Katalog docelowy dla projektu
            project_dir = f"/opt/reactjs/sites/{domain}"

            # Obsługa różnych typów źródeł
            if self.is_valid_git_url(source):
                self.log_message(f"Cloning Git repository: {source}")
                if not self.clone_git_repo(source, project_dir):
                    self.send_error(500, "Git clone failed")
                    return
            elif source.startswith('data:application/tar+gz;base64,'):
                self.log_message("Processing base64 data")
                try:
                    # Dekodowanie i rozpakowanie archiwum
                    base64_data = source.replace('data:application/tar+gz;base64,', '')
                    with tempfile.TemporaryDirectory() as temp_dir:
                        archive_path = os.path.join(temp_dir, 'source.tar.gz')
                        with open(archive_path, 'wb') as f:
                            f.write(base64.b64decode(base64_data))

                        # Przygotowanie katalogu docelowego
                        if os.path.exists(project_dir):
                            shutil.rmtree(project_dir)
                        shutil.copytree(temp_dir, project_dir)
                except Exception as e:
                    self.log_message(f"Error processing base64 data: {str(e)}")
                    self.send_error(500, "Error processing source data")
                    return
            else:
                self.send_error(400, "Invalid source format")
                return

            # Build projektu
            self.log_message("Building React project")
            if not self.build_react_project(project_dir):
                self.send_error(500, "Build failed")
                return

            # Konfiguracja DNS
            self.log_message("Updating Cloudflare DNS")
            if not self.update_cloudflare_dns(domain, cf_token):
                self.send_error(500, "DNS update failed")
                return

            # Konfiguracja PM2
            self.log_message("Setting up PM2")
            if not self.setup_pm2(domain, project_dir):
                self.send_error(500, "PM2 setup failed")
                return

            # Sukces
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "success",
                "message": "Deployment completed successfully",
                "domain": domain,
                "project_dir": project_dir
            }
            self.wfile.write(json.dumps(response).encode())
            self.log_message(f"Deployment successful: {json.dumps(response, indent=2)}")

        except Exception as e:
            error_msg = f"Deployment error: {str(e)}\n{traceback.format_exc()}"
            self.log_message(error_msg)
            self.send_error(500, error_msg)

def run_server():
    server_address = ('0.0.0.0', 8000)
    httpd = HTTPServer(server_address, DeploymentHandler)
    print("Deployment server running on port 8000...")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()