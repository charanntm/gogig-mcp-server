from app.config import settings
from app.server import mcp


def main() -> None:
    mcp.run(transport="http", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
