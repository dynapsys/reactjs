import unittest
from deployment_server import DeploymentHandler

class TestDeploymentHandler(unittest.TestCase):
    def setUp(self):
        self.handler = DeploymentHandler()

if __name__ == '__main__':
    unittest.main()
