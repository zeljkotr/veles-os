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


engine = create_database_engine()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_session():

    return SessionLocal()


def test_connection():

    try:

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