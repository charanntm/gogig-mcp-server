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

| Variable             | Default                 | Description                             |
| -------------------- | ----------------------- | ---------------------------------------- |
| `GOGIG_HOST`         | `0.0.0.0`               | Bind host (http transport)               |
| `GOGIG_PORT`         | `8000`                  | Bind port (http transport)               |
| `GOGIG_TRANSPORT`    | `http`                  | `http` or `stdio`                        |
| `GOGIG_API_BASE_URL` | `http://localhost:8080` | Base URL of the gogig-api-nestjs API     |
| `GOGIG_TOKEN`        | (empty)                 | Fallback bearer token, for `stdio`       |
| `GOGIG_AUTH_ENABLED` | `false`                 | Turn on the OAuth login flow             |
| `GOGIG_AUTH_CLIENT_ID` | (empty)               | The `AuthClient.clientId` to log in as   |
| `GOGIG_PUBLIC_URL`   | `http://localhost:8000` | Externally visible URL of this server    |
| `GOGIG_AUTH_ORIGIN`  | `http://localhost:8000` | `Origin` sent to gOGig; must be in `allowedUrls` |
| `GOGIG_OAUTH_CLIENT_ID` | (empty)              | A fixed OAuth client id, for clients configured by hand |
| `GOGIG_OAUTH_REDIRECT_URIS` | claude.ai + Inspector callbacks | Allowlist for that client's `redirect_uri` |

## Authentication

Every tool call reaches the API as the **end user**, so the API's guards decide
what they may read. A call with no credential is refused. Three ways a caller
proves who they are, most specific first:

1. **OAuth login** (`GOGIG_AUTH_ENABLED=true`) — the client is sent to a login
   page, the user signs in with a one-time code, and the client receives an
   access token and a refresh token. See below.
2. **Forwarded bearer** — the caller's own `Authorization` header, passed
   straight through. This is what MCP Inspector does.
3. **`GOGIG_TOKEN`** — for stdio clients, which have no request to read a
   header from. Accepted with or without the `Bearer ` prefix.

Put `GOGIG_TOKEN` in `.env` (gitignored) or the MCP client's own `env` block —
never in source.

## OAuth login

FastMCP supplies the OAuth 2.1 protocol — discovery, PKCE, dynamic client
registration, `/authorize`, `/token`, `/register` — and this server supplies
the identity half: `/login` collects a phone number or email, gOGig sends a
one-time code, and `/login/verify` exchanges it for a gOGig session.

The access token a client holds is **ours**, not gOGig's. The gOGig token sits
behind it in memory and is forwarded on each tool call, renewed through gOGig's
`/renewAccessToken` when its 4-hour life runs out. Sessions are in memory, so
restarting the server signs everyone out.

### One-time setup

gOGig's login endpoints are client-gated, so this server needs an `AuthClient`
row whose `allowedUrls` contains its origin. `secret_key` is the JWT signing
secret for anonymous client tokens — generate a long random string:

```sql
INSERT INTO AuthClient (clientId, name, secret_key, allowedUrls)
VALUES ('mcp_gogig', 'gogig-mcp-server', '<long random secret>', 'http://localhost:8000');
```

Then:

```bash
GOGIG_AUTH_ENABLED=true
GOGIG_AUTH_CLIENT_ID=mcp_gogig
GOGIG_PUBLIC_URL=http://localhost:8000
GOGIG_AUTH_ORIGIN=http://localhost:8000
```

`GOGIG_PUBLIC_URL` is where clients reach this server — the OAuth metadata and
the login page are advertised under it, so it must be externally visible.
`GOGIG_AUTH_ORIGIN` is sent as the `Origin` header to gOGig and must appear in
that row's `allowedUrls`, or every login is refused.

Keep `mcp_gogig` out of `SINGLE_SESSION_CLIENT_IDS` unless you want signing in
here to end the user's other sessions.

### Two different "client ids"

Easy to conflate, and the error they produce looks the same:

- **`GOGIG_AUTH_CLIENT_ID`** — the `AuthClient` row above. How *this server*
  authenticates to gOGig's login API.
- **`GOGIG_OAUTH_CLIENT_ID`** — how an *MCP client* identifies itself to this
  server. Leave it blank and clients register themselves (DCR). Set it only
  when a client is configured with a client id by hand — note that registered
  clients are held in memory, so a restart turns a self-registered client away
  until it registers again, while a fixed one keeps working.

They may hold the same string, but they are checked by different systems.

## Claude Desktop

Add to `~/.config/Claude/claude_desktop_config.json`, keeping whatever keys are
already there:

```json
{
  "mcpServers": {
    "gogig-mcp-server": {
      "command": "/home/charan-t-m/.local/bin/uv",
      "args": [
        "--directory", "/home/charan-t-m/Devkernal/Gogig/gogig-mcp-server",
        "run", "python", "-m", "app.main"
      ],
      "env": {
        "GOGIG_TRANSPORT": "stdio",
        "GOGIG_API_BASE_URL": "http://localhost:8080",
        "GOGIG_TOKEN": "<your gOGig bearer token>"
      }
    }
  }
}
```

The API must be reachable at `GOGIG_API_BASE_URL`. Restart Claude Desktop
fully after editing.

## Tools

All tools are backed by the `mcp` module in
[gogig-api-nestjs](../gogig-api-nestjs) (`src/modules/mcp/`), scoped through
one `McpScopeService`: the whole team's work on campaigns the user leads,
their own work everywhere else, every campaign for a gOGig admin. Every tool
is a read except the two report tools below, which queue a real job and send
a real email — see [Reports](#reports).

### Tasks

- `get_task_summary(gig_id?, start_date?, end_date?)` — flagged / warned / clean counts and quality rates
- `list_tasks(gig_id?, validation?, start_date?, end_date?, page?, page_size?)` — the user's tasks, newest first
- `get_task_details(task_id)` — one task with its validation reasons and detector reads
- `get_task_flag_reasons(gig_id?, start_date?, end_date?)` — why work is being flagged, busiest reason first

### Campaigns

- `list_my_campaigns(page?, page_size?)` — the campaigns a `gig_id` may be set to
- `get_campaign_performance(gig_id?, start_date?, end_date?, page?, page_size?)` — delivery and quality per campaign

### Users

- `whoami(start_date?, end_date?)` — who the user is, how far they can see, and their own figures; worth calling first
- `list_team_members(gig_id?, start_date?, end_date?, page?, page_size?)` — the roster under them, idle members included
- `search_users(q, page?, page_size?)` — find a person by name; by email or phone too, for an admin
- `get_user_performance(gig_id?, start_date?, end_date?, page?, page_size?)` — per-person figures, busiest first
- `get_user_details(user_id?, start_date?, end_date?)` — one person's totals; omit `user_id` for the caller's own

`list_team_members` is **membership**-derived (who is mapped under you, even
with nothing submitted); `get_user_performance` is **work**-derived (whose
submissions you are reading, including people with no mapping at all). They
answer different questions and neither is a superset of the other.

### Reports

The one WRITE surface. Generating a report queues a real cloud job and emails
the result to the **caller's own account address** — never returned inline,
never sent anywhere else. Scoped to the product's own rule: brand, agency, or
admin; a plain executor is refused, same as the "Generate Report" button in
the console.

- `generate_campaign_report(gig_id, type, start_date?, end_date?, validation_reason?)` — `type` is `pdf` or `summary`; returns a `jobId` and a masked email address
- `get_report_status(gig_id, type)` — progress and the download link once ready; `null` until the worker picks the job up

To retry a failed job or refresh an expired download link, call
`generate_campaign_report` again — a fresh job re-signs the link.

### Reading the numbers

`flagged` is `taskValidation = 'error'` and `warned` is `'warn'`; severity is
resolved per campaign by the validation pipeline. Rates divide by **validated**
work only and are `null` until something has been validated — never 0.
`delivery` is `submitted / totalTaskToBeDone`, `null` without a target, and may
exceed 1. People are reported by name only — `emailId` and `phoneNumber` appear
only on a gOGig admin's answer, where identifying a specific person is the
point. Password, OTP and token columns are never read for anyone.
