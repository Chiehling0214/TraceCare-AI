from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


settings = get_settings()
engine = create_engine(settings.database_url, connect_args=_connect_args(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all() -> None:
    Base.metadata.create_all(bind=engine)
    run_additive_migrations()


def run_additive_migrations() -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "clinical_events" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("clinical_events")}
    additions = {
        "deferred_at": "DATETIME",
        "deferred_until": "DATETIME",
        "escalated_at": "DATETIME",
        "escalation_reason": "VARCHAR(255)",
    }
    with engine.begin() as connection:
        for column_name, column_type in additions.items():
            if column_name not in existing_columns:
                connection.execute(text(f"ALTER TABLE clinical_events ADD COLUMN {column_name} {column_type}"))
