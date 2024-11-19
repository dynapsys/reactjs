#!/usr/bin/python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import os
import base64
import tempfile
import shutil
from urllib.parse import urlparse
import logging
import sys
from datetime import datetime
import traceback

from .dns import update_cloudflare_dns
from .git import clone_git_repo, is_valid_git_url

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class DeploymentHandler(BaseHTTPRequestHandler):
    def send_json_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = json.dumps(data, indent=2).encode('utf-8')
        self.wfile.write(response)

    def check_git_installation(self):
        """Check if git is installed and available"""
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

    def build_react_project(self, project_dir):
        """Build React project"""
        try:
            logging.info(f"Starting build in: {project_dir}")

            # Check if package.json exists
            if not os.path.exists(os.path.join(project_dir, 'package.json')):
                logging.error("No package.json in project")
                return False

            # Install dependencies with output display
            logging.info("Installing npm dependencies...")
            process = subprocess.Popen(
                ['npm', 'install'],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                logging.error(f"npm install error: {stderr.decode()}")
                return False

            # Build project
            logging.info("Running npm build...")
            process = subprocess.Popen(
                ['npm', 'run', 'build'],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                logging.info("Build completed successfully")
                return True
            else:
                logging.error(f"Build error: {stderr.decode()}")
                return False

        except subprocess.CalledProcessError as e:
            logging.error(f"Build error: {str(e)}\n{traceback.format_exc()}")
            return False

    def setup_pm2(self, domain, project_dir):
        """Configure PM2 for the application"""
        try:
            logging.info(f"Configuring PM2 for domain: {domain}")

            # Stop existing instance
            logging.info("Stopping existing PM2 instance...")
            subprocess.run(['pm2', 'delete', domain], stderr=subprocess.DEVNULL)

            # Start new instance
            logging.info("Starting new PM2 instance...")
            process = subprocess.Popen(
                ['pm2', 'start', 'npm', '--name', domain, '--', 'start'],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                logging.error(f"PM2 start error: {stderr.decode()}")
                return False

            # Save PM2 configuration
            logging.info("Saving PM2 configuration...")
            save_process = subprocess.Popen(
                ['pm2', 'save'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            save_stdout, save_stderr = save_process.communicate()

            if save_process.returncode == 0:
                logging.info("PM2 configuration saved successfully")
                return True
            else:
                logging.error(f"PM2 save error: {save_stderr.decode()}")
                return False

        except subprocess.CalledProcessError as e:
            logging.error(f"PM2 setup error: {str(e)}\n{traceback.format_exc()}")
            return False

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

            # Check required fields
            if not all(key in params for key in ['domain', 'cf_token', 'source']):
                self.send_json_response(400, {"error": "Missing required fields"})
                return

            domain = params['domain']
            cf_token = params['cf_token']
            source = params['source']

            # Target directory for project
            project_dir = f"/opt/reactjs/sites/{domain}"
            logging.info(f"Target directory: {project_dir}")

            # Handle different source types
            if is_valid_git_url(source):
                if not clone_git_repo(source, project_dir):
                    self.send_error(500, "Git clone failed")
                    return
            elif source.startswith('data:application/tar+gz;base64,'):
                logging.info("Processing base64 data")
                try:
                    base64_data = source.replace('data:application/tar+gz;base64,', '')
                    with tempfile.TemporaryDirectory() as temp_dir:
                        archive_path = os.path.join(temp_dir, 'source.tar.gz')
                        logging.info(f"Saving archive to: {archive_path}")

                        with open(archive_path, 'wb') as f:
                            f.write(base64.b64decode(base64_data))

                        if os.path.exists(project_dir):
                            logging.info(f"Removing existing directory: {project_dir}")
                            shutil.rmtree(project_dir)

                        logging.info(f"Copying files to: {project_dir}")
                        shutil.copytree(temp_dir, project_dir)
                except Exception as e:
                    logging.error(f"Error processing base64 data: {str(e)}\n{traceback.format_exc()}")
                    self.send_error(500, "Error processing source data")
                    return
            else:
                logging.error(f"Invalid source format: {source[:100]}...")
                self.send_error(400, "Invalid source format")
                return

            # Build project
            if not self.build_react_project(project_dir):
                self.send_error(500, "Build failed")
                return

            # Configure DNS
            if not update_cloudflare_dns(domain, cf_token):
                self.send_error(500, "DNS update failed")
                return

            # Configure PM2
            if not self.setup_pm2(domain, project_dir):
                self.send_error(500, "PM2 setup failed")
                return

            # Success
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
    """Run the deployment server"""
    try:
        server_address = ('', port)
        httpd = HTTPServer(server_address, DeploymentHandler)
        logging.info(f'Starting deployment server on port {port}...')
        httpd.serve_forever()
    except Exception as e:
        logging.error(f"Server error: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs('/opt/reactjs/logs', exist_ok=True)
    os.makedirs('/opt/reactjs/sites', exist_ok=True)

    # Check permissions
    for dir_path in ['/opt/reactjs/logs', '/opt/reactjs/sites']:
        if not os.access(dir_path, os.W_OK):
            print(f"Warning: No write permission to {dir_path}")

    run_server()
