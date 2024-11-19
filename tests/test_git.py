import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil
import subprocess
from dynapsys.git import clone_git_repo, is_valid_git_url, check_git_installation

class TestGitOperations(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.valid_urls = [
            'https://github.com/user/repo.git',
            'https://github.com/user/repo',
            'git@github.com:user/repo.git',
            'https://gitlab.com/user/repo.git',
            'https://bitbucket.org/user/repo.git'
        ]
        self.invalid_urls = [
            'http://invalid-domain.com/repo.git',
            'https://github.com/invalid/repo/extra',
            'not-a-url',
            'git@gitlab.com:user/repo.git',  # Only GitHub SSH URLs are supported
            '',
            None,
            'https://github.com/',
            'https://github.com/user',
            'git@github.com:user',
            'https://bitbucket.org/user/',
            'ftp://github.com/user/repo.git'
        ]

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_valid_git_urls(self):
        """Test validation of valid Git URLs"""
        for url in self.valid_urls:
            self.assertTrue(
                is_valid_git_url(url), 
                f"URL should be valid: {url}"
            )

    def test_invalid_git_urls(self):
        """Test validation of invalid Git URLs"""
        for url in self.invalid_urls:
            self.assertFalse(
                is_valid_git_url(url), 
                f"URL should be invalid: {url}"
            )

    def test_git_installation(self):
        """Test Git installation check"""
        # Test successful check
        with patch('subprocess.check_output') as mock_check:
            mock_check.return_value = b'git version 2.34.1'
            self.assertTrue(check_git_installation())

        # Test git not found
        with patch('subprocess.check_output', side_effect=FileNotFoundError):
            self.assertFalse(check_git_installation())

        # Test git command error
        with patch('subprocess.check_output', 
                  side_effect=subprocess.CalledProcessError(1, 'git')):
            self.assertFalse(check_git_installation())

    @patch('subprocess.Popen')
    def test_clone_git_repo_success(self, mock_popen):
        """Test successful Git repository cloning"""
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.stdout.readline.side_effect = ['Cloning...', '', '']
        process_mock.communicate.return_value = ('', '')
        process_mock.poll.return_value = 0
        mock_popen.return_value = process_mock

        # Create a mock .git directory to simulate successful clone
        os.makedirs(os.path.join(self.test_dir, '.git'))

        result = clone_git_repo('https://github.com/user/repo.git', self.test_dir)
        self.assertTrue(result)

    def test_clone_git_repo_invalid_url(self):
        """Test cloning with invalid Git URL"""
        for url in self.invalid_urls:
            if url is not None:  # Skip None as it would raise TypeError
                result = clone_git_repo(url, self.test_dir)
                self.assertFalse(result, f"Should fail for invalid URL: {url}")

    @patch('subprocess.Popen')
    def test_clone_git_repo_command_failure(self, mock_popen):
        """Test handling of Git clone command failure"""
        process_mock = MagicMock()
        process_mock.returncode = 1
        process_mock.stdout.readline.side_effect = ['', '']
        process_mock.communicate.return_value = ('', 'fatal: repository not found')
        process_mock.poll.return_value = 1
        mock_popen.return_value = process_mock

        result = clone_git_repo('https://github.com/user/repo.git', self.test_dir)
        self.assertFalse(result)

    def test_clone_git_repo_permission_error(self):
        """Test handling of permission errors"""
        with patch('os.access', return_value=False):
            result = clone_git_repo(
                'https://github.com/user/repo.git',
                '/root/test'
            )
            self.assertFalse(result)

    @patch('subprocess.Popen')
    def test_clone_git_repo_empty_result(self, mock_popen):
        """Test handling of successful clone but empty repository"""
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.stdout.readline.side_effect = ['', '']
        process_mock.communicate.return_value = ('', '')
        process_mock.poll.return_value = 0
        mock_popen.return_value = process_mock

        result = clone_git_repo('https://github.com/user/repo.git', self.test_dir)
        self.assertFalse(result)

    @patch('subprocess.Popen')
    def test_clone_git_repo_existing_directory(self, mock_popen):
        """Test cloning when target directory exists"""
        # Create some existing content
        os.makedirs(os.path.join(self.test_dir, 'existing'))
        with open(os.path.join(self.test_dir, 'existing/file.txt'), 'w') as f:
            f.write('test')

        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.stdout.readline.side_effect = ['Cloning...', '', '']
        process_mock.communicate.return_value = ('', '')
        process_mock.poll.return_value = 0
        mock_popen.return_value = process_mock

        # Create a mock .git directory to simulate successful clone
        os.makedirs(os.path.join(self.test_dir, '.git'))

        result = clone_git_repo('https://github.com/user/repo.git', self.test_dir)
        self.assertTrue(result)
        # Verify directory was cleaned before clone
        self.assertFalse(
            os.path.exists(os.path.join(self.test_dir, 'existing')),
            "Existing directory should be removed before clone"
        )

    def test_clone_git_repo_parent_directory_creation(self):
        """Test creation of parent directories during clone"""
        nested_dir = os.path.join(self.test_dir, 'nested', 'path', 'repo')
        
        with patch('subprocess.Popen') as mock_popen:
            process_mock = MagicMock()
            process_mock.returncode = 0
            process_mock.stdout.readline.side_effect = ['Cloning...', '', '']
            process_mock.communicate.return_value = ('', '')
            process_mock.poll.return_value = 0
            mock_popen.return_value = process_mock

            # Create a mock .git directory to simulate successful clone
            os.makedirs(os.path.join(nested_dir, '.git'))

            result = clone_git_repo(
                'https://github.com/user/repo.git',
                nested_dir
            )
            self.assertTrue(result)
            self.assertTrue(
                os.path.exists(os.path.dirname(nested_dir)),
                "Parent directories should be created"
            )

    @patch('subprocess.Popen')
    def test_clone_git_repo_subprocess_exception(self, mock_popen):
        """Test handling of subprocess exceptions"""
        mock_popen.side_effect = subprocess.SubprocessError("Test error")

        result = clone_git_repo('https://github.com/user/repo.git', self.test_dir)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
