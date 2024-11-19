import unittest
from unittest.mock import patch, MagicMock
import json
from dynapsys.dns import update_cloudflare_dns

class TestDNSOperations(unittest.TestCase):
    def setUp(self):
        self.domain = "test.example.com"
        self.cf_token = "test-token"
        self.test_ip = "1.2.3.4"
        self.zone_id = "test-zone-id"
        self.record_id = "test-record-id"

    @patch('subprocess.Popen')
    def test_update_cloudflare_dns_success(self, mock_popen):
        # Mock IP address request
        ip_process_mock = MagicMock()
        ip_process_mock.returncode = 0
        ip_process_mock.communicate.return_value = (self.test_ip.encode(), b'')

        # Mock zone request
        zone_process_mock = MagicMock()
        zone_process_mock.returncode = 0
        zone_response = {
            'success': True,
            'result': [{'id': self.zone_id}]
        }
        zone_process_mock.communicate.return_value = (json.dumps(zone_response).encode(), b'')

        # Mock DNS record request
        record_process_mock = MagicMock()
        record_process_mock.returncode = 0
        record_response = {
            'success': True,
            'result': [{'id': self.record_id}]
        }
        record_process_mock.communicate.return_value = (json.dumps(record_response).encode(), b'')

        # Mock update request
        update_process_mock = MagicMock()
        update_process_mock.returncode = 0
        update_response = {'success': True}
        update_process_mock.communicate.return_value = (json.dumps(update_response).encode(), b'')

        # Configure mock to return different process mocks for different commands
        mock_popen.side_effect = [
            ip_process_mock,
            zone_process_mock,
            record_process_mock,
            update_process_mock
        ]

        # Test the function
        result = update_cloudflare_dns(self.domain, self.cf_token)
        self.assertTrue(result)

    @patch('subprocess.Popen')
    def test_update_cloudflare_dns_ip_failure(self, mock_popen):
        # Mock IP address request failure
        ip_process_mock = MagicMock()
        ip_process_mock.returncode = 1
        ip_process_mock.communicate.return_value = (b'', b'Error getting IP')

        mock_popen.return_value = ip_process_mock

        result = update_cloudflare_dns(self.domain, self.cf_token)
        self.assertFalse(result)

    @patch('subprocess.Popen')
    def test_update_cloudflare_dns_zone_failure(self, mock_popen):
        # Mock IP address request success
        ip_process_mock = MagicMock()
        ip_process_mock.returncode = 0
        ip_process_mock.communicate.return_value = (self.test_ip.encode(), b'')

        # Mock zone request failure
        zone_process_mock = MagicMock()
        zone_process_mock.returncode = 0
        zone_response = {
            'success': False,
            'errors': ['Zone not found']
        }
        zone_process_mock.communicate.return_value = (json.dumps(zone_response).encode(), b'')

        mock_popen.side_effect = [ip_process_mock, zone_process_mock]

        result = update_cloudflare_dns(self.domain, self.cf_token)
        self.assertFalse(result)

    @patch('subprocess.Popen')
    def test_update_cloudflare_dns_create_record(self, mock_popen):
        # Mock IP address request
        ip_process_mock = MagicMock()
        ip_process_mock.returncode = 0
        ip_process_mock.communicate.return_value = (self.test_ip.encode(), b'')

        # Mock zone request
        zone_process_mock = MagicMock()
        zone_process_mock.returncode = 0
        zone_response = {
            'success': True,
            'result': [{'id': self.zone_id}]
        }
        zone_process_mock.communicate.return_value = (json.dumps(zone_response).encode(), b'')

        # Mock DNS record request (no existing record)
        record_process_mock = MagicMock()
        record_process_mock.returncode = 0
        record_response = {
            'success': True,
            'result': []
        }
        record_process_mock.communicate.return_value = (json.dumps(record_response).encode(), b'')

        # Mock create request
        create_process_mock = MagicMock()
        create_process_mock.returncode = 0
        create_response = {'success': True}
        create_process_mock.communicate.return_value = (json.dumps(create_response).encode(), b'')

        mock_popen.side_effect = [
            ip_process_mock,
            zone_process_mock,
            record_process_mock,
            create_process_mock
        ]

        result = update_cloudflare_dns(self.domain, self.cf_token)
        self.assertTrue(result)

    def test_update_cloudflare_dns_invalid_domain(self):
        result = update_cloudflare_dns('', self.cf_token)
        self.assertFalse(result)

        result = update_cloudflare_dns(None, self.cf_token)
        self.assertFalse(result)

    def test_update_cloudflare_dns_invalid_token(self):
        result = update_cloudflare_dns(self.domain, '')
        self.assertFalse(result)

        result = update_cloudflare_dns(self.domain, None)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
