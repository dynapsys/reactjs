# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-11-20

### Added
- New configuration management system with environment variable support
- Command-line interface (CLI) for all major operations
- Comprehensive utility functions module
- Type hints throughout the codebase
- Proper Python packaging setup with setuptools
- Development tools configuration (black, isort, pytest)
- Comprehensive test suite with pytest

### Changed
- Restructured project into modular components
- Improved error handling and logging
- Updated deployment server with better process management
- Enhanced DNS management with better error reporting
- Improved Git operations with better validation

### Fixed
- Fixed package installation issues
- Improved error handling in deployment process
- Better logging configuration
- Enhanced directory permission checks

## [0.1.0] - 2024-01-17

### Added
- Initial release of dynapsys package
- Deployment server functionality for React applications
- Cloudflare DNS management integration
- Git repository cloning and validation
- PM2 process management integration
- Base64 deployment support
- Comprehensive logging system
- Command-line interface through entry points

### Changed
- Restructured project into modular components:
  - deployment.py: Core server and deployment logic
  - dns.py: Cloudflare DNS management
  - git.py: Git operations and validation

### Fixed
- Improved error handling in deployment process
- Better logging configuration
- Directory permission checks
- Git clone validation
