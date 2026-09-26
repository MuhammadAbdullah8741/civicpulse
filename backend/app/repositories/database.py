import os
from functools import lru_cache

from sqlalchemy import URL, Engine, create_engine


def database_url() -> URL:
    return URL.create(
        drivername="postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ.get("POSTGRES_HOST", "database"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ["POSTGRES_DB"],
    )


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(
        database_url(),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        connect_args={"connect_timeout": 3},
    )

def check_database() -> None:
    from sqlalchemy import text

    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))


def close_database() -> None:
    if get_engine.cache_info().currsize:
        try:
            get_engine().dispose()
        finally:
            get_engine.cache_clear()
