"""Configuration management for DynaPsys"""
import os
from pathlib import Path
from typing import Dict, Any
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Configuration class for DynaPsys"""
    
    # Default values
    DEFAULTS = {
        'LOG_LEVEL': 'DEBUG',
        'LOG_FILE': 'deployment.log',
        'SITES_DIR': '/opt/reactjs/sites',
        'SERVER_HOST': '',
        'SERVER_PORT': 8000,
        'CLOUDFLARE_API_URL': 'https://api.cloudflare.com/client/v4',
        'PM2_SAVE_ON_EXIT': True,
        'ENABLE_SSL': False,
        'SSL_CERT_FILE': '',
        'SSL_KEY_FILE': '',
    }

    def __init__(self):
        """Initialize configuration with environment variables or defaults"""
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from environment variables or use defaults"""
        for key, default in self.DEFAULTS.items():
            env_key = f'DYNAPSYS_{key}'
            env_value = os.getenv(env_key)

            if env_value is not None:
                # Convert string values to appropriate types
                if isinstance(default, bool):
                    self._config[key] = env_value.lower() in ('true', '1', 'yes')
                elif isinstance(default, int):
                    try:
                        self._config[key] = int(env_value)
                    except ValueError:
                        logging.warning(f"Invalid integer value for {env_key}: {env_value}")
                        self._config[key] = default
                else:
                    self._config[key] = env_value
            else:
                self._config[key] = default

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        directories = [
            self.sites_dir,
            os.path.dirname(self.log_file)
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    @property
    def log_level(self) -> str:
        """Get logging level"""
        return self._config['LOG_LEVEL']

    @property
    def log_file(self) -> str:
        """Get log file path"""
        return self._config['LOG_FILE']

    @property
    def sites_dir(self) -> str:
        """Get sites directory path"""
        return self._config['SITES_DIR']

    @property
    def server_host(self) -> str:
        """Get server host"""
        return self._config['SERVER_HOST']

    @property
    def server_port(self) -> int:
        """Get server port"""
        return self._config['SERVER_PORT']

    @property
    def cloudflare_api_url(self) -> str:
        """Get Cloudflare API URL"""
        return self._config['CLOUDFLARE_API_URL']

    @property
    def pm2_save_on_exit(self) -> bool:
        """Get PM2 save on exit setting"""
        return self._config['PM2_SAVE_ON_EXIT']

    @property
    def enable_ssl(self) -> bool:
        """Get SSL enable setting"""
        return self._config['ENABLE_SSL']

    @property
    def ssl_cert_file(self) -> str:
        """Get SSL certificate file path"""
        return self._config['SSL_CERT_FILE']

    @property
    def ssl_key_file(self) -> str:
        """Get SSL key file path"""
        return self._config['SSL_KEY_FILE']

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self._config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Get configuration value by key using dictionary syntax"""
        return self._config[key]

    def __str__(self) -> str:
        """String representation of configuration"""
        return f"DynaPsys Config: {self._config}"

# Create global configuration instance
config = Config()
