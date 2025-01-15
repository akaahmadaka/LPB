from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import logging
from .user_model import Base

# Set up logging
logger = logging.getLogger(__name__)

class Link(Base):
    """Link model for storing Telegram group links."""
    __tablename__ = "links"

    # Primary key and basic info
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False, index=True)
    url = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    
    # Metrics
    clicks = Column(Integer, default=0)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    views = Column(Integer, default=0)
    reported_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_checked = Column(DateTime)
    last_clicked = Column(DateTime)
    
    # Status flags
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False, index=True)
    is_featured = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    
    # Moderation
    moderator_note = Column(String(500))
    category = Column(String(50), index=True)
    tags = Column(String(200))
    
    # Relationship with User
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    user = relationship("User", back_populates="links")

    def __init__(self, title: str, url: str, user_id: int, description: str = None):
        """Initialize a new Link instance."""
        self.title = title
        self.url = url
        self.user_id = user_id
        self.description = description
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def increment_clicks(self):
        """Increment click counter and update timestamp."""
        self.clicks += 1
        self.last_clicked = datetime.utcnow()
        logger.info(f"Clicks incremented for link {self.id}: {self.clicks}")

    def increment_upvotes(self):
        """Increment upvote counter."""
        self.upvotes += 1
        logger.info(f"Upvotes incremented for link {self.id}: {self.upvotes}")

    def increment_downvotes(self):
        """Increment downvote counter."""
        self.downvotes += 1
        logger.info(f"Downvotes incremented for link {self.id}: {self.downvotes}")

    def report(self):
        """Increment report counter."""
        self.reported_count += 1
        logger.warning(f"Link {self.id} reported. Total reports: {self.reported_count}")

    def toggle_status(self, status: bool):
        """Toggle link active status."""
        self.is_active = status
        logger.info(f"Link {self.id} {'activated' if status else 'deactivated'}")

    def calculate_score(self) -> float:
        """Calculate link score based on metrics."""
        score = (
            (self.upvotes * 1.5) -
            (self.downvotes * 1.0) +
            (self.clicks * 0.5)
        )
        return max(0, score)

    def __repr__(self):
        """String representation of Link."""
        return f"<Link(id={self.id}, title='{self.title}', clicks={self.clicks})>"