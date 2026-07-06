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
        existing_columns = set()
    else:
        existing_columns = {column["name"] for column in inspector.get_columns("clinical_events")}
    clinical_event_additions = {
        "deferred_at": "DATETIME",
        "deferred_until": "DATETIME",
        "escalated_at": "DATETIME",
        "escalation_reason": "VARCHAR(255)",
    }
    with engine.begin() as connection:
        for column_name, column_type in clinical_event_additions.items():
            if existing_columns and column_name not in existing_columns:
                connection.execute(text(f"ALTER TABLE clinical_events ADD COLUMN {column_name} {column_type}"))
        if "import_batches" not in inspector.get_table_names():
            connection.execute(
                text(
                    """
                    CREATE TABLE import_batches (
                        id INTEGER NOT NULL,
                        import_kind VARCHAR(32) NOT NULL,
                        source_filename VARCHAR(255) NOT NULL,
                        schema_version VARCHAR(32) NOT NULL,
                        status VARCHAR(32) NOT NULL,
                        rows_received INTEGER NOT NULL,
                        records_created INTEGER NOT NULL,
                        duplicates_skipped INTEGER NOT NULL,
                        errors_json TEXT NOT NULL,
                        created_at DATETIME NOT NULL,
                        PRIMARY KEY (id)
                    )
                    """
                )
            )
            connection.execute(text("CREATE INDEX ix_import_batches_id ON import_batches (id)"))
            connection.execute(text("CREATE INDEX ix_import_batches_import_kind ON import_batches (import_kind)"))
            connection.execute(text("CREATE INDEX ix_import_batches_status ON import_batches (status)"))
            connection.execute(text("CREATE INDEX ix_import_batches_created_at ON import_batches (created_at)"))
