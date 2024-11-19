import unittest
from unittest.mock import patch, MagicMock
import json
import subprocess
from dynapsys.dns import update_cloudflare_dns

class TestDNSOperations(unittest.TestCase):
    def setUp(self):
        self.domain = "test.example.com"
        self.cf_token = "test-token"
        self.test_ip = "1.2.3.4"
        self.zone_id = "test-zone-id"
        self.record_id = "test-record-id"

    def test_invalid_inputs(self):
        """Test DNS update with invalid inputs"""
        test_cases = [
            (None, self.cf_token),
            ('', self.cf_token),
            (self.domain, None),
            (self.domain, ''),
            (None, None),
            ('', ''),
        ]

        for domain, token in test_cases:
            result = update_cloudflare_dns(domain, token)
            self.assertFalse(result, f"Should fail for domain={domain}, token={token}")

    @patch('subprocess.Popen')
    def test_ip_fetch_failure(self, mock_popen):
        """Test handling of IP fetch failure"""
        process_mock = MagicMock()
        process_mock.returncode = 1
        process_mock.communicate.return_value = (b'', b'Failed to get IP')
        mock_popen.return_value = process_mock

        result = update_cloudflare_dns(self.domain, self.cf_token)
        self.assertFalse(result)

    @patch('subprocess.Popen')
    def test_zone_fetch_failure(self, mock_popen):
        """Test handling of zone fetch failure"""
        # Mock successful IP fetch
        ip_process = MagicMock()
        ip_process.returncode = 0
        ip_process.communicate.return_value = (self.test_ip.encode(), b'')

        # Mock failed zone fetch
        zone_process = MagicMock()
        zone_process.returncode = 0
        zone_response = {
            'success': False,
            'errors': ['Zone not found']
        }
        zone_process.communicate.return_value = (json.dumps(zone_response).encode(), b'')

        mock_popen.side_effect = [ip_process, zone_process]

        result = update_cloudflare_dns(self.domain, self.cf_token)
        self.assertFalse(result)

    @patch('subprocess.Popen')
    def test_zone_empty_result(self, mock_popen):
        """Test handling of empty zone result"""
        # Mock successful IP fetch
        ip_process = MagicMock()
        ip_process.returncode = 0
        ip_process.communicate.return_value = (self.test_ip.encode(), b'')

        # Mock zone fetch with empty result
        zone_process = MagicMock()
        zone_process.returncode = 0
        zone_response = {
            'success': True,
            'result': []
        }
        zone_process.communicate.return_value = (json.dumps(zone_response).encode(), b'')

        mock_popen.side_effect = [ip_process, zone_process]

        result = update_cloudflare_dns(self.domain, self.cf_token)
        self.assertFalse(result)

    @patch('subprocess.Popen')
    def test_record_creation_success(self, mock_popen):
        """Test successful DNS record creation"""
        # Mock successful IP fetch
        ip_process = MagicMock()
        ip_process.returncode = 0
        ip_process.communicate.return_value = (self.test_ip.encode(), b'')

        # Mock successful zone fetch
        zone_process = MagicMock()
        zone_process.returncode = 0
        zone_response = {
            'success': True,
            'result': [{'id': self.zone_id}]
        }
        zone_process.communicate.return_value = (json.dumps(zone_response).encode(), b'')

        # Mock empty record fetch (no existing record)
        record_process = MagicMock()
        record_process.returncode = 0
        record_response = {
            'success': True,
            'result': []
        }
        record_process.communicate.return_value = (json.dumps(record_response).encode(), b'')

        # Mock successful record creation
        create_process = MagicMock()
        create_process.returncode = 0
        create_response = {
            'success': True,
            'result': {'id': self.record_id}
        }
        create_process.communicate.return_value = (json.dumps(create_response).encode(), b'')

        mock_popen.side_effect = [ip_process, zone_process, record_process, create_process]

        result = update_cloudflare_dns(self.domain, self.cf_token)
        self.assertTrue(result)

    @patch('subprocess.Popen')
    def test_record_update_success(self, mock_popen):
        """Test successful DNS record update"""
        # Mock successful IP fetch
        ip_process = MagicMock()
        ip_process.returncode = 0
        ip_process.communicate.return_value = (self.test_ip.encode(), b'')

        # Mock successful zone fetch
        zone_process = MagicMock()
        zone_process.returncode = 0
        zone_response = {
            'success': True,
            'result': [{'id': self.zone_id}]
        }
        zone_process.communicate.return_value = (json.dumps(zone_response).encode(), b'')

        # Mock existing record fetch
        record_process = MagicMock()
        record_process.returncode = 0
        record_response = {
            'success': True,
            'result': [{'id': self.record_id}]
        }
        record_process.communicate.return_value = (json.dumps(record_response).encode(), b'')

        # Mock successful record update
        update_process = MagicMock()
        update_process.returncode = 0
        update_response = {
            'success': True,
            'result': {'id': self.record_id}
        }
        update_process.communicate.return_value = (json.dumps(update_response).encode(), b'')

        mock_popen.side_effect = [ip_process, zone_process, record_process, update_process]

        result = update_cloudflare_dns(self.domain, self.cf_token)
        self.assertTrue(result)

    @patch('subprocess.Popen')
    def test_invalid_json_response(self, mock_popen):
        """Test handling of invalid JSON responses"""
        # Mock successful IP fetch
        ip_process = MagicMock()
        ip_process.returncode = 0
        ip_process.communicate.return_value = (self.test_ip.encode(), b'')

        # Mock invalid JSON response
        zone_process = MagicMock()
        zone_process.returncode = 0
        zone_process.communicate.return_value = (b'invalid json', b'')

        mock_popen.side_effect = [ip_process, zone_process]

        result = update_cloudflare_dns(self.domain, self.cf_token)
        self.assertFalse(result)

    @patch('subprocess.Popen')
    def test_subprocess_exception(self, mock_popen):
        """Test handling of subprocess exceptions"""
        mock_popen.side_effect = subprocess.SubprocessError("Test error")

        result = update_cloudflare_dns(self.domain, self.cf_token)
        self.assertFalse(result)

    @patch('subprocess.Popen')
    def test_subdomain_handling(self, mock_popen):
        """Test handling of subdomains"""
        subdomain = "sub.test.example.com"
        
        # Mock successful IP fetch
        ip_process = MagicMock()
        ip_process.returncode = 0
        ip_process.communicate.return_value = (self.test_ip.encode(), b'')

        # Mock successful zone fetch
        zone_process = MagicMock()
        zone_process.returncode = 0
        zone_response = {
            'success': True,
            'result': [{'id': self.zone_id}]
        }
        zone_process.communicate.return_value = (json.dumps(zone_response).encode(), b'')

        # Mock record fetch
        record_process = MagicMock()
        record_process.returncode = 0
        record_response = {
            'success': True,
            'result': []
        }
        record_process.communicate.return_value = (json.dumps(record_response).encode(), b'')

        # Mock successful record creation
        create_process = MagicMock()
        create_process.returncode = 0
        create_response = {
            'success': True,
            'result': {'id': self.record_id}
        }
        create_process.communicate.return_value = (json.dumps(create_response).encode(), b'')

        mock_popen.side_effect = [ip_process, zone_process, record_process, create_process]

        result = update_cloudflare_dns(subdomain, self.cf_token)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
