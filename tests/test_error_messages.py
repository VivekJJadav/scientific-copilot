from sqlalchemy.exc import OperationalError

from app.api.error_messages import describe_runtime_error, is_database_connection_error


def test_describe_runtime_error_for_local_database_connection_refused():
    exc = OperationalError(
        "SELECT 1",
        {},
        ConnectionRefusedError("[Errno 61] Connection refused"),
    )

    message = describe_runtime_error(
        exc,
        "postgresql+asyncpg://postgres:postgres@localhost:5432/scientific_copilot",
    )

    assert "Database unavailable at localhost:5432." in message
    assert "docker compose up -d postgres" in message


def test_is_database_connection_error_for_asyncpg_oserror():
    exc = OSError(
        "Multiple exceptions: [Errno 61] Connect call failed ('::1', 5432, 0, 0), "
        "[Errno 61] Connect call failed ('127.0.0.1', 5432)"
    )

    assert is_database_connection_error(exc) is True
