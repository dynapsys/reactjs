import unittest
from unittest.mock import patch, MagicMock
import json
import os
import tempfile
import shutil
from http.server import HTTPServer
from dynapsys.deployment import DeploymentHandler, run_server

class TestDeploymentHandler(unittest.TestCase):
    def setUp(self):
        self.handler = DeploymentHandler(None, None, None)
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_check_git_installation(self):
        self.assertTrue(self.handler.check_git_installation())

    @patch('subprocess.Popen')
    def test_build_react_project_success(self, mock_popen):
        # Create test package.json
        os.makedirs(self.test_dir, exist_ok=True)
        with open(os.path.join(self.test_dir, 'package.json'), 'w') as f:
            json.dump({'name': 'test-project'}, f)

        # Mock npm install process
        install_process = MagicMock()
        install_process.returncode = 0
        install_process.communicate.return_value = (b'', b'')

        # Mock npm build process
        build_process = MagicMock()
        build_process.returncode = 0
        build_process.communicate.return_value = (b'', b'')

        mock_popen.side_effect = [install_process, build_process]

        result = self.handler.build_react_project(self.test_dir)
        self.assertTrue(result)

    @patch('subprocess.Popen')
    def test_build_react_project_no_package_json(self, mock_popen):
        result = self.handler.build_react_project(self.test_dir)
        self.assertFalse(result)
        mock_popen.assert_not_called()

    @patch('subprocess.Popen')
    def test_build_react_project_install_failure(self, mock_popen):
        # Create test package.json
        os.makedirs(self.test_dir, exist_ok=True)
        with open(os.path.join(self.test_dir, 'package.json'), 'w') as f:
            json.dump({'name': 'test-project'}, f)

        # Mock npm install process failure
        install_process = MagicMock()
        install_process.returncode = 1
        install_process.communicate.return_value = (b'', b'npm install error')

        mock_popen.return_value = install_process

        result = self.handler.build_react_project(self.test_dir)
        self.assertFalse(result)

    @patch('subprocess.Popen')
    def test_setup_pm2_success(self, mock_popen):
        # Mock pm2 delete process
        delete_process = MagicMock()
        delete_process.returncode = 0
        delete_process.communicate.return_value = (b'', b'')

        # Mock pm2 start process
        start_process = MagicMock()
        start_process.returncode = 0
        start_process.communicate.return_value = (b'', b'')

        # Mock pm2 save process
        save_process = MagicMock()
        save_process.returncode = 0
        save_process.communicate.return_value = (b'', b'')

        mock_popen.side_effect = [delete_process, start_process, save_process]

        result = self.handler.setup_pm2('test.com', self.test_dir)
        self.assertTrue(result)

    @patch('subprocess.Popen')
    def test_setup_pm2_start_failure(self, mock_popen):
        # Mock pm2 delete process
        delete_process = MagicMock()
        delete_process.returncode = 0
        delete_process.communicate.return_value = (b'', b'')

        # Mock pm2 start process failure
        start_process = MagicMock()
        start_process.returncode = 1
        start_process.communicate.return_value = (b'', b'pm2 start error')

        mock_popen.side_effect = [delete_process, start_process]

        result = self.handler.setup_pm2('test.com', self.test_dir)
        self.assertFalse(result)

    @patch('http.server.HTTPServer')
    def test_run_server(self, mock_http_server):
        mock_server = MagicMock()
        mock_http_server.return_value = mock_server

        # Mock serve_forever to avoid blocking
        mock_server.serve_forever.side_effect = KeyboardInterrupt()

        try:
            run_server(port=8000)
        except KeyboardInterrupt:
            pass

        mock_http_server.assert_called_once_with(('', 8000), DeploymentHandler)
        mock_server.serve_forever.assert_called_once()

    def test_send_json_response(self):
        mock_wfile = MagicMock()
        self.handler.wfile = mock_wfile
        self.handler.send_response = MagicMock()
        self.handler.send_header = MagicMock()
        self.handler.end_headers = MagicMock()

        test_data = {'status': 'success'}
        self.handler.send_json_response(200, test_data)

        self.handler.send_response.assert_called_once_with(200)
        self.handler.send_header.assert_called_once_with('Content-Type', 'application/json')
        self.handler.end_headers.assert_called_once()
        mock_wfile.write.assert_called_once_with(json.dumps(test_data, indent=2).encode('utf-8'))

if __name__ == '__main__':
    unittest.main()
