import unittest
import os
import shutil
import tempfile
from dynapsys.git import is_valid_git_url, clone_git_repo, check_git_installation

class TestGitOperations(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_valid_git_urls(self):
        valid_urls = [
            'https://github.com/user/repo.git',
            'https://github.com/user/repo',
            'git@github.com:user/repo.git',
            'https://gitlab.com/user/repo.git',
            'https://bitbucket.org/user/repo.git'
        ]
        for url in valid_urls:
            self.assertTrue(is_valid_git_url(url), f"URL should be valid: {url}")

    def test_invalid_git_urls(self):
        invalid_urls = [
            'http://invalid-domain.com/repo.git',
            'https://github.com/invalid/repo/extra',
            'not-a-url',
            'git@gitlab.com:user/repo.git',  # Only GitHub SSH URLs are supported
            ''
        ]
        for url in invalid_urls:
            self.assertFalse(is_valid_git_url(url), f"URL should be invalid: {url}")

    def test_git_installation(self):
        self.assertTrue(check_git_installation(), "Git should be installed")

    def test_clone_git_repo(self):
        test_repo = "https://github.com/user/test-repo.git"
        target_dir = os.path.join(self.test_dir, "test-repo")
        
        # Test with invalid repository
        self.assertFalse(clone_git_repo(test_repo, target_dir))
        self.assertFalse(os.path.exists(target_dir))

        # Test with valid repository (would need a real repository URL)
        # self.assertTrue(clone_git_repo("https://github.com/real/repo.git", target_dir))
        # self.assertTrue(os.path.exists(target_dir))
        # self.assertTrue(os.path.exists(os.path.join(target_dir, ".git")))

if __name__ == '__main__':
    unittest.main()
