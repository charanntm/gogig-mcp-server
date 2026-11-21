from dataclasses import dataclass

import httpx

from app.config import settings

REFRESH_COOKIE = "refreshToken"


class GogigAuthError(Exception):
    """The gOGig auth service refused a step of the login."""


@dataclass
class GogigSession:
    """A signed-in gOGig user, as the auth service hands them back."""

    user_id: str
    access_token: str
    refresh_token: str | None
    expires_at: float | None


async def send_otp(identifier: str) -> str:
    """Start a login. Returns the channel gOGig used ("phone" or "email")."""
    payload = _identifier_payload(identifier)
    async with _client() as client:
        token = await _anonymous_token(client)
        response = await client.post(
            "/sendOtp",
            params={"clientId": settings.auth_client_id},
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
    body = _body(response)

    # A disabled account answers 200 with a statusCode in the body.
    if response.is_error or body.get("statusCode") == 403:
        raise GogigAuthError(
            _message(body, response, "Could not send the code"))
    return str(body.get("type") or "phone")


async def verify_otp(identifier: str, otp: str) -> GogigSession:
    payload = {**_identifier_payload(identifier), "otp": _otp_value(otp)}
    async with _client() as client:
        token = await _anonymous_token(client)
        response = await client.post(
            "/verifyOtp",
            params={"clientId": settings.auth_client_id},
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
    body = _body(response)

    if response.is_error:
        raise GogigAuthError(
            _message(body, response, "That code was not accepted"))
    # An account missing its other login detail gets a completion token, which
    # is not a session: the user has to finish signing up in the gOGig app.
    if "completionToken" in body:
        raise GogigAuthError(
            "This account still needs to be completed in the gOGig app before it can sign in here."
        )
    access_token = body.get("token")
    if not access_token:
        raise GogigAuthError(_message(body, response, "No token was issued"))

    return GogigSession(
        user_id=_subject(access_token),
        access_token=access_token,
        refresh_token=response.cookies.get(REFRESH_COOKIE),
        expires_at=_expiry(body.get("expiresAt")),
    )


async def renew(session: GogigSession) -> GogigSession:
    """A gOGig access token lasts 4h; the refresh cookie buys a new one."""
    if not session.refresh_token:
        raise GogigAuthError(
            "This session has no refresh token; sign in again.")

    async with _client() as client:
        response = await client.post(
            "/renewAccessToken",
            headers={"Cookie": f"{REFRESH_COOKIE}={session.refresh_token}"},
        )
    body = _body(response)

    if response.is_error or not body.get("token"):
        raise GogigAuthError(
            _message(body, response, "Could not renew the session"))

    return GogigSession(
        user_id=session.user_id,
        access_token=body["token"],
        # gOGig rotates the cookie on renewal when it chooses to; keep the old
        # one when it does not.
        refresh_token=response.cookies.get(
            REFRESH_COOKIE) or session.refresh_token,
        expires_at=_expiry(body.get("expiresAt")),
    )


# The login endpoints are client-gated: an anonymous token signed with this
# client's secret, and an Origin that the client's allowedUrls lists.
async def _anonymous_token(client: httpx.AsyncClient) -> str:
    response = await client.get(
        "/getAnonymousToken",
        params={"clientId": settings.auth_client_id},
        headers={"Origin": settings.auth_origin},
    )
    body = _body(response)
    if response.is_error or not body.get("token"):
        raise GogigAuthError(
            _message(body, response,
                     "This MCP server is not a registered gOGig client")
        )
    return body["token"]


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=settings.api_base_url, timeout=30.0)


# gOGig compares the code with `===` against an int column, so a string here
# is silently "wrong OTP" however correct the digits are.
def _otp_value(otp: str) -> int:
    digits = otp.strip()
    if not digits.isdigit():
        raise GogigAuthError("Enter the numeric code we sent you.")
    return int(digits)


def _identifier_payload(identifier: str) -> dict:
    value = identifier.strip()
    if "@" in value:
        return {"emailId": value}
    return {"phoneNumber": value}


def _body(response: httpx.Response) -> dict:
    try:
        body = response.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def _message(body: dict, response: httpx.Response, fallback: str) -> str:
    return str(body.get("message") or body.get("error") or fallback)


def _expiry(value: object) -> float | None:
    try:
        seconds = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    # gOGig reports this in milliseconds.
    return seconds / 1000 if seconds > 1e11 else seconds


def _subject(access_token: str) -> str:
    import base64
    import json

    try:
        payload = access_token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload))
    except (IndexError, ValueError):
        raise GogigAuthError("The token gOGig issued could not be read")
    subject = claims.get("sub")
    if not subject:
        raise GogigAuthError("The token gOGig issued carries no subject")
    return str(subject)
