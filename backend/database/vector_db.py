
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Connection details for Vector DB (Port 5433)
# Fallback to defaults from docker-compose if env vars not set
DB_USER = os.getenv("VECTOR_DB_USER", "postgres")
DB_PASS = os.getenv("VECTOR_DB_PASSWORD", "postgres")
DB_HOST = os.getenv("VECTOR_DB_HOST", "localhost")
DB_PORT = os.getenv("VECTOR_DB_PORT", "5433")
DB_NAME = os.getenv("VECTOR_DB_NAME", "knowledge_graph")

VECTOR_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    VECTOR_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args={'client_encoding': 'utf8'}
)

VectorSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
VectorBase = declarative_base()

def get_vector_session():
    db = VectorSessionLocal()
    try:
        yield db
    finally:
        db.close()
