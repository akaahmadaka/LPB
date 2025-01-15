from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import logging

logger = logging.getLogger(__name__)
Base = declarative_base()

class User(Base):
    """User model with only user_id"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Keep the relationship with links
    links = relationship(
        "Link",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __init__(self, user_id: int):
        """Initialize a new User instance."""
        self.user_id = user_id

    def __repr__(self):
        """String representation of User."""
        return f"<User(user_id={self.user_id})>"