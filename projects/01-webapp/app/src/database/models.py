from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base
from src.database.database import azdb


Base = declarative_base()

class Task(Base):
    __tablename__ = "task"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255),nullable=False )
    done = Column(Boolean, default=False, nullable=False)

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    full_name = Column(String, nullable=False)
    hased_password = Column(String, nullable=False)
    disabled = Column(Boolean, nullable=False, default=False)


Base.metadata.create_all(bind=azdb.engine)