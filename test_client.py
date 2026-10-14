"""Smoke test without Claude: start server.py as a subprocess and call its tools over stdio."""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

from mcp import Client, StdioServerParameters

SERVER = Path(__file__).parent / "server.py"


async def main() -> None:
    db_path = Path(tempfile.mkdtemp()) / "test.db"  # separate database, the real one is untouched
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
        env={**os.environ, "CRM_DB_PATH": str(db_path)},
    )
    async with Client(params) as client:
        tools = await client.list_tools()
        print("Tools:", [t.name for t in tools.tools])

        r = await client.call_tool("add_lead", {"name": "Olena", "phone": "+380000000000",
                                                "message": "Do you have almonds in stock?"})
        print("add_lead ->", r.structured_content)

        r = await client.call_tool("update_status", {"lead_id": 1, "status": "in_progress"})
        print("update_status ->", r.structured_content)

        r = await client.call_tool("update_status", {"lead_id": 999, "status": "done"})
        print("missing lead ->", r.is_error, r.content[0].text)

        r = await client.call_tool("list_leads", {})
        print("list_leads ->", r.structured_content)

        res = await client.read_resource("crm://stats")
        print("crm://stats ->", res.contents[0].text)

        prompts = await client.list_prompts()
        print("Prompts:", [p.name for p in prompts.prompts])


asyncio.run(main())
