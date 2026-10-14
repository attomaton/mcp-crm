"""Mini-CRM MCP server: customer leads stored in SQLite.

Run over stdio (this is how Claude Code / Claude Desktop / Codex start it):
    python server.py

Inspect it in the browser with MCP Inspector:
    mcp dev server.py
"""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

# The database path can be overridden with the CRM_DB_PATH environment variable
DB_PATH = Path(os.environ.get("CRM_DB_PATH", Path(__file__).parent / "leads.db"))

Status = Literal["new", "in_progress", "done"]


class Lead(BaseModel):
    """A customer lead. The SDK builds the tool's output JSON schema from this model."""

    id: int
    name: str
    phone: str
    message: str
    status: Status
    created_at: str


mcp = MCPServer(
    "mini-crm",
    instructions="CRM with customer leads of an online store. Use the tools "
    "to add leads, list them and change their status.",
)


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    """Open a connection, commit on success and always close it."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
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
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---------- Tools: actions the model can call ----------

@mcp.tool()
def add_lead(name: str, phone: str, message: str) -> Lead:
    """Create a new customer lead. Returns the created lead."""
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO leads (name, phone, message, created_at) VALUES (?, ?, ?, ?)",
            (name, phone, message, datetime.now().isoformat(timespec="seconds")),
        )
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (cur.lastrowid,)).fetchone()
    return Lead(**dict(row))


@mcp.tool()
def list_leads(status: Status | None = None, limit: int = 20) -> list[Lead]:
    """List leads, newest first. Optionally filter by status: new, in_progress, done."""
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
    """Change the status of a lead by its id."""
    with db() as conn:
        cur = conn.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
        if cur.rowcount == 0:
            # ToolError is an expected error: the model sees its message
            raise ToolError(f"Lead with id={lead_id} not found")
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    return Lead(**dict(row))


# ---------- Resource: data the client can read ----------

@mcp.resource("crm://stats")
def stats() -> str:
    """Number of leads in each status."""
    with db() as conn:
        rows = conn.execute("SELECT status, COUNT(*) AS n FROM leads GROUP BY status").fetchall()
    return "\n".join(f"{r['status']}: {r['n']}" for r in rows) or "No leads yet"


# ---------- Prompt: a ready-made request template ----------

@mcp.prompt()
def daily_report() -> str:
    """Template: a daily report on new leads."""
    return (
        "Get all leads with status new via list_leads, group them by topic "
        "(prices, delivery, availability, other) and suggest who to answer first."
    )


if __name__ == "__main__":
    # IMPORTANT for stdio: never print() to stdout,
    # stdout carries the protocol. Write logs to stderr.
    mcp.run()  # transport="stdio" by default
