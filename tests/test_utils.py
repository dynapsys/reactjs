import unittest
import os
import json
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
from dynapsys.utils import (
    ensure_directory,
    run_command,
    load_json_file,
    save_json_file,
    is_port_in_use,
    get_free_port,
    get_system_info,
    format_size,
    is_valid_domain,
    setup_logging
)

class TestUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, 'test.json')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_ensure_directory(self):
        """Test directory creation and permission checking"""
        test_path = os.path.join(self.temp_dir, 'test_dir')
        
        # Test creating new directory
        self.assertTrue(ensure_directory(test_path))
        self.assertTrue(os.path.exists(test_path))
        self.assertTrue(os.access(test_path, os.W_OK))

        # Test existing directory
        self.assertTrue(ensure_directory(test_path))

        # Test permission error
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError()
            self.assertFalse(ensure_directory('/root/test'))

    @patch('subprocess.Popen')
    def test_run_command(self, mock_popen):
        """Test command execution"""
        # Test successful command
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.communicate.return_value = ('output', 'error')
        mock_popen.return_value = process_mock

        code, stdout, stderr = run_command(['echo', 'test'])
        self.assertEqual(code, 0)
        self.assertEqual(stdout, 'output')
        self.assertEqual(stderr, 'error')

        # Test command timeout
        process_mock.communicate.side_effect = subprocess.TimeoutExpired(['test'], 1)
        code, stdout, stderr = run_command(['test'], timeout=1)
        self.assertEqual(code, -1)
        self.assertEqual(stdout, '')
        self.assertIn('timeout', stderr.lower())

        # Test command failure
        process_mock.communicate.side_effect = Exception('Command failed')
        code, stdout, stderr = run_command(['test'])
        self.assertEqual(code, -1)
        self.assertEqual(stdout, '')
        self.assertIn('failed', stderr.lower())

    def test_json_file_operations(self):
        """Test JSON file operations"""
        test_data = {'key': 'value', 'number': 42}

        # Test saving JSON
        self.assertTrue(save_json_file(self.test_file, test_data))
        self.assertTrue(os.path.exists(self.test_file))

        # Test loading JSON
        loaded_data = load_json_file(self.test_file)
        self.assertEqual(loaded_data, test_data)

        # Test loading invalid JSON
        with open(self.test_file, 'w') as f:
            f.write('invalid json')
        self.assertIsNone(load_json_file(self.test_file))

        # Test loading non-existent file
        self.assertIsNone(load_json_file('nonexistent.json'))

    @patch('socket.socket')
    def test_port_checks(self, mock_socket):
        """Test port availability checking"""
        # Test port in use
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_socket.return_value.__enter__.return_value = mock_sock
        self.assertTrue(is_port_in_use(8000))

        # Test port free
        mock_sock.connect_ex.return_value = 1
        self.assertFalse(is_port_in_use(8000))

        # Test get_free_port
        mock_sock.connect_ex.side_effect = [1]  # First port is free
        self.assertEqual(get_free_port(8000, 8001), 8000)

        # Test no free ports
        mock_sock.connect_ex.side_effect = [0, 0]  # All ports in use
        self.assertIsNone(get_free_port(8000, 8001))

    @patch('platform.system', return_value='Linux')
    @patch('platform.release', return_value='5.4.0')
    @patch('platform.python_version', return_value='3.8.0')
    def test_system_info(self, *mocks):
        """Test system information gathering"""
        info = get_system_info()
        self.assertEqual(info['os'], 'Linux')
        self.assertEqual(info['os_release'], '5.4.0')
        self.assertEqual(info['python_version'], '3.8.0')

    def test_format_size(self):
        """Test file size formatting"""
        test_cases = [
            (500, '500.0B'),
            (1024, '1.0KB'),
            (1024 * 1024, '1.0MB'),
            (1024 * 1024 * 1024, '1.0GB'),
            (1024 * 1024 * 1024 * 1024, '1.0TB'),
        ]
        for size, expected in test_cases:
            self.assertEqual(format_size(size), expected)

    def test_domain_validation(self):
        """Test domain name validation"""
        valid_domains = [
            'example.com',
            'sub.example.com',
            'sub-domain.example.com',
            'example.co.uk',
        ]
        for domain in valid_domains:
            self.assertTrue(is_valid_domain(domain))

        invalid_domains = [
            'invalid',
            'invalid.',
            '.invalid',
            'inv@lid.com',
            '-invalid.com',
            'invalid-.com',
            'invalid..com',
        ]
        for domain in invalid_domains:
            self.assertFalse(is_valid_domain(domain))

    def test_setup_logging(self):
        """Test logging setup"""
        log_file = os.path.join(self.temp_dir, 'logs', 'test.log')

        # Test with file handler
        setup_logging(level='DEBUG', log_file=log_file)
        self.assertTrue(os.path.exists(os.path.dirname(log_file)))
        
        # Test logging
        test_message = 'Test log message'
        logging.info(test_message)
        
        with open(log_file, 'r') as f:
            log_content = f.read()
            self.assertIn(test_message, log_content)

        # Test without file handler
        setup_logging(level='INFO')
        logging.info(test_message)  # Should not raise any errors

if __name__ == '__main__':
    unittest.main()
