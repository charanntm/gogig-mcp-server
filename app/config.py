from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="GOGIG_")

    host: str = "0.0.0.0"
    port: int = 8000
    transport: Literal["http", "stdio"] = "http"

    api_base_url: str = "http://localhost:8080"

    # Fallback credential for stdio, which has no request to read a header from.
    # Over http the caller's own Authorization header wins.
    token: str = ""

    # --- OAuth login -------------------------------------------------------
    # Off by default: without it the server still accepts a forwarded bearer
    # token or GOGIG_TOKEN, which is how Inspector and stdio clients work.
    auth_enabled: bool = True
    # Where clients reach this server; the OAuth metadata and the login page
    # are advertised under it, so it must be the externally visible URL.
    public_url: str = "http://localhost:8000"
    # The AuthClient row gOGig's login endpoints are gated on.
    auth_client_id: str = "mcp_gogig"
    # Must appear in that row's allowedUrls, or gOGig refuses the client.
    auth_origin: str = "http://localhost:8000"

    # A fixed OAuth client, for MCP clients configured with a client id by hand
    # rather than registering themselves. Registered clients live in memory, so
    # without this a restart invalidates whatever the client registered and it
    # is turned away until it registers again. Blank leaves only registration.
    oauth_client_id: str = ""
    oauth_redirect_uris: str = (
        "https://claude.ai/api/mcp/auth_callback,"
        "https://claude.com/api/mcp/auth_callback,"
        "http://localhost:6274/oauth/callback"
    )

    @property
    def oauth_redirect_uri_list(self) -> list[str]:
        return [uri.strip() for uri in self.oauth_redirect_uris.split(",") if uri.strip()]


settings = Settings()
