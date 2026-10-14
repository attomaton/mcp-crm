# mini-crm — MCP-сервер для заявок клиентов

MCP-сервер на Python (официальный SDK `mcp` v2), который даёт AI-агенту (Claude, Codex и др.) доступ к простой CRM в SQLite.

| Тип | Имя | Что делает |
|---|---|---|
| Tool | `add_lead` | создать заявку (имя, телефон, сообщение) |
| Tool | `list_leads` | список заявок, фильтр по статусу |
| Tool | `update_status` | сменить статус: `new` / `in_progress` / `done` |
| Resource | `crm://stats` | сколько заявок в каждом статусе |
| Prompt | `daily_report` | шаблон «разбери новые заявки за день» |

## Установка

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Проверка

```bash
python test_client.py      # вызывает все инструменты без Claude
mcp dev server.py          # MCP Inspector в браузере (нужен Node.js)
```

## Подключение

**Claude Code**
```bash
claude mcp add --transport stdio mini-crm -- /полный/путь/.venv/bin/python /полный/путь/server.py
claude mcp list
```

**Codex** — `~/.codex/config.toml`
```toml
[mcp_servers.mini-crm]
command = "/полный/путь/.venv/bin/python"
args = ["/полный/путь/server.py"]
```

**Claude Desktop** — `claude_desktop_config.json`
```json
{
  "mcpServers": {
    "mini-crm": {
      "command": "/полный/путь/.venv/bin/python",
      "args": ["/полный/путь/server.py"]
    }
  }
}
```

На Windows путь к Python: `C:\\...\\.venv\\Scripts\\python.exe`.

Путь к базе можно задать переменной окружения `CRM_DB_PATH` (по умолчанию `leads.db` рядом с `server.py`).
