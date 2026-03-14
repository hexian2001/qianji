# Qianji v2 🚀

[![CI](https://github.com/hexian2001/qianji/actions/workflows/ci.yml/badge.svg)](https://github.com/hexian2001/qianji/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/qianji.svg)](https://badge.fury.io/py/qianji)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Universal Browser Automation for AI**

Qianji is an enterprise-grade browser automation tool designed for AI agents, developers, and automation workflows. It provides a robust HTTP API, CLI tool, and MCP (Model Context Protocol) support.

📖 [中文文档](README_CN.md)

## ✨ Features

- 🌐 **HTTP API** - RESTful API for any language
- 🖥️ **CLI Tool** - Command-line interface with auto-completion
- 🤖 **MCP Support** - Native Model Context Protocol integration
- 🔄 **Multi-Browser** - Manage multiple browser instances
- 📸 **Smart Snapshots** - Element detection with reference IDs
- 🗂️ **Tab Management** - Create, switch, and close tabs
- 🍪 **Storage Management** - Cookies, localStorage, sessionStorage
- 🐛 **Debug Tools** - Console logs, network requests, errors
- 🔒 **Enterprise Ready** - Structured logging, error handling, tests
- 🛡️ **CAPTCHA Bypass** - Enhanced human verification evasion with stealth mode

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
cd qianji && pip install -e .

# Install Chrome (Intelligent - Auto-detect platform)
chmod +x install-chrome.sh && ./install-chrome.sh
source ~/.bashrc  # or ~/.zshrc

# Or use playwright (slower)
# playwright install chromium
```

### CLI Usage

```bash
# Check server status
qianji status

# Start browser (auto-starts server if not running)
qianji start

# Navigate to a page
qianji navigate https://example.com

# Get page snapshot
qianji snapshot

# Click element (e1 is the reference from snapshot)
qianji click e1

# Type text
qianji type e2 "hello world"

# Take screenshot
qianji screenshot output.png --full-page

# Stop browser
qianji stop
```

### HTTP API Usage

```bash
# Navigate
curl -X POST http://localhost:18796/api/v1/navigate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Get snapshot
curl -X POST http://localhost:18796/api/v1/snapshot

# Click element
curl -X POST http://localhost:18796/api/v1/act/click \
  -H "Content-Type: application/json" \
  -d '{"ref": "e1"}'
```

### Python API Usage

```python
from qianji import BrowserManager
from qianji.models.config import BrowserConfig

# Create configuration
config = BrowserConfig(
    headless=False,
    no_sandbox=False,
)

# Start browser
manager = BrowserManager(config)
await manager.start()

# Get page
page = await manager.get_or_create_page()

# Navigate
await page.goto("https://example.com")

# Take screenshot
await page.screenshot(path="screenshot.png")

# Stop browser
await manager.stop()
```

## 📚 Documentation

- [API Documentation](docs/openapi.json) - OpenAPI/Swagger specification
- [Architecture](ARCHITECTURE.md) - System architecture and design
- [Contributing](CONTRIBUTING.md) - Contribution guidelines
- [Changelog](CHANGELOG.md) - Version history

## 🏗️ Project Structure

```
qianji/
├── qianji/
│   ├── core/           # Core browser management
│   ├── routes/         # API routes
│   ├── models/         # Data models
│   ├── utils/          # Utilities
│   ├── cli.py          # CLI tool
│   ├── server.py       # HTTP server
│   └── mcp.py          # MCP support
├── tests/              # Test suite
├── docs/               # Documentation
├── .github/workflows/  # CI/CD
└── pyproject.toml      # Project config
```

## 🧪 Development

### Setup

```bash
# Clone repository
git clone https://github.com/hexian2001/qianji.git
cd qianji

# Install development dependencies
cd qianji && pip install -e ".[dev]"
playwright install chromium

# Install pre-commit hooks
pre-commit install
```

### Code Quality

```bash
# Format code
black qianji tests

# Run linter
ruff check qianji tests

# Type check
mypy qianji

# Run tests
pytest

# Run with coverage
pytest --cov=qianji --cov-report=html
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `QIANJI_PORT` | Server port | 18796 |
| `QIANJI_HEADLESS` | Run headless | true |
| `QIANJI_NO_SANDBOX` | Disable sandbox | false |
| `QIANJI_IDLE_TIMEOUT` | Idle timeout (s) | 3600 |
| `QIANJI_MAX_LIFETIME` | Max lifetime (s) | 3600 |

### CLI Options

```bash
# Start server with options
qianji-server --port 18796 --headless=false

# CLI with options
qianji --server http://localhost:18796 status
qianji start --headless --window-size 1920,1080
qianji snapshot --format json
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) - Browser automation library
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [OpenClaw](https://github.com/efritz/openclaw) - browser automation design reference

## 📞 Support

- GitHub Issues: [https://github.com/hexian2001/qianji/issues](https://github.com/hexian2001/qianji/issues)
- Documentation: [https://github.com/hexian2001/qianji#readme](https://github.com/hexian2001/qianji#readme)

---

Made with ❤️ for the AI community
