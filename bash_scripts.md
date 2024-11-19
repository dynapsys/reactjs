# Bash Scripts Documentation

This document describes the functionality of all bash scripts in the project.

## cloudflare.sh
A script for managing Cloudflare DNS configuration.

### Functions:
- Validates Cloudflare API token and domain
- Checks Zone ID for the domain
- Verifies DNS records
- Checks proxy status
- Provides detailed status report and suggestions

### Usage:
```bash
./cloudflare.sh <domain> <cloudflare_token>
```

## deploy-git.sh
A testing script for the deployment server.

### Functions:
- Tests deployment server on localhost:8000
- Performs multiple validation tests:
  1. Basic connection test using CURL
  2. Full deployment request test
  3. Port 8000 availability check
  4. Python process verification
  5. ReactJS service status check
  6. Log file inspection
  7. Firewall rules verification

### Usage:
```bash
./deploy-git.sh
```

## deploy-zip.sh
A script for deploying projects using ZIP archives.

### Functions:
- Validates input parameters
- Packages project directory into base64-encoded tar.gz
- Sends deployment request to deployment server

### Usage:
```bash
./deploy-zip.sh <project-path> <domain> <cloudflare-token>
```

## domain.sh
A comprehensive script for setting up domain configuration and deployment infrastructure.

### Functions:
1. Caddy Server Configuration:
   - Sets up reverse proxy for reactjs.dynapsys.com
   - Configures security headers
   - Sets up logging
   - Enables GZIP compression

2. Deployment Script Setup:
   - Creates deployment script with following capabilities:
     - Git repository cloning
     - Local file copying
     - NPM dependencies installation
     - React application building
     - Cloudflare DNS configuration
     - PM2 process management

### Key Features:
- Automatic Cloudflare DNS record management
- PM2 process management integration
- Secure headers configuration
- Logging setup
- Environment configuration

### Usage:
The script is typically run once during initial setup:
```bash
./domain.sh
```

## Additional Scripts:

### test_caddy.sh
- Tests Caddy server configuration
- Verifies server responses
- Checks SSL/TLS setup

### test_python.sh
- Validates Python environment
- Checks script permissions
- Verifies Python dependencies

### test_services.sh
- Checks status of all services
- Validates service configurations
- Monitors service logs

### fix_config.sh
- Repairs configuration issues
- Resets permissions where needed
- Validates configuration files

### git.sh
- Handles Git operations
- Manages repository cloning
- Validates Git URLs

### install.sh
- Manages installation of dependencies
- Sets up required permissions
- Configures initial system setup

### php_install.sh
- Configures PHP environment
- Sets up PHP-FPM
- Manages PHP dependencies

### status.sh
- Provides system status overview
- Checks all service states
- Displays relevant logs

## Common Features Across Scripts:
- Error handling and validation
- Logging functionality
- Permission management
- Security considerations
- Service status checking
- Configuration validation

## Best Practices Implemented:
1. Input validation
2. Error handling
3. Logging
4. Security headers
5. Permission management
6. Service monitoring
7. Configuration backup
8. Clean error messages
9. Status reporting
10. Documentation within scripts
