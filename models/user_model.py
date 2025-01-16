from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    """User model with credits and referral tracking."""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)  # Telegram user ID
    credits = Column(Integer, default=5)  # Initial 5 credits for new users
    referred_by = Column(Integer, nullable=True)  # Store who referred this user

    # Define the relationship to Link model
    links = relationship("Link", back_populates="user")

    def __repr__(self):
        """String representation of User."""
        return f"<User(user_id={self.user_id}, credits={self.credits})>"