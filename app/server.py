from fastmcp import FastMCP

from app.config import settings
from app.tools import (
    register_campaign_tools,
    register_report_tools,
    register_task_tools,
    register_user_tools,
)


def _auth():
    if not settings.auth_enabled:
        return None
    if not settings.auth_client_id:
        raise RuntimeError(
            "GOGIG_AUTH_ENABLED is on but GOGIG_AUTH_CLIENT_ID is unset: "
            "gOGig's login endpoints are client-gated and will refuse every attempt."
        )
    from app.auth.provider import GogigOAuthProvider

    return GogigOAuthProvider()


mcp = FastMCP(name="Gogig MCP Server", auth=_auth())

register_task_tools(mcp)
register_campaign_tools(mcp)
register_user_tools(mcp)
register_report_tools(mcp)
