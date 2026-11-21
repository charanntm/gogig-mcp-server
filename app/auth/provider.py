import secrets
import time
from pathlib import Path

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    AuthorizeError,
    RefreshToken,
    TokenError,
    construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from starlette.requests import Request
from starlette.responses import (
    FileResponse,
    HTMLResponse,
    RedirectResponse,
    Response,
)
from starlette.routing import Route

from fastmcp.server.auth.auth import ClientRegistrationOptions, OAuthProvider

from app.auth import login_page
from app.auth.gogig_client import GogigAuthError, send_otp, verify_otp
from app.auth.sessions import sessions
from app.config import settings

LOGO_PATH = Path(__file__).with_name("gogig-logo.png")

AUTH_CODE_TTL_SECONDS = 5 * 60
ACCESS_TOKEN_TTL_SECONDS = 60 * 60


class GogigOAuthProvider(OAuthProvider):
    """
    An OAuth 2.1 authorization server fronting gOGig's own OTP login.

    FastMCP supplies the protocol: discovery metadata, PKCE, dynamic client
    registration, and the /authorize, /token and /register endpoints. What it
    has no opinion about is WHO the user is, so that part is here —
    `authorize` parks the request and sends the browser to our login page,
    and the page finishes the flow once gOGig has verified a one-time code.

    The access token a client ends up holding is OURS. The gOGig token behind
    it never leaves this process; `SessionStore` maps one to the other so a
    tool call can forward the right thing.
    """

    def __init__(self) -> None:
        super().__init__(
            base_url=settings.public_url,
            client_registration_options=ClientRegistrationOptions(enabled=True),
        )
        self._clients: dict[str, OAuthClientInformationFull] = {}
        self._codes: dict[str, AuthorizationCode] = {}
        self._access: dict[str, AccessToken] = {}
        self._refresh: dict[str, RefreshToken] = {}
        self._refresh_to_access: dict[str, str] = {}
        self._register_static_client()

    # --------------------------------------------------------- clients ---

    def _register_static_client(self) -> None:
        """
        Accept one client id that was configured by hand.

        Redirect URIs are an explicit allowlist rather than anything the caller
        sends: the authorization code is delivered to this address, so a
        permissive list here is an open redirect with a credential attached.
        """
        if not settings.oauth_client_id:
            return
        self._clients[settings.oauth_client_id] = OAuthClientInformationFull(
            client_id=settings.oauth_client_id,
            redirect_uris=settings.oauth_redirect_uri_list,  # type: ignore[arg-type]
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            # Public client: PKCE is what proves the exchange, not a secret.
            token_endpoint_auth_method="none",
            client_name="gogig-mcp-server",
        )

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        return self._clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        if client_info.client_id is None:
            raise ValueError("client_id is required for client registration")
        self._clients[client_info.client_id] = client_info

    # --------------------------------------------------------- authorize ---

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        if client.client_id is None:
            raise AuthorizeError(
                error="invalid_client", error_description="Client ID is required"
            )
        txn = sessions.start_login(client.client_id, params)
        return f"{settings.public_url.rstrip('/')}/login?txn={txn}"

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        code = self._codes.get(authorization_code)
        if code is None or code.client_id != client.client_id:
            return None
        if code.expires_at < time.time():
            self._codes.pop(authorization_code, None)
            return None
        return code

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        if authorization_code.code not in self._codes:
            raise TokenError("invalid_grant", "Authorization code already used")
        self._codes.pop(authorization_code.code, None)

        gogig = sessions.finish_code(authorization_code.code)
        if gogig is None:
            raise TokenError("invalid_grant", "That sign-in is no longer valid")

        return self._issue(
            client_id=authorization_code.client_id,
            scopes=authorization_code.scopes,
            bind=lambda token: sessions.bind(token, gogig),
        )

    # ----------------------------------------------------------- refresh ---

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        token = self._refresh.get(refresh_token)
        if token is None or token.client_id != client.client_id:
            return None
        return token

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        if not set(scopes).issubset(set(refresh_token.scopes)):
            raise TokenError("invalid_scope", "Requested scopes exceed the grant")

        previous_access = self._refresh_to_access.pop(refresh_token.token, None)
        self._refresh.pop(refresh_token.token, None)
        if previous_access:
            self._access.pop(previous_access, None)

        def rebind(token: str) -> None:
            if previous_access and sessions.rebind(previous_access, token) is None:
                raise TokenError("invalid_grant", "That session has ended")

        return self._issue(
            client_id=refresh_token.client_id,
            scopes=scopes or refresh_token.scopes,
            bind=rebind,
        )

    # ------------------------------------------------------------ tokens ---

    async def load_access_token(self, token: str) -> AccessToken | None:
        access = self._access.get(token)
        if access is None:
            return None
        if access.expires_at is not None and access.expires_at < time.time():
            self._access.pop(token, None)
            sessions.forget(token)
            return None
        return access

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        self._access.pop(token.token, None)
        self._refresh.pop(token.token, None)
        sessions.forget(token.token)

    def _issue(self, *, client_id: str, scopes: list[str], bind) -> OAuthToken:
        access_value = f"gogig_at_{secrets.token_urlsafe(32)}"
        refresh_value = f"gogig_rt_{secrets.token_urlsafe(32)}"
        expires_at = int(time.time() + ACCESS_TOKEN_TTL_SECONDS)

        bind(access_value)

        self._access[access_value] = AccessToken(
            token=access_value,
            client_id=client_id,
            scopes=scopes,
            expires_at=expires_at,
            subject=sessions.user_id(access_value),
        )
        self._refresh[refresh_value] = RefreshToken(
            token=refresh_value, client_id=client_id, scopes=scopes, expires_at=None
        )
        self._refresh_to_access[refresh_value] = access_value

        return OAuthToken(
            access_token=access_value,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_TTL_SECONDS,
            refresh_token=refresh_value,
            scope=" ".join(scopes),
        )

    # ------------------------------------------------------ login routes ---

    def get_routes(self, mcp_path: str | None = None) -> list[Route]:
        return [
            *super().get_routes(mcp_path),
            Route("/login", self._login_form, methods=["GET"]),
            Route("/login", self._login_submit, methods=["POST"]),
            Route("/login/verify", self._login_verify, methods=["POST"]),
            Route("/login/logo.png", self._logo, methods=["GET"]),
        ]

    async def _logo(self, request: Request) -> Response:
        return FileResponse(
            LOGO_PATH,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    async def _login_form(self, request: Request) -> Response:
        txn = request.query_params.get("txn", "")
        if sessions.pending(txn) is None:
            return HTMLResponse(login_page.expired_page(), status_code=400)
        return HTMLResponse(login_page.identifier_form(txn))

    async def _login_submit(self, request: Request) -> Response:
        form = await request.form()
        txn = str(form.get("txn", ""))
        identifier = str(form.get("identifier", "")).strip()

        login = sessions.pending(txn)
        if login is None:
            return HTMLResponse(login_page.expired_page(), status_code=400)
        if not identifier:
            return HTMLResponse(
                login_page.identifier_form(txn, "Enter a phone number or email."),
                status_code=400,
            )

        try:
            channel = await send_otp(identifier)
        except GogigAuthError as error:
            return HTMLResponse(
                login_page.identifier_form(txn, str(error)), status_code=400
            )

        login.identifier = identifier
        login.channel = channel
        return HTMLResponse(login_page.otp_form(txn, identifier, channel))

    async def _login_verify(self, request: Request) -> Response:
        form = await request.form()
        txn = str(form.get("txn", ""))
        otp = str(form.get("otp", "")).strip()

        login = sessions.pending(txn)
        if login is None or not login.identifier:
            return HTMLResponse(login_page.expired_page(), status_code=400)

        try:
            session = await verify_otp(login.identifier, otp)
        except GogigAuthError as error:
            return HTMLResponse(
                login_page.otp_form(
                    txn, login.identifier, login.channel or "phone", str(error)
                ),
                status_code=400,
            )

        sessions.finish_login(txn)
        params: AuthorizationParams = login.params
        code_value = f"gogig_ac_{secrets.token_urlsafe(24)}"
        self._codes[code_value] = AuthorizationCode(
            code=code_value,
            client_id=login.client_id,
            redirect_uri=params.redirect_uri,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
            scopes=params.scopes or [],
            expires_at=time.time() + AUTH_CODE_TTL_SECONDS,
            code_challenge=params.code_challenge,
        )
        sessions.hold_for_code(code_value, session)

        return RedirectResponse(
            construct_redirect_uri(
                str(params.redirect_uri), code=code_value, state=params.state
            ),
            status_code=302,
        )
