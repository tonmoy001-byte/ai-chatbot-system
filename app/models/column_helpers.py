"""SQLite/PostgreSQL compatible column helpers."""
import uuid as _uuid


def _get_db_url():
    """Lazy database URL detection."""
    try:
        from app.config import get_settings
        return get_settings().DATABASE_URL
    except Exception:
        return ""


def uuid_primary_key():
    """Return appropriate primary key column for the database."""
    from sqlalchemy import Column, String
    url = _get_db_url()
    if url.startswith("sqlite"):
        return Column(String(36), primary_key=True, default=lambda: str(_uuid.uuid4()))
    else:
        from sqlalchemy.dialects.postgresql import UUID
        return Column(UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)


def uuid_foreign_key(*args, **kwargs):
    """Return appropriate foreign key column for the database."""
    from sqlalchemy import Column, String
    url = _get_db_url()
    if url.startswith("sqlite"):
        return Column(String(36), *args, **kwargs)
    else:
        from sqlalchemy.dialects.postgresql import UUID
        return Column(UUID(as_uuid=True), *args, **kwargs)
