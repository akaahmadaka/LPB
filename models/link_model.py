from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import logging
from .user_model import Base

logger = logging.getLogger(__name__)

class Link(Base):
    """Link model with only essential fields"""
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    url = Column(String(255), nullable=False)
    clicks = Column(Integer, default=0)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    submit_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    score = Column(Float, default=0.0)
    
    # Relationship with User
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    user = relationship("User", back_populates="links")

    def __init__(self, title: str, url: str, user_id: int):
        """Initialize a new Link instance."""
        self.title = title
        self.url = url
        self.user_id = user_id
        self.submit_date = datetime.utcnow()

    def increment_clicks(self):
        """Increment click counter."""
        self.clicks += 1
        logger.info(f"Clicks incremented for link {self.id}: {self.clicks}")

    def increment_upvotes(self):
        """Increment upvote counter."""
        self.upvotes += 1
        logger.info(f"Upvotes incremented for link {self.id}: {self.upvotes}")

    def increment_downvotes(self):
        """Increment downvote counter."""
        self.downvotes += 1
        logger.info(f"Downvotes incremented for link {self.id}: {self.downvotes}")

    def calculate_score(self) -> float:
        """Calculate link score based on metrics."""
        self.score = (
            (self.upvotes * 1.5) -
            (self.downvotes * 1.0) +
            (self.clicks * 0.5)
        )
        return self.score

    def __repr__(self):
        """String representation of Link."""
        return f"<Link(id={self.id}, title='{self.title}', clicks={self.clicks})>"