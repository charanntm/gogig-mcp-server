import secrets
import time
from dataclasses import dataclass, field

from mcp.server.auth.provider import AuthorizationParams

from app.auth.gogig_client import GogigSession, renew

PENDING_LOGIN_TTL_SECONDS = 10 * 60

# A gOGig access token lasts 4h; renew a little early rather than racing it.
RENEW_SKEW_SECONDS = 60


@dataclass
class PendingLogin:
    """An authorization in flight: the client is waiting at the login page."""

    client_id: str
    params: AuthorizationParams
    created_at: float = field(default_factory=time.time)
    # Set once the first step succeeds, so the code step knows who to verify.
    identifier: str | None = None
    channel: str | None = None

    @property
    def expired(self) -> bool:
        return time.time() - self.created_at > PENDING_LOGIN_TTL_SECONDS


class SessionStore:
    """
    In-memory binding from the tokens WE issue to the gOGig session behind them.

    The access token an MCP client holds is ours, not gOGig's, so every tool
    call has to come back here to find the gOGig token to forward. Restarting
    the server drops every session and clients sign in again.
    """

    def __init__(self) -> None:
        self._pending: dict[str, PendingLogin] = {}
        self._by_token: dict[str, GogigSession] = {}
        # Signed in, but the client has not redeemed its code yet.
        self._by_code: dict[str, GogigSession] = {}

    # ------------------------------------------------------------ pending ---

    def start_login(self, client_id: str, params: AuthorizationParams) -> str:
        self._sweep()
        txn = secrets.token_urlsafe(24)
        self._pending[txn] = PendingLogin(client_id=client_id, params=params)
        return txn

    def pending(self, txn: str) -> PendingLogin | None:
        login = self._pending.get(txn)
        if login is None:
            return None
        if login.expired:
            self._pending.pop(txn, None)
            return None
        return login

    def finish_login(self, txn: str) -> PendingLogin | None:
        login = self.pending(txn)
        if login is not None:
            self._pending.pop(txn, None)
        return login

    # --------------------------------------------------------------- code ---

    def hold_for_code(self, code: str, session: GogigSession) -> None:
        """Park a signed-in session until its authorization code is redeemed."""
        self._by_code[code] = session

    def finish_code(self, code: str) -> GogigSession | None:
        return self._by_code.pop(code, None)

    # ------------------------------------------------------------ sessions ---

    def bind(self, token: str, session: GogigSession) -> None:
        self._by_token[token] = session

    def rebind(self, old_token: str, new_token: str) -> GogigSession | None:
        """Carry a session across token rotation on refresh."""
        session = self._by_token.pop(old_token, None)
        if session is not None:
            self._by_token[new_token] = session
        return session

    def forget(self, token: str) -> None:
        self._by_token.pop(token, None)

    async def gogig_token(self, token: str) -> str | None:
        """The gOGig access token for one of our tokens, renewed if it is stale."""
        session = self._by_token.get(token)
        if session is None:
            return None

        if session.expires_at and session.expires_at - RENEW_SKEW_SECONDS <= time.time():
            session = await renew(session)
            self._by_token[token] = session
        return session.access_token

    def user_id(self, token: str) -> str | None:
        session = self._by_token.get(token)
        return session.user_id if session else None

    def _sweep(self) -> None:
        for txn in [txn for txn, login in self._pending.items() if login.expired]:
            self._pending.pop(txn, None)


sessions = SessionStore()
