import unittest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from dynapsys.cli import cli, serve, dns, clone, config_info, get_config

class TestCLI(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_cli_debug_flag(self):
        """Test CLI debug flag"""
        result = self.runner.invoke(cli, ['--debug'])
        self.assertEqual(result.exit_code, 0)

    @patch('dynapsys.cli.run_server')
    def test_serve_command(self, mock_run_server):
        """Test serve command"""
        # Test default options
        result = self.runner.invoke(serve)
        self.assertEqual(result.exit_code, 0)
        mock_run_server.assert_called_once_with(port=8000)

        # Test custom port
        mock_run_server.reset_mock()
        result = self.runner.invoke(serve, ['--port', '9000'])
        self.assertEqual(result.exit_code, 0)
        mock_run_server.assert_called_once_with(port=9000)

        # Test SSL options
        result = self.runner.invoke(serve, [
            '--ssl',
            '--cert', 'cert.pem',
            '--key', 'key.pem'
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('SSL enabled', result.output)

    @patch('dynapsys.cli.update_cloudflare_dns')
    def test_dns_command(self, mock_update_dns):
        """Test DNS command"""
        # Test successful update
        mock_update_dns.return_value = True
        result = self.runner.invoke(dns, ['example.com', 'token123'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('DNS updated successfully', result.output)
        mock_update_dns.assert_called_once_with('example.com', 'token123')

        # Test failed update
        mock_update_dns.return_value = False
        result = self.runner.invoke(dns, ['example.com', 'token123'])
        self.assertEqual(result.exit_code, 1)
        self.assertIn('Failed to update DNS', result.output)

    @patch('dynapsys.cli.is_valid_git_url')
    @patch('dynapsys.cli.clone_git_repo')
    def test_clone_command(self, mock_clone_repo, mock_is_valid_url):
        """Test clone command"""
        # Test successful clone
        mock_is_valid_url.return_value = True
        mock_clone_repo.return_value = True
        result = self.runner.invoke(clone, [
            'https://github.com/user/repo.git',
            '/path/to/target'
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Repository cloned successfully', result.output)
        mock_clone_repo.assert_called_once_with(
            'https://github.com/user/repo.git',
            '/path/to/target'
        )

        # Test invalid URL
        mock_is_valid_url.return_value = False
        result = self.runner.invoke(clone, [
            'invalid-url',
            '/path/to/target'
        ])
        self.assertEqual(result.exit_code, 1)
        self.assertIn('Invalid git URL', result.output)

        # Test failed clone
        mock_is_valid_url.return_value = True
        mock_clone_repo.return_value = False
        result = self.runner.invoke(clone, [
            'https://github.com/user/repo.git',
            '/path/to/target'
        ])
        self.assertEqual(result.exit_code, 1)
        self.assertIn('Failed to clone repository', result.output)

    def test_config_info_command(self):
        """Test config info command"""
        result = self.runner.invoke(config_info)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Current Configuration:', result.output)
        self.assertIn('Log Level:', result.output)
        self.assertIn('Server Port:', result.output)

    def test_get_config_command(self):
        """Test get config command"""
        # Test getting all config values
        result = self.runner.invoke(get_config)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('LOG_LEVEL=', result.output)
        self.assertIn('SERVER_PORT=', result.output)

        # Test getting specific config value
        result = self.runner.invoke(get_config, ['LOG_LEVEL'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('LOG_LEVEL=', result.output)

        # Test getting non-existent config value
        result = self.runner.invoke(get_config, ['NON_EXISTENT'])
        self.assertEqual(result.exit_code, 1)
        self.assertIn('not found', result.output)

    def test_cli_help(self):
        """Test CLI help messages"""
        # Test main help
        result = self.runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Dynamic Python System Deployment Tools', result.output)

        # Test serve command help
        result = self.runner.invoke(serve, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Start the deployment server', result.output)

        # Test dns command help
        result = self.runner.invoke(dns, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Update DNS records in Cloudflare', result.output)

        # Test clone command help
        result = self.runner.invoke(clone, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Clone a git repository', result.output)

if __name__ == '__main__':
    unittest.main()
