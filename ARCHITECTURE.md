# Qianji Architecture

This document describes the high-level architecture of Qianji.

## Overview

Qianji is a browser automation tool designed for AI agents. It provides:

- **HTTP API**: RESTful API for browser control
- **CLI Tool**: Command-line interface for direct interaction
- **MCP Support**: Model Context Protocol integration
- **Multi-Browser**: Support for multiple browser instances

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Clients                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   CLI Tool  │  │  HTTP API   │  │  MCP (AI Agents)    │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
          └────────────────┴────────────────────┘
                           │
          ┌────────────────┴────────────────────┐
          │         FastAPI Server               │
          │  ┌──────────────────────────────┐   │
          │  │       API Routes             │   │
          │  │  ┌──────┐ ┌──────┐ ┌──────┐  │   │
          │  │  │Basic │ │Agent │ │Tabs  │  │   │
          │  │  └──────┘ └──────┘ └──────┘  │   │
          │  └──────────────────────────────┘   │
          └────────────────┬────────────────────┘
                           │
          ┌────────────────┴────────────────────┐
          │         Core Layer                   │
          │  ┌──────────┐    ┌──────────────┐   │
          │  │ Browser  │◄──►│ Tab Manager  │   │
          │  │ Registry │    └──────────────┘   │
          │  └────┬─────┘                       │
          │       │                             │
          │  ┌────┴─────┐    ┌──────────────┐   │
          │  │ Browser  │◄──►│ PW Client    │   │
          │  │ Manager  │    │ (Playwright) │   │
          │  └──────────┘    └──────────────┘   │
          └─────────────────────────────────────┘
                           │
          ┌────────────────┴────────────────────┐
          │      External Dependencies           │
          │         (Playwright/Browser)         │
          └─────────────────────────────────────┘
```

## Components

### 1. API Layer (`qianji/routes/`)

#### Basic Routes (`basic.py`)
- Server status
- Browser lifecycle (start, stop)
- Browser instance management

#### Agent Routes (`agent_*.py`)
- `agent_snapshot.py`: Page snapshots and element detection
- `agent_act.py`: User actions (click, type, fill)
- `agent_storage.py`: Cookie and local storage
- `agent_dialog.py`: Dialog handling
- `agent_debug.py`: Console logs and network

#### Tab Routes (`tabs.py`)
- Tab creation and management
- Tab switching

### 2. Core Layer (`qianji/core/`)

#### Browser Registry (`browser_registry.py`)
- Manages multiple browser instances
- Handles browser lifecycle
- Routes requests to correct browser

#### Browser Manager (`browser_manager.py`)
- Controls individual browser instance
- Manages Playwright context
- Handles browser startup/shutdown

#### Tab Manager (`tab_manager.py`)
- Manages tabs within a browser
- Handles tab switching
- Tracks tab state

#### PW Client (`pw_client.py`)
- Playwright integration
- Browser detection
- Page interaction

### 3. Models (`qianji/models/`)

#### Config (`config.py`)
- Browser configuration
- Profile management
- Settings validation

#### Responses (`responses.py`)
- API response models
- Standardized output format

#### Snapshot (`snapshot.py`)
- Page snapshot data
- Element information

### 4. CLI (`qianji/cli.py`)

- Command-line interface
- HTTP client for API
- Auto server startup
- Format output (text/json)

### 5. MCP Support (`qianji/mcp*.py`)

- Model Context Protocol integration
- Tool definitions for AI agents
- Server wrapper

## Data Flow

### Browser Startup

```
1. Client → POST /start
2. API Route → browser_registry.create_browser()
3. BrowserRegistry → new BrowserManager
4. BrowserManager → pw_client.launch_browser()
5. Playwright → Launch browser process
6. Return browser_id to client
```

### Page Navigation

```
1. Client → POST /api/v1/navigate {url}
2. API Route → browser_registry.get_browser()
3. BrowserManager → get_or_create_page()
4. Page → goto(url)
5. Return {url, title} to client
```

### Element Interaction

```
1. Client → POST /api/v1/snapshot
2. Snapshot → Parse DOM, assign refs
3. Return interactive elements with refs
4. Client → POST /api/v1/act/click {ref}
5. Find element by ref → click()
6. Return success status
```

## Configuration

### Profile Configuration

```python
ProfileConfig:
  - name: str
  - headless: bool
  - no_sandbox: bool
  - user_data_dir: Optional[str]
  - args: List[str]
```

### Browser Configuration

```python
BrowserConfig:
  - port: int
  - headless: bool
  - no_sandbox: bool
  - idle_timeout: float
  - max_lifetime: float
  - profiles: Dict[str, ProfileConfig]
```

## Multi-Browser Support

Qianji supports multiple concurrent browser instances:

```
browser_registry:
  _browsers: Dict[str, BrowserInstance]
    - browser_1: BrowserInstance
    - browser_2: BrowserInstance
    - ...

BrowserInstance:
  - browser_id: str
  - manager: BrowserManager
  - profile_name: str
  - user_data_dir: str
  - idle_timeout: float
  - max_lifetime: float
```

Each browser instance:
- Has isolated user data directory
- Independent lifecycle
- Separate tab management

## Error Handling

### Exception Hierarchy

```
QianjiError (base)
  ├── BrowserError
  │   ├── BrowserNotStartedError
  │   ├── BrowserLaunchError
  │   ├── NavigationError
  │   ├── ElementNotFoundError
  │   └── ActionError
  ├── ConfigError
  └── ValidationError
```

### Error Response Format

```json
{
  "ok": false,
  "success": false,
  "error": {
    "code": "ELEMENT_NOT_FOUND",
    "message": "Element not found: e99"
  }
}
```

## Security Considerations

1. **Sandbox Mode**: Disabled for Docker/root with `--no-sandbox`
2. **User Data Isolation**: Each browser has isolated user data
3. **Input Validation**: All inputs validated with Pydantic
4. **Timeout Protection**: Idle and max lifetime timeouts
5. **Resource Cleanup**: Automatic cleanup on shutdown

## Performance

1. **Async Operations**: All I/O is async
2. **Connection Pooling**: HTTP client reuse
3. **Lazy Loading**: Browser started on first use
4. **Background Tasks**: Browser startup is non-blocking

## Extension Points

1. **Custom Profiles**: Define browser profiles in config
2. **Middleware**: FastAPI middleware for request/response
3. **Custom Actions**: Extend agent_act.py
4. **Plugins**: Future plugin system
