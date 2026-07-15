from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def create_database_engine(database_url: str) -> Engine:
    options = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=options, pool_pre_ping=True)


engine = create_database_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def database_is_connected(target: Engine = engine) -> bool:
    try:
        with target.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def database_type(database_url: str) -> str:
    scheme = database_url.split(":", 1)[0].split("+", 1)[0]
    return {"sqlite": "SQLite", "postgresql": "PostgreSQL"}.get(scheme, scheme.title())
