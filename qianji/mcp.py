"""
MCP (Model Context Protocol) 支持
让 qianji 可以被 Claude Desktop, Cursor 等工具使用
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

import httpx


class QianjiMCPServer:
    """MCP 服务器实现"""
    
    def __init__(self, base_url: str = "http://localhost:18791"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.tools = self._define_tools()
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """定义可用工具"""
        return [
            {
                "name": "browser_navigate",
                "description": "Navigate to a URL",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to navigate to"},
                        "targetId": {"type": "string", "description": "Target tab ID"},
                    },
                    "required": ["url"],
                },
            },
            {
                "name": "browser_snapshot",
                "description": "Get a snapshot of the current page with interactive elements",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "targetId": {"type": "string", "description": "Target tab ID"},
                    },
                },
            },
            {
                "name": "browser_click",
                "description": "Click an element by ref",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ref": {"type": "string", "description": "Element ref (e.g., e1)"},
                        "targetId": {"type": "string", "description": "Target tab ID"},
                        "doubleClick": {"type": "boolean", "description": "Double click"},
                    },
                    "required": ["ref"],
                },
            },
            {
                "name": "browser_fill",
                "description": "Fill a form field",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ref": {"type": "string", "description": "Element ref"},
                        "text": {"type": "string", "description": "Text to fill"},
                        "targetId": {"type": "string", "description": "Target tab ID"},
                    },
                    "required": ["ref", "text"],
                },
            },
            {
                "name": "browser_type",
                "description": "Type text into an element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ref": {"type": "string", "description": "Element ref"},
                        "text": {"type": "string", "description": "Text to type"},
                        "targetId": {"type": "string", "description": "Target tab ID"},
                        "submit": {"type": "boolean", "description": "Press Enter after typing"},
                    },
                    "required": ["ref", "text"],
                },
            },
            {
                "name": "browser_screenshot",
                "description": "Take a screenshot",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "targetId": {"type": "string", "description": "Target tab ID"},
                        "fullPage": {"type": "boolean", "description": "Full page screenshot"},
                    },
                },
            },
            {
                "name": "browser_evaluate",
                "description": "Execute JavaScript",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "script": {"type": "string", "description": "JavaScript code"},
                        "targetId": {"type": "string", "description": "Target tab ID"},
                    },
                    "required": ["script"],
                },
            },
        ]
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 MCP 请求"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                    },
                    "serverInfo": {
                        "name": "qianji",
                        "version": "2.0.0",
                    },
                },
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": self.tools,
                },
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            result = await self._call_tool(tool_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}",
                },
            }
    
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        try:
            if name == "browser_navigate":
                resp = await self.client.post(
                    f"{self.base_url}/navigate",
                    json=arguments
                )
                data = resp.json()
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Navigated to: {data.get('url')}\nTitle: {data.get('title')}",
                        }
                    ],
                }
            
            elif name == "browser_snapshot":
                resp = await self.client.post(
                    f"{self.base_url}/snapshot",
                    json=arguments
                )
                data = resp.json()
                interactive = data.get("interactive", "")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Page: {data.get('title')}\nURL: {data.get('url')}\n\nInteractive elements:\n{interactive}",
                        }
                    ],
                }
            
            elif name == "browser_click":
                resp = await self.client.post(
                    f"{self.base_url}/act/click",
                    json=arguments
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Clicked element: {arguments.get('ref')}",
                        }
                    ],
                }
            
            elif name == "browser_fill":
                resp = await self.client.post(
                    f"{self.base_url}/act/fill",
                    json=arguments
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Filled element: {arguments.get('ref')}",
                        }
                    ],
                }
            
            elif name == "browser_type":
                resp = await self.client.post(
                    f"{self.base_url}/act/type",
                    json=arguments
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Typed into element: {arguments.get('ref')}",
                        }
                    ],
                }
            
            elif name == "browser_screenshot":
                resp = await self.client.post(
                    f"{self.base_url}/screenshot",
                    json=arguments
                )
                data = resp.json()
                path = data.get("path")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Screenshot saved to: {path}",
                        }
                    ],
                }
            
            elif name == "browser_evaluate":
                resp = await self.client.post(
                    f"{self.base_url}/debug/evaluate",
                    json=arguments
                )
                data = resp.json()
                result = data.get("data", {}).get("result")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Result: {json.dumps(result, indent=2)}",
                        }
                    ],
                }
            
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Unknown tool: {name}",
                        }
                    ],
                    "isError": True,
                }
        
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}",
                    }
                ],
                "isError": True,
            }
    
    async def run(self):
        """运行 MCP 服务器 (STDIO 模式)"""
        print("qianji MCP server started", file=sys.stderr)
        
        while True:
            try:
                line = input()
                if not line:
                    continue
                
                request = json.loads(line)
                response = await self.handle_request(request)
                
                print(json.dumps(response), flush=True)
            
            except EOFError:
                break
            except json.JSONDecodeError as e:
                print(f"Invalid JSON: {e}", file=sys.stderr)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
        
        await self.client.aclose()


def main():
    """MCP 服务器入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="qianji MCP Server")
    parser.add_argument("--server", default="http://localhost:18791", help="qianji server URL")
    
    args = parser.parse_args()
    
    server = QianjiMCPServer(base_url=args.server)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
