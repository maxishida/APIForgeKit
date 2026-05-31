from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Iterator

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from core.config import get_settings
from core.models import Base, LeadTest


def build_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_settings().database_url
    connect_args = {"connect_timeout": 2} if url.startswith("postgresql") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def database_status(engine: Engine) -> dict[str, object]:
    start = perf_counter()
    try:
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
            total = session.scalar(select(func.count()).select_from(LeadTest)) or 0
            last_record = session.scalar(select(func.max(LeadTest.created_at)))
        latency = round((perf_counter() - start) * 1000, 2)
        return {
            "online": True,
            "latency_ms": latency,
            "record_count": int(total),
            "last_record": last_record.isoformat() if last_record else "Sem registros",
            "error": None,
        }
    except SQLAlchemyError as exc:
        latency = round((perf_counter() - start) * 1000, 2)
        return {
            "online": False,
            "latency_ms": latency,
            "record_count": 0,
            "last_record": "Indisponível",
            "error": str(exc),
        }
