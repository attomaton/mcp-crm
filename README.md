# mini-crm — MCP server for customer leads

An MCP server in Python (official `mcp` SDK v2) that gives an AI agent such as Claude Code access to a simple lead CRM stored in SQLite.

| Type | Name | What it does |
|---|---|---|
| Tool | `add_lead` | create a lead (name, phone, message) |
| Tool | `list_leads` | list leads, optionally filtered by status |
| Tool | `update_status` | change status: `new` / `in_progress` / `done` |
| Resource | `crm://stats` | number of leads in each status |
| Prompt | `daily_report` | template: "review today's new leads" |

## How it works

- Tool parameters and outputs are typed (type hints + a Pydantic model), so the SDK generates JSON schemas the agent can follow.
- Expected errors are raised as `ToolError`, so the agent sees a readable message (e.g. `Lead with id=999 not found`).
- All SQL queries are parameterized; status values are restricted with `Literal`.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\python.exe -m pip install -r requirements.txt
# macOS/Linux: .venv/bin/python -m pip install -r requirements.txt
```

## Test

```bash
python test_client.py      # calls every tool over stdio, no Claude needed
mcp dev server.py          # MCP Inspector in the browser (requires Node.js)
```

## Connect

**Claude Code**
```bash
claude mcp add --scope user --transport stdio mini-crm -- /full/path/.venv/bin/python /full/path/server.py
claude mcp list
```

**Codex** — `~/.codex/config.toml`
```toml
[mcp_servers.mini-crm]
command = "/full/path/.venv/bin/python"
args = ["/full/path/server.py"]
```

**Claude Desktop** — `claude_desktop_config.json`
```json
{
  "mcpServers": {
    "mini-crm": {
      "command": "/full/path/.venv/bin/python",
      "args": ["/full/path/server.py"]
    }
  }
}
```

On Windows the Python path is `C:\...\.venv\Scripts\python.exe`.

The database path can be set with the `CRM_DB_PATH` environment variable (default: `leads.db` next to `server.py`).

## License

MIT
