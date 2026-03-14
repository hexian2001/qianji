# Qianji v2 🚀

[![CI](https://github.com/hexian2001/qianji/actions/workflows/ci.yml/badge.svg)](https://github.com/hexian2001/qianji/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/qianji.svg)](https://badge.fury.io/py/qianji)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**通用浏览器自动化工具**

Qianji 是一个企业级的浏览器自动化工具，专为 AI 智能体、开发者和自动化工作流设计。它提供了强大的 HTTP API、CLI 工具和 MCP（模型上下文协议）支持。

📖 [English Documentation](README.md)

## ✨ 特性

- 🌐 **HTTP API** - 支持任何语言的 RESTful API
- 🖥️ **CLI 工具** - 带自动补全的命令行界面
- 🤖 **MCP 支持** - 原生模型上下文协议集成
- 🔄 **多浏览器** - 管理多个浏览器实例
- 📸 **智能快照** - 带引用 ID 的元素检测
- 🗂️ **标签页管理** - 创建、切换和关闭标签页
- 🍪 **存储管理** - Cookies、localStorage、sessionStorage
- 🐛 **调试工具** - 控制台日志、网络请求、错误捕获
- 🔒 **企业级** - 结构化日志、错误处理、完整测试
- 🛡️ **验证码绕过** - 增强的人机验证规避能力，支持隐身模式

## 🚀 快速开始

### 安装

```bash
# 从 PyPI 安装
cd qianji && pip install -e .

# 安装 Chrome（智能安装 - 自动检测平台）
chmod +x install-chrome.sh && ./install-chrome.sh
source ~/.bashrc  # 或 ~/.zshrc

# 或使用 playwright（较慢）
# playwright install chromium
```

### CLI 使用

```bash
# 检查服务器状态
qianji status

# 启动浏览器（如未运行会自动启动服务器）
qianji start

# 导航到页面
qianji navigate https://example.com

# 获取页面快照
qianji snapshot

# 点击元素（e1 是快照中的引用 ID）
qianji click e1

# 输入文本
qianji type e2 "hello world"

# 截图
qianji screenshot output.png --full-page

# 停止浏览器
qianji stop
```

### HTTP API 使用

```bash
# 导航
curl -X POST http://localhost:18796/api/v1/navigate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# 获取快照
curl -X POST http://localhost:18796/api/v1/snapshot

# 点击元素
curl -X POST http://localhost:18796/api/v1/act/click \
  -H "Content-Type: application/json" \
  -d '{"ref": "e1"}'
```

### Python API 使用

```python
from qianji import BrowserManager
from qianji.models.config import BrowserConfig

# 创建配置
config = BrowserConfig(
    headless=False,
    no_sandbox=False,
)

# 启动浏览器
manager = BrowserManager(config)
await manager.start()

# 获取页面
page = await manager.get_or_create_page()

# 导航
await page.goto("https://example.com")

# 截图
await page.screenshot(path="screenshot.png")

# 停止浏览器
await manager.stop()
```

## 📚 文档

- [API 文档](docs/openapi.json) - OpenAPI/Swagger 规范
- [架构文档](ARCHITECTURE.md) - 系统架构和设计
- [贡献指南](CONTRIBUTING.md) - 贡献指南
- [更新日志](CHANGELOG.md) - 版本历史

## 🏗️ 项目结构

```
qianji/
├── qianji/
│   ├── core/           # 核心浏览器管理
│   ├── routes/         # API 路由
│   ├── models/         # 数据模型
│   ├── utils/          # 工具模块
│   ├── cli.py          # CLI 工具
│   ├── server.py       # HTTP 服务器
│   └── mcp.py          # MCP 支持
├── tests/              # 测试套件
├── docs/               # 文档
├── .github/workflows/  # CI/CD
└── pyproject.toml      # 项目配置
```

## 🧪 开发

### 设置

```bash
# 克隆仓库
git clone https://github.com/hexian2001/qianji.git
cd qianji

# 安装开发依赖
pip install -e ".[dev]"
playwright install chromium

# 安装 pre-commit 钩子
pre-commit install
```

### 代码质量

```bash
# 格式化代码
black qianji tests

# 运行 linter
ruff check qianji tests

# 类型检查
mypy qianji

# 运行测试
pytest

# 生成覆盖率报告
pytest --cov=qianji --cov-report=html
```

## 🔧 配置

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `QIANJI_PORT` | 服务器端口 | 18796 |
| `QIANJI_HEADLESS` | 无头模式 | true |
| `QIANJI_NO_SANDBOX` | 禁用沙箱 | false |
| `QIANJI_IDLE_TIMEOUT` | 空闲超时（秒） | 3600 |
| `QIANJI_MAX_LIFETIME` | 最大生命周期（秒） | 3600 |

### CLI 选项

```bash
# 使用选项启动服务器
qianji-server --port 18796 --headless=false

# CLI 选项
qianji --server http://localhost:18796 status
qianji start --headless --window-size 1920,1080
qianji snapshot --format json
```

## 🤝 贡献

我们欢迎贡献！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解指南。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [Playwright](https://playwright.dev/) - 浏览器自动化库
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [OpenClaw](https://github.com/efritz/openclaw) - 浏览器自动化设计参考

## 📞 支持

- GitHub Issues: [https://github.com/hexian2001/qianji/issues](https://github.com/hexian2001/qianji/issues)
- 文档: [https://github.com/hexian2001/qianji#readme](https://github.com/hexian2001/qianji#readme)

---

用 ❤️ 为 AI 社区打造
