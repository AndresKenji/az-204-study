from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from src.database import Base

class Task(Base):
    __tablename__ = "task"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255),nullable=False )
    done = Column(Boolean, default=False, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))
    description = Column(String, nullable=True)
    creation_date = Column(Date, nullable=True)
    done_date = Column(Date, nullable=True)

    user = relationship("User", back_populates="tasks")



