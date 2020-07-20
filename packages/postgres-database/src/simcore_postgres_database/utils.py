import sqlalchemy as sa
from sqlalchemy.engine import Engine
from yarl import URL

from .models.base import metadata


def build_url(
    *,
    database: str = "",
    user: str = "",
    password: str = "",
    host: str = "localhost",
    port: int = 5432,
    **_kwargs,
) -> URL:
    """
       Safe build pg url as 'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}'
    """
    dsn = URL.build(
        scheme="postgresql+psycopg2",
        user=user,
        password=password,
        host=host,
        port=port,
        path=f"/{database}",
    )
    # _kwargs allows expand on larger dicts without raising exceptions
    return dsn


def create_tables(dsn: URL):
    try:
        engine: Engine = sa.create_engine(str(dsn))
        metadata.create_all(engine)
    finally:
        engine.dispose()


def raise_if_not_responsive(dsn: URL, *, verbose=False):
    """ checks whether database is responsive, otherwise it throws exception"""
    try:
        engine: Engine = sa.create_engine(
            str(dsn), echo=verbose, echo_pool=verbose, pool_timeout=5
        )
        conn = engine.connect()
        conn.close()
    finally:
        engine.dispose()
