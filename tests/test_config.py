import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from dynapsys.config import Config

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Clear any existing environment variables
        for key in os.environ.keys():
            if key.startswith('DYNAPSYS_'):
                del os.environ[key]
        
        self.temp_dir = tempfile.mkdtemp()

    def test_default_values(self):
        """Test that default values are set correctly"""
        config = Config()
        
        self.assertEqual(config.log_level, 'DEBUG')
        self.assertEqual(config.server_port, 8000)
        self.assertEqual(config.sites_dir, '/opt/reactjs/sites')
        self.assertFalse(config.enable_ssl)
        self.assertTrue(config.pm2_save_on_exit)

    def test_environment_override(self):
        """Test that environment variables override defaults"""
        os.environ['DYNAPSYS_LOG_LEVEL'] = 'INFO'
        os.environ['DYNAPSYS_SERVER_PORT'] = '9000'
        os.environ['DYNAPSYS_SITES_DIR'] = '/custom/path'
        os.environ['DYNAPSYS_ENABLE_SSL'] = 'true'
        os.environ['DYNAPSYS_PM2_SAVE_ON_EXIT'] = 'false'

        config = Config()

        self.assertEqual(config.log_level, 'INFO')
        self.assertEqual(config.server_port, 9000)
        self.assertEqual(config.sites_dir, '/custom/path')
        self.assertTrue(config.enable_ssl)
        self.assertFalse(config.pm2_save_on_exit)

    def test_invalid_port_value(self):
        """Test handling of invalid integer values"""
        os.environ['DYNAPSYS_SERVER_PORT'] = 'invalid'
        config = Config()
        self.assertEqual(config.server_port, 8000)  # Should use default

    def test_boolean_conversion(self):
        """Test boolean value conversion from environment variables"""
        test_cases = [
            ('true', True),
            ('True', True),
            ('1', True),
            ('yes', True),
            ('false', False),
            ('False', False),
            ('0', False),
            ('no', False),
        ]

        for env_value, expected in test_cases:
            os.environ['DYNAPSYS_ENABLE_SSL'] = env_value
            config = Config()
            self.assertEqual(config.enable_ssl, expected)

    def test_directory_creation(self):
        """Test that required directories are created"""
        test_path = os.path.join(self.temp_dir, 'test_sites')
        os.environ['DYNAPSYS_SITES_DIR'] = test_path
        os.environ['DYNAPSYS_LOG_FILE'] = os.path.join(self.temp_dir, 'logs/test.log')

        config = Config()
        
        self.assertTrue(os.path.exists(test_path))
        self.assertTrue(os.path.exists(os.path.dirname(config.log_file)))

    def test_get_method(self):
        """Test the get method with default values"""
        config = Config()
        
        # Test existing key
        self.assertEqual(config.get('LOG_LEVEL'), 'DEBUG')
        
        # Test non-existing key with default
        self.assertEqual(config.get('NON_EXISTING', 'default'), 'default')
        
        # Test non-existing key without default
        self.assertIsNone(config.get('NON_EXISTING'))

    def test_dictionary_access(self):
        """Test dictionary-style access to configuration"""
        config = Config()
        
        self.assertEqual(config['LOG_LEVEL'], 'DEBUG')
        
        with self.assertRaises(KeyError):
            _ = config['NON_EXISTING']

    def test_string_representation(self):
        """Test string representation of configuration"""
        config = Config()
        string_repr = str(config)
        
        self.assertIn('DynaPsys Config:', string_repr)
        self.assertIn('LOG_LEVEL', string_repr)
        self.assertIn('SERVER_PORT', string_repr)

    @patch('pathlib.Path.mkdir')
    def test_directory_creation_error(self, mock_mkdir):
        """Test handling of directory creation errors"""
        mock_mkdir.side_effect = PermissionError()
        
        # Should not raise an exception
        config = Config()
        self.assertIsNotNone(config)

    def test_cloudflare_api_url(self):
        """Test Cloudflare API URL configuration"""
        custom_url = 'https://custom.cloudflare.api'
        os.environ['DYNAPSYS_CLOUDFLARE_API_URL'] = custom_url
        
        config = Config()
        self.assertEqual(config.cloudflare_api_url, custom_url)

    def test_ssl_configuration(self):
        """Test SSL configuration settings"""
        os.environ['DYNAPSYS_ENABLE_SSL'] = 'true'
        os.environ['DYNAPSYS_SSL_CERT_FILE'] = '/path/to/cert.pem'
        os.environ['DYNAPSYS_SSL_KEY_FILE'] = '/path/to/key.pem'

        config = Config()
        
        self.assertTrue(config.enable_ssl)
        self.assertEqual(config.ssl_cert_file, '/path/to/cert.pem')
        self.assertEqual(config.ssl_key_file, '/path/to/key.pem')

if __name__ == '__main__':
    unittest.main()
