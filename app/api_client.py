import httpx
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_access_token, get_http_headers

from app.config import settings


async def api_get(path: str, params: dict | None = None) -> dict | list:
    async with _client(await _caller_token()) as client:
        response = await client.get(path, params=_present(params))

    if response.is_error:
        raise ToolError(f"gOGig API {response.status_code}: {_detail(response)}")
    return response.json()


async def api_post(path: str, body: dict | None = None) -> dict | list:
    async with _client(await _caller_token()) as client:
        response = await client.post(path, json=_present(body))

    if response.is_error:
        raise ToolError(f"gOGig API {response.status_code}: {_detail(response)}")
    return response.json()


# This server stores no long-lived credential of its own: every call carries the
# end user's token, so the API's guards scope the answer to what they may read.
def _client(authorization: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.api_base_url,
        headers={"Authorization": authorization},
        timeout=30.0,
    )


async def _caller_token() -> str:
    """
    Three ways a caller proves who they are, most specific first.

    Under OAuth the token the client holds is ours, not gOGig's, so it buys a
    lookup rather than being forwarded. The other two are for clients that
    cannot do the OAuth dance: a bearer token passed straight through (MCP
    Inspector), and a configured one (stdio, which has no request at all).
    """
    token = await _session_token()
    if token:
        return token

    # `authorization` is in FastMCP's default strip list, so it has to be asked
    # for by name — forwarding it to the API is the whole point here.
    headers = get_http_headers(include={"authorization"})
    forwarded = headers.get("authorization")
    if forwarded:
        return forwarded

    configured = _configured_token()
    if configured:
        return configured

    raise ToolError(
        "Not signed in — connect this server again and complete the gOGig "
        "login, or set GOGIG_TOKEN for a stdio client."
    )


async def _session_token() -> str | None:
    access = get_access_token()
    if access is None:
        return None

    from app.auth.gogig_client import GogigAuthError
    from app.auth.sessions import sessions

    try:
        gogig = await sessions.gogig_token(access.token)
    except GogigAuthError as error:  # a dead refresh must read as "sign in again"
        raise ToolError(f"Your gOGig session has ended: {error}")
    return f"Bearer {gogig}" if gogig else None


def _configured_token() -> str:
    raw = settings.token.strip()
    if not raw:
        return ""
    return raw if raw.lower().startswith("bearer ") else f"Bearer {raw}"


def _present(params: dict | None) -> dict:
    return {key: value for key, value in (params or {}).items() if value is not None}


def _detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text[:400]
    if isinstance(body, dict):
        return str(body.get("message") or body.get("detail") or body)[:400]
    return str(body)[:400]
