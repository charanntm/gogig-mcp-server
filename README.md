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

The server starts on `http://0.0.0.0:8000/mcp`.

## Configuration

Settings are read from environment variables prefixed with `GOGIG_`, or a `.env` file:

| Variable      | Default    | Description        |
| ------------- | ---------- | ------------------- |
| `GOGIG_HOST`  | `0.0.0.0`  | Bind host            |
| `GOGIG_PORT`  | `8000`     | Bind port            |
