"""Проверка сервера без Claude: запускаем server.py как подпроцесс и вызываем инструменты."""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

from mcp import Client, StdioServerParameters

SERVER = Path(__file__).parent / "server.py"


async def main() -> None:
    db_path = Path(tempfile.mkdtemp()) / "test.db"  # отдельная база, чтобы не трогать рабочую
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
        env={**os.environ, "CRM_DB_PATH": str(db_path)},
    )
    async with Client(params) as client:
        tools = await client.list_tools()
        print("Инструменты:", [t.name for t in tools.tools])

        r = await client.call_tool("add_lead", {"name": "Олена", "phone": "+380000000000",
                                                "message": "Чи є мигдаль у наявності?"})
        print("add_lead ->", r.structured_content)

        r = await client.call_tool("update_status", {"lead_id": 1, "status": "in_progress"})
        print("update_status ->", r.structured_content)

        r = await client.call_tool("update_status", {"lead_id": 999, "status": "done"})
        print("несуществующая заявка ->", r.is_error, r.content[0].text)

        r = await client.call_tool("list_leads", {})
        print("list_leads ->", r.structured_content)

        res = await client.read_resource("crm://stats")
        print("crm://stats ->", res.contents[0].text)

        prompts = await client.list_prompts()
        print("Промпты:", [p.name for p in prompts.prompts])


asyncio.run(main())
