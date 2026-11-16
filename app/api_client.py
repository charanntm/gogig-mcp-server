import httpx

from app.config import settings


def get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.api_base_url,
        headers={"X-API-Key": settings.api_key},
        timeout=30.0,
    )
