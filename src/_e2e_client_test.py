"""재부팅 전 사전검증용 임시 스크립트 — 실제 MCP stdio 프로토콜 경로로 서버를 검증한다.
(Claude Code 재시작 없이도, 진짜 MCP 클라이언트가 뭘 받는지 지금 확인 가능)
"""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = str(Path(__file__).with_name("server.py"))


async def main():
    params = StdioServerParameters(command=sys.executable, args=[SERVER])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print("=== initialize ===")
            print("server name:", init.server_info.name, "version:", init.server_info.version)

            tools = await session.list_tools()
            print("\n=== list_tools ===")
            for t in tools.tools:
                print(f"- {t.name}: {t.description[:60]!r}...")

            print("\n=== call_tool: list_windows ===")
            r = await session.call_tool("list_windows", {})
            print("isError:", r.is_error, "| content blocks:", len(r.content))
            print(r.content[0].text[:200], "...")

            print("\n=== call_tool: capture_screen ===")
            r = await session.call_tool("capture_screen", {})
            print("isError:", r.is_error, "| content blocks:", len(r.content))
            for block in r.content:
                print(" block type:", block.type, "| mimeType:", getattr(block, "mimeType", None))

            print("\n=== call_tool: capture_window (오프스크린, 에러 경로 재확인) ===")
            r = await session.call_tool("capture_window", {"title_contains": "VirtualBoxVM"})
            print("isError:", r.is_error)
            print(r.content[0].text)

            print("\n=== call_tool: read_log (화이트리스트 위반 경로) ===")
            r = await session.call_tool("read_log", {"name": "존재안함"})
            print("isError:", r.is_error)
            print(r.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
