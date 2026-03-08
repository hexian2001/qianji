# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Enterprise-grade project structure
- Comprehensive test suite with pytest
- CI/CD pipeline with GitHub Actions
- Code quality tools: Black, Ruff, MyPy
- Pre-commit hooks configuration
- OpenAPI/Swagger API documentation
- Structured logging with structlog
- Custom exception hierarchy
- `--format` flag for CLI output (text/json)
- Automatic server startup in CLI
- Root user auto-detection for --no-sandbox

### Changed
- Refactored CLI with better error handling
- Improved browser startup with background tasks
- Enhanced documentation structure

### Fixed
- HTTP timeout issues during browser startup
- Parameter passing in browser registry

## [2.0.0] - 2024-01-XX

### Added
- Multi-browser support with browser registry
- Browser lifecycle management (idle timeout, max lifetime)
- CLI tool with comprehensive commands
- MCP (Model Context Protocol) support
- HTTP API with FastAPI
- Snapshot/Ref system for element interaction
- Tab management (create, close, switch)
- Cookie and storage management
- Screenshot capabilities
- JavaScript evaluation
- Form interaction (fill, type, click)

### Changed
- Complete rewrite for OpenClaw compatibility
- New configuration system with profiles

## [1.0.0] - 2023-XX-XX

### Added
- Initial release
- Basic browser automation
- HTTP API server
- Single browser instance support
