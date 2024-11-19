import unittest
from unittest.mock import patch, MagicMock, call
import json
import os
import tempfile
import shutil
import base64
from http.server import HTTPServer
from dynapsys.deployment import DeploymentHandler, run_server

class TestDeploymentHandler(unittest.TestCase):
    def setUp(self):
        self.handler = DeploymentHandler(None, None, None)
        self.test_dir = tempfile.mkdtemp()
        self.handler.wfile = MagicMock()
        self.handler.send_response = MagicMock()
        self.handler.send_header = MagicMock()
        self.handler.end_headers = MagicMock()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_check_git_installation(self):
        """Test git installation check"""
        self.assertTrue(self.handler.check_git_installation())

        with patch('subprocess.check_output', side_effect=FileNotFoundError):
            self.assertFalse(self.handler.check_git_installation())

        with patch('subprocess.check_output', side_effect=subprocess.CalledProcessError(1, 'git')):
            self.assertFalse(self.handler.check_git_installation())

    @patch('subprocess.Popen')
    def test_build_react_project_success(self, mock_popen):
        """Test successful React project build"""
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
        self.assertEqual(mock_popen.call_count, 2)

    def test_build_react_project_missing_package_json(self):
        """Test build with missing package.json"""
        result = self.handler.build_react_project(self.test_dir)
        self.assertFalse(result)

    @patch('subprocess.Popen')
    def test_build_react_project_npm_install_failure(self, mock_popen):
        """Test build with npm install failure"""
        os.makedirs(self.test_dir, exist_ok=True)
        with open(os.path.join(self.test_dir, 'package.json'), 'w') as f:
            json.dump({'name': 'test-project'}, f)

        process = MagicMock()
        process.returncode = 1
        process.communicate.return_value = (b'', b'npm install error')
        mock_popen.return_value = process

        result = self.handler.build_react_project(self.test_dir)
        self.assertFalse(result)

    @patch('subprocess.Popen')
    def test_setup_pm2_success(self, mock_popen):
        """Test successful PM2 setup"""
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
        self.assertEqual(mock_popen.call_count, 3)

    def test_send_json_response(self):
        """Test JSON response sending"""
        test_cases = [
            (200, {'status': 'success'}),
            (400, {'error': 'Bad request'}),
            (500, {'error': 'Server error', 'details': 'Test error'})
        ]

        for status_code, data in test_cases:
            self.handler.send_json_response(status_code, data)
            self.handler.send_response.assert_called_with(status_code)
            self.handler.send_header.assert_called_with('Content-Type', 'application/json')
            self.handler.end_headers.assert_called()
            self.handler.wfile.write.assert_called_with(
                json.dumps(data, indent=2).encode('utf-8')
            )

    def test_do_POST_empty_request(self):
        """Test POST request with empty content"""
        self.handler.headers = MagicMock()
        self.handler.headers.get.return_value = '0'
        self.handler.rfile = MagicMock()
        self.handler.rfile.read.return_value = b''

        self.handler.do_POST()
        
        self.handler.send_json_response.assert_called_with(
            400, {"error": "Empty request"}
        )

    def test_do_POST_invalid_json(self):
        """Test POST request with invalid JSON"""
        self.handler.headers = MagicMock()
        self.handler.headers.get.return_value = '10'
        self.handler.rfile = MagicMock()
        self.handler.rfile.read.return_value = b'invalid json'

        self.handler.do_POST()
        
        self.assertTrue(any(
            call(400, {"error": msg}) == c 
            for c in self.handler.send_json_response.call_args_list
            for msg in c[0][1].values()
            if "Invalid JSON" in msg
        ))

    def test_do_POST_missing_fields(self):
        """Test POST request with missing required fields"""
        self.handler.headers = MagicMock()
        self.handler.headers.get.return_value = '50'
        self.handler.rfile = MagicMock()
        
        test_cases = [
            {},
            {'domain': 'test.com'},
            {'domain': 'test.com', 'cf_token': 'token'},
            {'cf_token': 'token', 'source': 'source'},
        ]

        for data in test_cases:
            self.handler.rfile.read.return_value = json.dumps(data).encode()
            self.handler.do_POST()
            self.handler.send_json_response.assert_called_with(
                400, {"error": "Missing required fields"}
            )

    @patch('http.server.HTTPServer')
    def test_run_server(self, mock_http_server):
        """Test server running"""
        mock_server = MagicMock()
        mock_http_server.return_value = mock_server

        # Test normal start
        run_server(port=8000)
        mock_http_server.assert_called_once_with(('', 8000), DeploymentHandler)
        mock_server.serve_forever.assert_called_once()

        # Test with server error
        mock_http_server.side_effect = Exception("Test error")
        with self.assertRaises(SystemExit):
            run_server(port=8000)

    def test_base64_deployment(self):
        """Test deployment from base64 data"""
        # Create test tar.gz content
        test_content = b"test content"
        base64_content = base64.b64encode(test_content).decode()
        source = f"data:application/tar+gz;base64,{base64_content}"

        self.handler.headers = MagicMock()
        self.handler.headers.get.return_value = str(len(json.dumps({
            'domain': 'test.com',
            'cf_token': 'token',
            'source': source
        }).encode()))
        
        self.handler.rfile = MagicMock()
        self.handler.rfile.read.return_value = json.dumps({
            'domain': 'test.com',
            'cf_token': 'token',
            'source': source
        }).encode()

        with patch('tempfile.TemporaryDirectory') as mock_temp_dir:
            mock_temp_dir.return_value.__enter__.return_value = self.test_dir
            self.handler.do_POST()

if __name__ == '__main__':
    unittest.main()
