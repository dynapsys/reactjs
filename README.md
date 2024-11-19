# DynaPsys

DynaPsys is a comprehensive Python package for automated deployment and management of web applications, with a focus on React applications. It provides tools for deployment automation, DNS management through Cloudflare, and process management using PM2.

## Features

- Automated deployment server for web applications
- Cloudflare DNS management integration
- Git repository support
- PM2 process management
- Base64 deployment support
- Comprehensive logging system

## Installation

```bash
pip install dynapsys
```

## Usage

### Starting the Deployment Server

```python
from dynapsys.deployment import run_server

# Start the server on port 8000 (default)
run_server()

# Or specify a custom port
run_server(port=8080)
```

### Deploying an Application

Send a POST request to the deployment server:

```bash
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "your-domain.com",
    "cf_token": "your-cloudflare-token",
    "source": "https://github.com/username/repo.git"
  }'
```

### Using Individual Components

#### Git Operations

```python
from dynapsys.git import clone_git_repo, is_valid_git_url

# Validate Git URL
if is_valid_git_url("https://github.com/username/repo.git"):
    # Clone repository
    clone_git_repo("https://github.com/username/repo.git", "/path/to/target")
```

#### DNS Management

```python
from dynapsys.dns import update_cloudflare_dns

# Update DNS records
update_cloudflare_dns("your-domain.com", "your-cloudflare-token")
```

## Requirements

- Python 3.6+
- Git
- Node.js and npm (for React applications)
- PM2 (for process management)
- Cloudflare API token (for DNS management)

## Configuration

The package uses environment variables for configuration:

- `DYNAPSYS_LOG_LEVEL`: Logging level (default: DEBUG)
- `DYNAPSYS_LOG_FILE`: Path to log file (default: deployment.log)
- `DYNAPSYS_SITES_DIR`: Directory for deployed sites (default: /opt/reactjs/sites)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the Apache 2 License - see the LICENSE file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes.

## Todo

See [TODO.md](TODO.md) for planned features and improvements.
