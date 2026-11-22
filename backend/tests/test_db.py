from sqlalchemy import inspect
from sqlmodel import SQLModel, create_engine
import app.models  # noqa: F401


def test_db_models_in_memory():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    expected_tables = {
        "workers",
        "attempts",
        "witness_invites",
        "vouches",
        "credentials",
        "audit_log",
    }

    assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"
