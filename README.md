# Gogig MCP Server

An MCP server built with [FastMCP](https://gofastmcp.com).

## Setup

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Run

```bash
uv run python -m app.main
```

The server starts on `http://0.0.0.0:8100/mcp`.

## Configuration

Settings are read from environment variables prefixed with `GOGIG_`, or a `.env` file:

| Variable          | Default                 | Description                          |
| ----------------- | ----------------------- | ------------------------------------- |
| `GOGIG_HOST`      | `0.0.0.0`               | Bind host                             |
| `GOGIG_PORT`      | `8100`                  | Bind port                             |
| `GOGIG_API_BASE_URL` | `http://localhost:8000` | Base URL of the gogig-detections API |
| `GOGIG_API_KEY`   | (empty)                 | Sent as `X-API-Key` to the gogig-detections API |

## Tools

### Tasks

Backed by the [gogig-detections](../gogig-detections) API.

- `get_task_details(task_id)` — task images and per-action run state (`GET /actions/api/task`)
- `get_task_status(task_id)` — per-action status summary (`GET /post-task-processing/status`)
- `trigger_task_processing(task_id, actions, sync=False)` — run detection actions for a task (`POST /post-task-processing`)
