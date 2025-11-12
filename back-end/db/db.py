import os
from sqlmodel import create_engine, Session
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://appuser:supersecret@localhost:5432/appdb")
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# conveniente helper se usi FastAPI Depends
def get_session():
    with Session(engine) as session:
        yield session
