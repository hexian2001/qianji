"""
MCP 配置生成器 - 一键配置 Claude Desktop, Cursor 等工具
"""

import json
import os
import platform
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class MCPSetup:
    """MCP 配置设置工具"""
    
    def __init__(self):
        self.system = platform.system()
        self.home = Path.home()
    
    def get_claude_config_path(self) -> Optional[Path]:
        """获取 Claude Desktop 配置文件路径"""
        if self.system == "Darwin":  # macOS
            return self.home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        elif self.system == "Windows":
            return Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
        else:  # Linux
            return self.home / ".config" / "Claude" / "claude_desktop_config.json"
    
    def get_cursor_config_path(self) -> Optional[Path]:
        """获取 Cursor 配置文件路径"""
        if self.system == "Darwin":
            return self.home / "Library" / "Application Support" / "Cursor" / "mcp.json"
        elif self.system == "Windows":
            return Path(os.environ.get("APPDATA", "")) / "Cursor" / "mcp.json"
        else:
            return self.home / ".config" / "Cursor" / "mcp.json"
    
    def get_windsurf_config_path(self) -> Optional[Path]:
        """获取 Windsurf 配置文件路径"""
        if self.system == "Darwin":
            return self.home / ".codeium" / "windsurf" / "mcp_config.json"
        elif self.system == "Windows":
            return Path(os.environ.get("USERPROFILE", "")) / ".codeium" / "windsurf" / "mcp_config.json"
        else:
            return self.home / ".codeium" / "windsurf" / "mcp_config.json"
    
    def generate_qianji_mcp_config(self, server_url: str = "http://localhost:18791") -> Dict[str, Any]:
        """生成 qianji MCP 配置"""
        return {
            "command": sys.executable,
            "args": ["-m", "qianji.mcp", "--server", server_url],
            "env": {
                "PYTHONIOENCODING": "utf-8"
            },
            "description": "Universal Browser Automation for AI",
        }
    
    def setup_claude(self, server_url: str = "http://localhost:18791", dry_run: bool = False) -> str:
        """配置 Claude Desktop"""
        config_path = self.get_claude_config_path()
        if not config_path:
            return "❌ 无法确定 Claude Desktop 配置路径"
        
        # 读取现有配置
        config = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception as e:
                return f"❌ 读取配置失败: {e}"
        
        # 确保 mcpServers 存在
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # 添加 qianji
        config["mcpServers"]["qianji"] = self.generate_qianji_mcp_config(server_url)
        
        if dry_run:
            return f"📋 Claude Desktop 配置预览 ({config_path}):\n{json.dumps(config, indent=2, ensure_ascii=False)}"
        
        # 写入配置
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, indent=2, fp=f, ensure_ascii=False)
            return f"✅ Claude Desktop 配置已更新: {config_path}"
        except Exception as e:
            return f"❌ 写入配置失败: {e}"
    
    def setup_cursor(self, server_url: str = "http://localhost:18791", dry_run: bool = False) -> str:
        """配置 Cursor"""
        config_path = self.get_cursor_config_path()
        if not config_path:
            return "❌ 无法确定 Cursor 配置路径"
        
        # 读取现有配置
        config = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception as e:
                return f"❌ 读取配置失败: {e}"
        
        # 确保 mcpServers 存在
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # 添加 qianji
        config["mcpServers"]["qianji"] = self.generate_qianji_mcp_config(server_url)
        
        if dry_run:
            return f"📋 Cursor 配置预览 ({config_path}):\n{json.dumps(config, indent=2, ensure_ascii=False)}"
        
        # 写入配置
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, indent=2, fp=f, ensure_ascii=False)
            return f"✅ Cursor 配置已更新: {config_path}"
        except Exception as e:
            return f"❌ 写入配置失败: {e}"
    
    def setup_windsurf(self, server_url: str = "http://localhost:18791", dry_run: bool = False) -> str:
        """配置 Windsurf"""
        config_path = self.get_windsurf_config_path()
        if not config_path:
            return "❌ 无法确定 Windsurf 配置路径"
        
        # 读取现有配置
        config = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception as e:
                return f"❌ 读取配置失败: {e}"
        
        # 确保 mcpServers 存在
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # 添加 qianji
        config["mcpServers"]["qianji"] = self.generate_qianji_mcp_config(server_url)
        
        if dry_run:
            return f"📋 Windsurf 配置预览 ({config_path}):\n{json.dumps(config, indent=2, ensure_ascii=False)}"
        
        # 写入配置
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, indent=2, fp=f, ensure_ascii=False)
            return f"✅ Windsurf 配置已更新: {config_path}"
        except Exception as e:
            return f"❌ 写入配置失败: {e}"
    
    def setup_all(self, server_url: str = "http://localhost:18791", dry_run: bool = False) -> str:
        """配置所有支持的 IDE"""
        results = []
        
        results.append("🎯 Claude Desktop:")
        results.append(self.setup_claude(server_url, dry_run))
        results.append("")
        
        results.append("🎯 Cursor:")
        results.append(self.setup_cursor(server_url, dry_run))
        results.append("")
        
        results.append("🎯 Windsurf:")
        results.append(self.setup_windsurf(server_url, dry_run))
        results.append("")
        
        if not dry_run:
            results.append("⚠️  请重启 IDE 以使配置生效")
        
        return "\n".join(results)
    
    def generate_shell_script(self, server_url: str = "http://localhost:18791") -> str:
        """生成 Shell 配置脚本"""
        script = f'''#!/bin/bash
# qianji MCP 配置脚本
# 一键配置 Claude Desktop, Cursor, Windsurf

set -e

echo "🔧 配置 qianji MCP..."

# 检测 Python 路径
PYTHON_PATH="{sys.executable}"
SERVER_URL="{server_url}"

# 配置 Claude Desktop
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CLAUDE_CONFIG="$HOME/.config/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    CLAUDE_CONFIG="$APPDATA/Claude/claude_desktop_config.json"
fi

if command -v claude &> /dev/null || [ -d "$(dirname "$CLAUDE_CONFIG")" ]; then
    echo "🎯 配置 Claude Desktop..."
    mkdir -p "$(dirname "$CLAUDE_CONFIG")"
    
    # 读取或创建配置
    if [ -f "$CLAUDE_CONFIG" ]; then
        CONFIG=$(cat "$CLAUDE_CONFIG")
    else
        CONFIG='{{}}'
    fi
    
    # 使用 Python 更新配置
    $PYTHON_PATH -c "
import json
import sys

config = json.loads('$CONFIG' if '$CONFIG' != '{{}}' else '{{}}')
if 'mcpServers' not in config:
    config['mcpServers'] = {{}}

config['mcpServers']['qianji'] = {{
    'command': '$PYTHON_PATH',
    'args': ['-m', 'qianji.mcp', '--server', '$SERVER_URL'],
    'env': {{'PYTHONIOENCODING': 'utf-8'}},
    'description': 'Universal Browser Automation for AI'
}}

print(json.dumps(config, indent=2))
" > "$CLAUDE_CONFIG"
    
    echo "✅ Claude Desktop 配置完成: $CLAUDE_CONFIG"
fi

# 配置 Cursor
CURSOR_CONFIG="$HOME/Library/Application Support/Cursor/mcp.json"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CURSOR_CONFIG="$HOME/.config/Cursor/mcp.json"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    CURSOR_CONFIG="$APPDATA/Cursor/mcp.json"
fi

if command -v cursor &> /dev/null || [ -d "$(dirname "$CURSOR_CONFIG")" ]; then
    echo "🎯 配置 Cursor..."
    mkdir -p "$(dirname "$CURSOR_CONFIG")"
    
    if [ -f "$CURSOR_CONFIG" ]; then
        CONFIG=$(cat "$CURSOR_CONFIG")
    else
        CONFIG='{{}}'
    fi
    
    $PYTHON_PATH -c "
import json

config = json.loads('$CONFIG' if '$CONFIG' != '{{}}' else '{{}}')
if 'mcpServers' not in config:
    config['mcpServers'] = {{}}

config['mcpServers']['qianji'] = {{
    'command': '$PYTHON_PATH',
    'args': ['-m', 'qianji.mcp', '--server', '$SERVER_URL'],
    'env': {{'PYTHONIOENCODING': 'utf-8'}},
    'description': 'Universal Browser Automation for AI'
}}

print(json.dumps(config, indent=2))
" > "$CURSOR_CONFIG"
    
    echo "✅ Cursor 配置完成: $CURSOR_CONFIG"
fi

# 配置 Windsurf
WINDSURF_CONFIG="$HOME/.codeium/windsurf/mcp_config.json"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    WINDSURF_CONFIG="$USERPROFILE/.codeium/windsurf/mcp_config.json"
fi

if command -v windsurf &> /dev/null || [ -d "$(dirname "$WINDSURF_CONFIG")" ]; then
    echo "🎯 配置 Windsurf..."
    mkdir -p "$(dirname "$WINDSURF_CONFIG")"
    
    if [ -f "$WINDSURF_CONFIG" ]; then
        CONFIG=$(cat "$WINDSURF_CONFIG")
    else
        CONFIG='{{}}'
    fi
    
    $PYTHON_PATH -c "
import json

config = json.loads('$CONFIG' if '$CONFIG' != '{{}}' else '{{}}')
if 'mcpServers' not in config:
    config['mcpServers'] = {{}}

config['mcpServers']['qianji'] = {{
    'command': '$PYTHON_PATH',
    'args': ['-m', 'qianji.mcp', '--server', '$SERVER_URL'],
    'env': {{'PYTHONIOENCODING': 'utf-8'}},
    'description': 'Universal Browser Automation for AI'
}}

print(json.dumps(config, indent=2))
" > "$WINDSURF_CONFIG"
    
    echo "✅ Windsurf 配置完成: $WINDSURF_CONFIG"
fi

echo ""
echo "🎉 MCP 配置完成！"
echo "⚠️  请重启 IDE 以使配置生效"
echo ""
echo "📖 使用方法:"
echo "   1. 启动 qianji-server: qianji-server"
echo "   2. 在 IDE 中启用 qianji MCP 工具"
echo "   3. 让 AI 使用浏览器自动化功能"
'''
        return script
    
    def generate_powershell_script(self, server_url: str = "http://localhost:18791") -> str:
        """生成 PowerShell 配置脚本 (Windows)"""
        script = f'''
# qianji MCP 配置脚本 (Windows)
# 一键配置 Claude Desktop, Cursor, Windsurf

$PYTHON_PATH = "{sys.executable}"
$SERVER_URL = "{server_url}"

Write-Host "🔧 配置 qianji MCP..." -ForegroundColor Cyan

# 配置 Claude Desktop
$CLAUDE_CONFIG = "$env:APPDATA\\Claude\\claude_desktop_config.json"
if (Test-Path (Split-Path $CLAUDE_CONFIG -Parent)) {{
    Write-Host "🎯 配置 Claude Desktop..." -ForegroundColor Yellow
    
    $config = @{{}}
    if (Test-Path $CLAUDE_CONFIG) {{
        $config = Get-Content $CLAUDE_CONFIG | ConvertFrom-Json
    }}
    
    if (-not $config.mcpServers) {{
        $config | Add-Member -NotePropertyName mcpServers -NotePropertyValue @{{}} -Force
    }}
    
    $config.mcpServers.qianji = @{{
        command = $PYTHON_PATH
        args = @("-m", "qianji.mcp", "--server", $SERVER_URL)
        env = @{{ PYTHONIOENCODING = "utf-8" }}
        description = "Universal Browser Automation for AI"
    }}
    
    $config | ConvertTo-Json -Depth 10 | Set-Content $CLAUDE_CONFIG
    Write-Host "✅ Claude Desktop 配置完成: $CLAUDE_CONFIG" -ForegroundColor Green
}}

# 配置 Cursor
$CURSOR_CONFIG = "$env:APPDATA\\Cursor\\mcp.json"
if (Test-Path (Split-Path $CURSOR_CONFIG -Parent)) {{
    Write-Host "🎯 配置 Cursor..." -ForegroundColor Yellow
    
    $config = @{{}}
    if (Test-Path $CURSOR_CONFIG) {{
        $config = Get-Content $CURSOR_CONFIG | ConvertFrom-Json
    }}
    
    if (-not $config.mcpServers) {{
        $config | Add-Member -NotePropertyName mcpServers -NotePropertyValue @{{}} -Force
    }}
    
    $config.mcpServers.qianji = @{{
        command = $PYTHON_PATH
        args = @("-m", "qianji.mcp", "--server", $SERVER_URL)
        env = @{{ PYTHONIOENCODING = "utf-8" }}
        description = "Universal Browser Automation for AI"
    }}
    
    $config | ConvertTo-Json -Depth 10 | Set-Content $CURSOR_CONFIG
    Write-Host "✅ Cursor 配置完成: $CURSOR_CONFIG" -ForegroundColor Green
}}

# 配置 Windsurf
$WINDSURF_CONFIG = "$env:USERPROFILE\\.codeium\\windsurf\\mcp_config.json"
if (Test-Path (Split-Path $WINDSURF_CONFIG -Parent)) {{
    Write-Host "🎯 配置 Windsurf..." -ForegroundColor Yellow
    
    $config = @{{}}
    if (Test-Path $WINDSURF_CONFIG) {{
        $config = Get-Content $WINDSURF_CONFIG | ConvertFrom-Json
    }}
    
    if (-not $config.mcpServers) {{
        $config | Add-Member -NotePropertyName mcpServers -NotePropertyValue @{{}} -Force
    }}
    
    $config.mcpServers.qianji = @{{
        command = $PYTHON_PATH
        args = @("-m", "qianji.mcp", "--server", $SERVER_URL)
        env = @{{ PYTHONIOENCODING = "utf-8" }}
        description = "Universal Browser Automation for AI"
    }}
    
    $config | ConvertTo-Json -Depth 10 | Set-Content $WINDSURF_CONFIG
    Write-Host "✅ Windsurf 配置完成: $WINDSURF_CONFIG" -ForegroundColor Green
}}

Write-Host ""
Write-Host "🎉 MCP 配置完成！" -ForegroundColor Green
Write-Host "⚠️  请重启 IDE 以使配置生效" -ForegroundColor Yellow
Write-Host ""
Write-Host "📖 使用方法:" -ForegroundColor Cyan
Write-Host "   1. 启动 qianji-server: qianji-server"
Write-Host "   2. 在 IDE 中启用 qianji MCP 工具"
Write-Host "   3. 让 AI 使用浏览器自动化功能"
'''
        return script


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="qianji MCP 配置工具 - 一键配置 Claude, Cursor, Windsurf"
    )
    
    parser.add_argument(
        "--ide",
        choices=["claude", "cursor", "windsurf", "all"],
        default="all",
        help="要配置的 IDE (默认: all)"
    )
    
    parser.add_argument(
        "--server",
        default="http://localhost:18791",
        help="qianji 服务器地址 (默认: http://localhost:18791)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览配置，不实际写入"
    )
    
    parser.add_argument(
        "--generate-script",
        action="store_true",
        help="生成 Shell/PowerShell 配置脚本"
    )
    
    parser.add_argument(
        "--output",
        help="脚本输出路径"
    )
    
    args = parser.parse_args()
    
    setup = MCPSetup()
    
    if args.generate_script:
        # 生成配置脚本
        if platform.system() == "Windows":
            script = setup.generate_powershell_script(args.server)
            default_output = "setup-qianji-mcp.ps1"
        else:
            script = setup.generate_shell_script(args.server)
            default_output = "setup-qianji-mcp.sh"
        
        output_path = args.output or default_output
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(script)
        
        # 设置可执行权限 (Unix)
        if platform.system() != "Windows":
            os.chmod(output_path, 0o755)
        
        print(f"✅ 配置脚本已生成: {output_path}")
        print(f"\n运行方式:")
        if platform.system() == "Windows":
            print(f"   powershell -ExecutionPolicy Bypass -File {output_path}")
        else:
            print(f"   ./{output_path}")
        
        return
    
    # 配置 IDE
    if args.ide == "claude":
        print(setup.setup_claude(args.server, args.dry_run))
    elif args.ide == "cursor":
        print(setup.setup_cursor(args.server, args.dry_run))
    elif args.ide == "windsurf":
        print(setup.setup_windsurf(args.server, args.dry_run))
    else:  # all
        print(setup.setup_all(args.server, args.dry_run))


if __name__ == "__main__":
    main()
