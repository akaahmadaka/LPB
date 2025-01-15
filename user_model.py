from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create base class for declarative models
Base = declarative_base()

class UserRole(enum.Enum):
    """Enumeration of possible user roles."""
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"

class UserStatus(enum.Enum):
    """Enumeration of possible user statuses."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"

class User(Base):
    """User model for storing Telegram user information."""
    __tablename__ = "users"

    # Primary key and identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # User information
    username = Column(String(32), unique=True, index=True)
    first_name = Column(String(64))
    last_name = Column(String(64))
    
    # Role and status management
    role = Column(String(20), default=UserRole.USER.value, nullable=False)
    status = Column(String(20), default=UserStatus.ACTIVE.value, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # User metrics
    contribution_score = Column(Integer, default=0)
    reputation = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    
    # Flags
    is_verified = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    
    # Relationship with links
    links = relationship(
        "Link",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __init__(self, user_id: int, username: str = None, 
                 first_name: str = None, last_name: str = None):
        """Initialize a new User instance."""
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.last_active = datetime.utcnow()

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    def update_last_active(self):
        """Update user's last active timestamp."""
        self.last_active = datetime.utcnow()
        logger.info(f"Updated last active time for user {self.user_id}")

    def update_contribution_score(self, points: int):
        """Update user's contribution score."""
        self.contribution_score += points
        logger.info(f"Updated contribution score for user {self.user_id}: {self.contribution_score}")

    def __repr__(self):
        """String representation of User."""
        return f"<User(id={self.user_id}, username='{self.username}', role='{self.role}')>"