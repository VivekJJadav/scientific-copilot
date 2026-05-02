from urllib.parse import urlparse

from sqlalchemy.exc import OperationalError


def is_database_connection_error(exc: Exception) -> bool:
    if isinstance(exc, OperationalError):
        return True

    message = str(exc).lower()
    return (
        ("connection refused" in message or "connect call failed" in message)
        and ("asyncpg" in message or "postgres" in message or "5432" in message)
    )


def describe_runtime_error(exc: Exception, database_url: str) -> str:
    if not is_database_connection_error(exc):
        return str(exc)

    parsed = urlparse(database_url.replace("+asyncpg", ""))
    host = parsed.hostname or "database"
    port = parsed.port or 5432

    if host in {"localhost", "127.0.0.1"}:
        return (
            f"Database unavailable at {host}:{port}. "
            "Start Postgres with `docker compose up -d postgres` and retry."
        )

    return f"Database unavailable at {host}:{port}. Ensure Postgres is running and retry."
