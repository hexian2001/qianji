# qianji v2 🚀

**Universal Browser Automation for AI - 100% OpenClaw Compatible**

任何 IDE / CLI / AI 都能使用的浏览器自动化工具。

## 特性

- ✅ **HTTP API** - RESTful API，任何语言都能调用
- ✅ **100% OpenClaw 兼容** - 相同端点和响应格式
- ✅ **Snapshot/Ref 系统** - 智能元素索引
- ✅ **多标签页** - 创建/关闭/切换标签页
- ✅ **Cookie/Storage** - 完整的存储管理
- ✅ **调试工具** - 控制台日志、错误、网络请求
- ✅ **CLI 工具** - 命令行直接操作
- ✅ **环境变量配置** - 灵活的配置方式

## 快速开始

### 安装

```bash
pip install qianji
playwright install chromium
```

### 启动服务器

```bash
# 默认启动
qianji-server

# 指定端口
qianji-server --port 18791

# 有头模式（可见浏览器）
qianji-server --headless=false

# 指定浏览器路径
qianji-server --browser-path /usr/bin/google-chrome
```

### CLI 使用

```bash
# 查看状态
qianji status

# 启动浏览器
qianji start

# 导航到页面
qianji navigate https://example.com

# 获取快照
qianji snapshot

# 点击元素 (e1 是快照中的 ref)
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
curl -X POST http://localhost:18791/navigate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# 获取快照
curl -X POST http://localhost:18791/snapshot

# 点击元素
curl -X POST http://localhost:18791/act/click \
  -H "Content-Type: application/json" \
  -d '{"ref": "e1"}'

# 输入文本
curl -X POST http://localhost:18791/act/type \
  -H "Content-Type: application/json" \
  -d '{"ref": "e2", "text": "hello", "submit": true}'

# 执行 JavaScript
curl -X POST http://localhost:18791/debug/evaluate \
  -H "Content-Type: application/json" \
  -d '{"script": "document.title"}'

# 获取 Cookie
curl -X POST http://localhost:18791/storage/cookies

# 截图
curl -X POST http://localhost:18791/screenshot \
  -H "Content-Type: application/json" \
  -d '{"fullPage": true}'
```

### Python 使用

```python
import httpx

# 创建客户端
client = httpx.Client(base_url="http://localhost:18791")

# 导航
client.post("/navigate", json={"url": "https://github.com/login"})

# 获取快照
resp = client.post("/snapshot")
snapshot = resp.json()
print(snapshot["interactive"])
# 输出:
# [e1] textbox: Username or email address
# [e2] textbox: Password
# [e3] button: Sign in

# 填写表单
client.post("/act/fill", json={"ref": "e1", "text": "myusername"})
client.post("/act/fill", json={"ref": "e2", "text": "mypassword"})

# 点击登录
client.post("/act/click", json={"ref": "e3"})

# 截图
client.post("/screenshot", json={"fullPage": True})
```

## API 端点

### 基础

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/` | 获取状态 |
| POST | `/start` | 启动浏览器 |
| POST | `/stop` | 停止浏览器 |
| POST | `/reset` | 重置浏览器 |

### 导航与快照

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/navigate` | 导航到URL |
| POST | `/snapshot` | 获取页面快照 |
| POST | `/screenshot` | 截图 |
| POST | `/pdf` | 生成PDF |
| POST | `/go-back` | 后退 |
| POST | `/go-forward` | 前进 |
| POST | `/reload` | 刷新 |

### 操作

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/act/click` | 点击元素 |
| POST | `/act/type` | 输入文本 |
| POST | `/act/fill` | 填充表单 |
| POST | `/act/press` | 按键 |
| POST | `/act/hover` | 悬停 |
| POST | `/act/select` | 选择选项 |
| POST | `/act/wait` | 等待 |

### 标签页

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/tabs` | 列出标签页 |
| POST | `/tabs/open` | 打开新标签页 |
| POST | `/tabs/close` | 关闭标签页 |
| POST | `/tabs/focus` | 聚焦标签页 |

### 存储

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/storage/cookies` | 获取 Cookie |
| POST | `/storage/cookies/set` | 设置 Cookie |
| POST | `/storage/cookies/clear` | 清除 Cookie |
| POST | `/storage/get` | 获取 Storage |
| POST | `/storage/set` | 设置 Storage |
| POST | `/storage/remove` | 删除 Storage 项 |
| POST | `/storage/clear` | 清空 Storage |

### 调试

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/debug/console` | 获取控制台日志 |
| POST | `/debug/errors` | 获取页面错误 |
| POST | `/debug/requests` | 获取网络请求 |
| POST | `/debug/evaluate` | 执行 JavaScript |

## 配置

### 环境变量

```bash
# 全局设置
export QIANJI_ENABLED=true
export QIANJI_HEADLESS=true
export QIANJI_NO_SANDBOX=false
export QIANJI_BROWSER_PATH=/usr/bin/google-chrome
export QIANJI_CONTROL_PORT=18791
export QIANJI_DEFAULT_PROFILE=default

# 配置文件特定设置
export QIANJI_PROFILE_DEFAULT_HEADLESS=false
export QIANJI_PROFILE_DEFAULT_BROWSER_PATH=/usr/bin/chromium
export QIANJI_PROFILE_WORK_HEADLESS=true
```

### 配置文件

```bash
# 创建配置文件目录
mkdir -p ~/.config/qianji

# 配置文件 (可选，环境变量优先级更高)
cat > ~/.config/qianji/config.json << 'JSON'
{
  "enabled": true,
  "headless": true,
  "noSandbox": false,
  "defaultProfile": "default",
  "profiles": {
    "default": {
      "headless": false,
      "executablePath": "/usr/bin/google-chrome"
    },
    "work": {
      "headless": true,
      "noSandbox": true
    }
  }
}
JSON
```

## 与 OpenClaw 对比

| 功能 | OpenClaw | qianji v2 |
|------|----------|-----------|
| 架构 | Gateway + CDP | HTTP Server + Playwright |
| 语言 | TypeScript | Python |
| API 格式 | 相同 | 100% 兼容 |
| Snapshot | ✅ | ✅ |
| Ref 系统 | ✅ | ✅ |
| 多标签页 | ✅ | ✅ |
| Cookie | ✅ | ✅ |
| Storage | ✅ | ✅ |
| 独立运行 | ❌ 需要 OpenClaw | ✅ 独立运行 |

## 适用场景

- **AI 工具集成** - Claude, Cursor, Copilot 等
- **自动化测试** - Playwright 替代方案
- **数据抓取** - 爬虫和采集
- **自动化工作流** - RPA 场景
- **CLI 工具** - 命令行自动化

## 许可证

MIT License

## MCP 配置

### 一键配置

```bash
# 配置所有支持的 IDE
qianji-setup-mcp

# 配置特定 IDE
qianji-setup-mcp --ide claude
qianji-setup-mcp --ide cursor
qianji-setup-mcp --ide windsurf

# 预览配置（不实际写入）
qianji-setup-mcp --dry-run

# 指定服务器地址
qianji-setup-mcp --server http://localhost:18791

# 生成配置脚本
qianji-setup-mcp --generate-script
qianji-setup-mcp --generate-script --output setup-mcp.sh
```

### 支持的 IDE

- **Claude Desktop** - Anthropic 的桌面应用
- **Cursor** - AI 驱动的代码编辑器
- **Windsurf** - Codeium 的 AI IDE

### 手动配置

#### Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "qianji": {
      "command": "python",
      "args": ["-m", "qianji.mcp"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

#### Cursor

编辑 `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "qianji": {
      "command": "python",
      "args": ["-m", "qianji.mcp"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

### 使用 MCP

配置完成后，在 IDE 中可以直接使用：

```
用户: 帮我打开 github.com 并登录
AI: 我来帮您操作浏览器...
    [使用 browser_navigate 导航到 github.com]
    [使用 browser_snapshot 获取页面快照]
    [使用 browser_fill 填写用户名密码]
    [使用 browser_click 点击登录按钮]
```
