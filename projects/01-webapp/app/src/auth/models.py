from sqlalchemy import Column, Integer, String, Boolean, Date
from sqlalchemy.orm import relationship
from src.database import Base


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    disabled = Column(Boolean, nullable=False, default=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    creation_date = Column(Date, nullable=False)
    disable_date = Column(Date, nullable=True)
    
    tasks = relationship("Task", back_populates="user")

