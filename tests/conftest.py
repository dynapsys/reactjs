import pytest
import os
import tempfile
import shutil
import logging

@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    test_dir = tempfile.mkdtemp()
    yield test_dir
    shutil.rmtree(test_dir)

@pytest.fixture
def mock_git_repo(temp_dir):
    """Create a mock git repository structure"""
    repo_dir = os.path.join(temp_dir, 'test-repo')
    os.makedirs(repo_dir)
    os.makedirs(os.path.join(repo_dir, '.git'))
    with open(os.path.join(repo_dir, 'package.json'), 'w') as f:
        f.write('{"name": "test-project"}')
    return repo_dir

@pytest.fixture
def mock_cloudflare_response():
    """Mock Cloudflare API response"""
    return {
        'success': True,
        'result': [{
            'id': 'test-zone-id',
            'name': 'example.com',
            'status': 'active'
        }]
    }

@pytest.fixture
def mock_deployment_request():
    """Mock deployment request data"""
    return {
        'domain': 'test.example.com',
        'cf_token': 'test-token',
        'source': 'https://github.com/test/repo.git'
    }
