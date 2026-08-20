"""
VELES Database Connection.

PostgreSQL + SQLAlchemy.
"""

import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


DATABASE_ENVIRONMENT_VARIABLE = "VELES_DATABASE_URL"


def get_database_url() -> str:
    database_url = os.getenv(
        DATABASE_ENVIRONMENT_VARIABLE
    )

    if not database_url:
        raise RuntimeError(
            f"Required environment variable "
            f"{DATABASE_ENVIRONMENT_VARIABLE} is not configured."
        )

    return database_url


def create_database_engine():
    return create_engine(
        get_database_url(),
        echo=False
    )


def get_engine():
    """
    Create the database engine lazily.

    The engine must not be created during module import because
    VELES configuration/bootstrap may not have initialized the
    database environment variable yet.
    """

    return create_database_engine()


def get_session():
    """
    Create a new database session.

    The engine is resolved lazily so database configuration is
    available before the connection is created.
    """

    engine = get_engine()

    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    return SessionLocal()


def test_connection():
    """
    Test the database connection.

    Returns:
        Row containing SELECT 1 on success.
        None on failure.
    """

    try:
        engine = get_engine()

        with engine.connect() as connection:

            result = connection.execute(
                text("SELECT 1")
            )

            return result.fetchone()

    except Exception as error:

        print(
            "DATABASE ERROR:",
            error
        )

        return None