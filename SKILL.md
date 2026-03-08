# Qianji Skill 文档

Qianji 是一个浏览器自动化工具，提供 CLI 接口用于控制浏览器。

## 安装

```bash
# 克隆仓库
git clone <repository-url>
cd qianji

# 安装依赖
pip install -e .

# 或使用 Conda
conda create -n qianji python=3.12
conda activate qianji
pip install -e .
```

## 快速开始

```bash
# 查看帮助
qianji --help

# 查看服务器状态
qianji status

# 启动默认浏览器
qianji start

# 导航到网页
qianji navigate https://example.com

# 获取页面快照
qianji snapshot
```

## CLI 完整用法

### 全局选项

```bash
qianji [全局选项] <命令> [命令选项]
```

| 选项 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--server` | | 服务器 URL | http://localhost:18796 |
| `--format` | | 输出格式 (`text` 或 `json`) | text |
| `--help` | `-h` | 显示帮助信息 | - |

### 输出格式

所有命令都支持 `--format` 参数，可以选择 `text`（人类可读）或 `json`（机器可读）格式输出。

**示例：**
```bash
# 文本格式（默认）
qianji status

# JSON 格式
qianji status --format json

# 获取页面快照为 JSON
qianji snapshot --format json

# 列出浏览器为 JSON
qianji browsers --format json
```

### 命令列表

#### 1. status - 获取服务器状态

```bash
qianji status [选项]
```

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--format` | 输出格式 (`text` 或 `json`) | text |

**示例：**
```bash
qianji status
qianji status --format json
qianji --server http://localhost:18888 status
```

---

#### 2. browsers - 列出所有浏览器实例

```bash
qianji browsers [选项]
```

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--format` | 输出格式 (`text` 或 `json`) | text |

**示例：**
```bash
qianji browsers
qianji browsers --format json
```

---

#### 3. new-browser - 创建新浏览器实例

```bash
qianji new-browser [选项]
```

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--id` | 浏览器实例 ID（可选，自动生成） | - |
| `--profile` | 配置文件名称 | default |
| `--headless` | 无头模式 | False |
| `--no-sandbox` | 禁用沙箱 | False |
| `--sandbox` | 强制启用沙箱（覆盖 root 自动检测） | False |
| `--window-size` | 窗口大小（例如：1920,1080） | - |
| `--user-agent` | 自定义 User-Agent | - |
| `--proxy` | 代理服务器（例如：http://proxy:8080） | - |
| `--disable-dev-shm` | 禁用 /dev/shm 使用 | False |
| `--disable-gpu` | 禁用 GPU 加速 | False |
| `--disable-extensions` | 禁用浏览器扩展 | False |
| `--format` | 输出格式 (`text` 或 `json`) | text |

**示例：**
```bash
# 创建默认浏览器（root 用户自动启用 --no-sandbox）
qianji new-browser --id chrome1

# 创建无头浏览器
qianji new-browser --id chrome1 --headless

# 强制启用沙箱（root 用户）
qianji new-browser --id chrome1 --sandbox

# 创建指定窗口大小的浏览器
qianji new-browser --id chrome1 --window-size 1920,1080

# 创建带代理的浏览器
qianji new-browser --id chrome1 --proxy http://proxy.example.com:8080

# 创建带自定义 User-Agent 的浏览器
qianji new-browser --id chrome1 --user-agent "Mozilla/5.0..."

# 组合使用多个选项
qianji new-browser --id chrome1 --headless --window-size 1920,1080
```

---

#### 4. close-browser - 关闭浏览器实例

```bash
qianji close-browser <browser_id> [选项]
```

**参数：**

| 参数 | 说明 |
|------|------|
| `browser_id` | 浏览器实例 ID（必需） |

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--format` | 输出格式 (`text` 或 `json`) | text |

**示例：**
```bash
qianji close-browser chrome1
qianji close-browser chrome1 --format json
```

---

#### 5. start - 启动默认浏览器

```bash
qianji start [选项]
```

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--profile` | 配置文件名称 | default |
| `--headless` | 无头模式 | False |
| `--no-sandbox` | 禁用沙箱 | False |
| `--sandbox` | 强制启用沙箱（覆盖 root 自动检测） | False |
| `--window-size` | 窗口大小（例如：1920,1080） | - |
| `--user-agent` | 自定义 User-Agent | - |
| `--proxy` | 代理服务器（例如：http://proxy:8080） | - |
| `--disable-dev-shm` | 禁用 /dev/shm 使用 | False |
| `--disable-gpu` | 禁用 GPU 加速 | False |
| `--disable-extensions` | 禁用浏览器扩展 | False |
| `--format` | 输出格式 (`text` 或 `json`) | text |

**示例：**
```bash
# 启动默认浏览器（root 用户自动启用 --no-sandbox）
qianji start

# 启动无头浏览器
qianji start --headless

# 强制启用沙箱（root 用户）
qianji start --sandbox

# 启动指定窗口大小的浏览器
qianji start --window-size 1920,1080

# 启动带自定义 User-Agent 的浏览器
qianji start --user-agent "Mozilla/5.0..."

# 启动带代理的浏览器
qianji start --proxy http://proxy.example.com:8080

# 组合使用多个选项
qianji start --headless --window-size 1920,1080
```

---

#### 6. stop - 停止浏览器

```bash
qianji stop [选项]
```

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--browser` | 浏览器实例 ID | default |
| `--format` | 输出格式 (`text` 或 `json`) | text |

**示例：**
```bash
# 停止默认浏览器
qianji stop

# 停止指定浏览器
qianji stop --browser chrome1
```

---

#### 7. tabs - 列出所有标签页

```bash
qianji tabs [选项]
```

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--browser` | 浏览器实例 ID | default |
| `--format` | 输出格式 (`text` 或 `json`) | text |

**示例：**
```bash
# 列出默认浏览器的标签页
qianji tabs

# 列出指定浏览器的标签页
qianji tabs --browser chrome1
```

---

#### 8. navigate - 导航到 URL

```bash
qianji navigate <url> [选项]
```

**参数：**

| 参数 | 说明 |
|------|------|
| `url` | 目标 URL（必需） |

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--browser` | 浏览器实例 ID | default |
| `--target` | 目标标签页 ID | current |
| `--format` | 输出格式 (`text` 或 `json`) | text |

**示例：**
```bash
# 导航到网页
qianji navigate https://example.com

# 在指定浏览器中导航
qianji navigate https://example.com --browser chrome1

# 在新标签页中导航
qianji navigate https://example.com --target new_tab

```

---

#### 9. snapshot - 获取页面快照

```bash
qianji snapshot [选项]
```

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--browser` | 浏览器实例 ID | default |
| `--target` | 目标标签页 ID | current |
| `--format` | 输出格式 (`text` 或 `json`) | text |

**示例：**
```bash
# 获取页面快照（文本格式）
qianji snapshot

# 获取指定浏览器的快照
qianji snapshot --browser chrome1

# 获取 JSON 格式快照
qianji snapshot --format json

# 获取文本格式快照
qianji snapshot --format text
```

---

#### 10. click - 点击元素

```bash
qianji click <element_id> [选项]
```

**参数：**

| 参数 | 说明 |
|------|------|
| `element_id` | 元素 ID（必需） |

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--browser` | 浏览器实例 ID | default |
| `--target` | 目标标签页 ID | current |
| `--format` | 输出格式 (`text` 或 `json`) | text |

**示例：**
```bash
# 点击元素
qianji click e1

# 在指定浏览器中点击
qianji click e1 --browser chrome1

# 在指定标签页中点击
qianji click e1 --browser chrome1 --target tab1

# JSON 格式输出
qianji click e1 --format json
```

---

#### 11. type - 输入文本

```bash
qianji type <element_id> <text> [选项]
```

**参数：**

| 参数 | 说明 |
|------|------|
| `element_id` | 元素 ID（必需） |
| `text` | 要输入的文本（必需） |

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--browser` | 浏览器实例 ID | default |
| `--target` | 目标标签页 ID | current |
| `--submit` | 输入后提交表单 | False |
| `--format` | 输出格式 (`text` 或 `json`) | text |

**示例：**
```bash
# 输入文本
qianji type e2 "hello world"

# 在指定浏览器中输入
qianji type e2 "hello world" --browser chrome1

# 输入后提交
qianji type e2 "hello world" --submit

# JSON 格式输出
qianji type e2 "hello world" --format json
```

---

#### 12. screenshot - 截取屏幕

```bash
qianji screenshot <output_path> [选项]
```

**参数：**

| 参数 | 说明 |
|------|------|
| `output_path` | 输出文件路径（必需） |

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--browser` | 浏览器实例 ID | default |
| `--target` | 目标标签页 ID | current |
| `--full-page` | 截取整个页面 | False |
| `--format` | 输出格式 (`text` 或 `json`) | text |

**示例：**
```bash
# 截取屏幕
qianji screenshot output.png

# 截取整个页面
qianji screenshot full.png --full-page

# 指定浏览器截图
qianji screenshot chrome1.png --browser chrome1

# JSON 格式输出
qianji screenshot output.png --format json
```

---

#### 13. fill - 填充表单字段

```bash
qianji fill <element_id> <text> [选项]
```

**参数：**

| 参数 | 说明 |
|------|------|
| `element_id` | 元素 ID（必需） |
| `text` | 要填充的文本（必需） |

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--browser` | 浏览器实例 ID | default |
| `--target` | 目标标签页 ID | current |
| `--format` | 输出格式 (`text` 或 `json`) | text |

**示例：**
```bash
# 填充输入框
qianji fill e1 "myuser"
qianji fill e2 "mypass"

# 在指定浏览器中填充
qianji fill e1 "query" --browser chrome1

# JSON 格式输出
qianji fill e1 "text" --format json
```

---

#### 14. evaluate - 执行 JavaScript

```bash
qianji evaluate <script> [选项]
```

**参数：**

| 参数 | 说明 |
|------|------|
| `script` | JavaScript 代码（必需） |

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--browser` | 浏览器实例 ID | default |
| `--target` | 目标标签页 ID | current |
| `--format` | 输出格式 (`text` 或 `json`) | text |

**示例：**
```bash
# 执行简单脚本
qianji evaluate "document.title"

# 执行复杂脚本
qianji evaluate "document.querySelector('h1').textContent"

# 在指定浏览器中执行
qianji evaluate "window.location.href" --browser chrome1

# JSON 格式输出
qianji evaluate "document.title" --format json
```

---

## 完整示例

### 自动化登录流程

```bash
# 1. 启动浏览器
qianji start --browser chrome1

# 2. 导航到登录页
qianji navigate https://example.com/login --browser chrome1

# 3. 填写表单
qianji fill "#username" "myuser" --browser chrome1
qianji fill "#password" "mypass" --browser chrome1

# 4. 点击登录按钮
qianji click "#login-btn" --browser chrome1

# 5. 等待页面加载
sleep 2

# 6. 获取页面快照
qianji snapshot --browser chrome1 --format text

# 7. 截图保存
qianji screenshot logged_in.png --browser chrome1

# 8. 关闭浏览器
qianji stop --browser chrome1
```

### 多浏览器并行操作

```bash
# 创建两个浏览器实例
qianji new-browser --id browser1
qianji new-browser --id browser2

# 同时在两个浏览器中导航
qianji navigate https://site1.com --browser browser1 &
qianji navigate https://site2.com --browser browser2 &
wait

# 分别截图
qianji screenshot site1.png --browser browser1
qianji screenshot site2.png --browser browser2

# 关闭浏览器
qianji close-browser --id browser1
qianji close-browser --id browser2
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `QIANJI_SERVER_URL` | 服务器 URL | http://localhost:18796 |
| `QIANJI_DEFAULT_BROWSER` | 默认浏览器 ID | default |

## 故障排除

### 常见问题

1. **连接失败**
   ```bash
   # 检查服务器是否运行
   qianji status
   
   # 指定服务器地址
   qianji --server http://localhost:18888 status
   ```

2. **浏览器启动失败**
   ```bash
   # 检查浏览器实例是否存在
   qianji browsers
   
   # 创建新浏览器
   qianji new-browser --id chrome1
   ```

3. **元素未找到**
   ```bash
   # 先获取页面快照查看可用元素
   qianji snapshot
   ```

## 许可证

MIT License
