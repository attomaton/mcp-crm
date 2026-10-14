"""Mini-CRM MCP server: заявки клиентов в SQLite.

Запуск (stdio, так его запускают Claude Code / Claude Desktop / Codex):
    python server.py

Проверка в браузере через MCP Inspector:
    mcp dev server.py
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

# Путь к базе можно переопределить переменной окружения CRM_DB_PATH
DB_PATH = Path(os.environ.get("CRM_DB_PATH", Path(__file__).parent / "leads.db"))

Status = Literal["new", "in_progress", "done"]


class Lead(BaseModel):
    """Модель заявки: из неё SDK строит JSON-схему ответа инструмента."""
    id: int
    name: str
    phone: str
    message: str
    status: Status
    created_at: str

mcp = MCPServer(
    "mini-crm",
    instructions="CRM с заявками клиентов магазина. Используй инструменты, "
    "чтобы добавлять заявки, смотреть их и менять статус.",
)


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL
        )"""
    )
    return conn


# ---------- Tools: действия, которые модель может вызвать ----------

@mcp.tool()
def add_lead(name: str, phone: str, message: str) -> Lead:
    """Создать новую заявку клиента. Возвращает созданную заявку."""
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO leads (name, phone, message, created_at) VALUES (?, ?, ?, ?)",
            (name, phone, message, datetime.now().isoformat(timespec="seconds")),
        )
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (cur.lastrowid,)).fetchone()
    return Lead(**dict(row))


@mcp.tool()
def list_leads(status: Status | None = None, limit: int = 20) -> list[Lead]:
    """Показать заявки. Можно отфильтровать по статусу: new, in_progress, done."""
    query, params = "SELECT * FROM leads", []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with db() as conn:
        return [Lead(**dict(r)) for r in conn.execute(query, params).fetchall()]


@mcp.tool()
def update_status(lead_id: int, status: Status) -> Lead:
    """Изменить статус заявки по её id."""
    with db() as conn:
        cur = conn.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
        if cur.rowcount == 0:
            # ToolError = ожидаемая ошибка: её текст увидит модель
            raise ToolError(f"Заявка с id={lead_id} не найдена")
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    return Lead(**dict(row))


# ---------- Resource: данные, которые клиент может прочитать ----------

@mcp.resource("crm://stats")
def stats() -> str:
    """Сколько заявок в каждом статусе."""
    with db() as conn:
        rows = conn.execute("SELECT status, COUNT(*) AS n FROM leads GROUP BY status").fetchall()
    return "\n".join(f"{r['status']}: {r['n']}" for r in rows) or "Заявок пока нет"


# ---------- Prompt: готовый шаблон запроса ----------

@mcp.prompt()
def daily_report() -> str:
    """Шаблон: отчёт по новым заявкам за день."""
    return (
        "Возьми все заявки со статусом new через list_leads, сгруппируй их по теме "
        "(цены, доставка, наличие, другое) и предложи, кому ответить первым."
    )


if __name__ == "__main__":
    # ВАЖНО для stdio: ничего не печатай в stdout через print() —
    # stdout занят протоколом. Логи пиши в stderr.
    mcp.run()  # по умолчанию transport="stdio"
