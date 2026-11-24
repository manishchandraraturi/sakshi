import os
from pathlib import Path
from sqlmodel import SQLModel, Session, create_engine

# Ensure data folder exists
data_dir = Path("data")
if not data_dir.exists():
    os.makedirs(data_dir, exist_ok=True)

# Ensure backend/data folder exists if launched from repo root
backend_data_dir = Path(__file__).resolve().parent.parent / "data"
if not backend_data_dir.exists():
    os.makedirs(backend_data_dir, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/sakshi.db")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    # Ensure coaching_json column exists in legacy databases
    try:
        from sqlmodel import text
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE attempts ADD COLUMN coaching_json TEXT"))
            conn.commit()
    except Exception:
        pass


def get_session():
    with Session(engine) as session:
        yield session
