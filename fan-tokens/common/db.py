import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from common.models import Base

engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///fan_tokens.db"))
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)
