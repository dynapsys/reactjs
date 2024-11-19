# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
