from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import logging
from .user_model import Base

logger = logging.getLogger(__name__)

class Link(Base):
    """Link model with voting users tracking"""
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    url = Column(String(255), nullable=False)
    clicks = Column(Integer, default=0)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    submit_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    score = Column(Float, default=0.0)
    # Store voter IDs as comma-separated string
    voter_ids = Column(String(1000), default='')
    
    # Relationship with User
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    user = relationship("User", back_populates="links")

    def __init__(self, title: str, url: str, user_id: int):
        """Initialize a new Link instance."""
        self.title = title
        self.url = url
        self.user_id = user_id
        self.submit_date = datetime.utcnow()
        self.voter_ids = ''
        self.upvotes = 0
        self.downvotes = 0
        self.score = 0.0
        self.clicks = 0

    def _get_voter_id_list(self):
        """Convert voter_ids string to list of integers"""
        if not self.voter_ids:
            return []
        return [int(id_) for id_ in self.voter_ids.split(',') if id_]

    def _save_voter_id_list(self, id_list):
        """Convert list of voter IDs to comma-separated string"""
        self.voter_ids = ','.join(str(id_) for id_ in id_list)

    def has_voter_voted(self, voter_id: int) -> bool:
        """Check if voter has already voted."""
        return str(voter_id) in self.voter_ids.split(',') if self.voter_ids else False

    def add_vote(self, voter_id: int, is_upvote: bool) -> bool:
        """Add a vote if voter hasn't voted before."""
        try:
            # Check if voter has already voted
            if self.has_voter_voted(voter_id):
                logger.info(f"Voter {voter_id} has already voted on link {self.id}")
                return False
                
            # Add voter ID
            current_voters = self._get_voter_id_list()
            current_voters.append(voter_id)
            self._save_voter_id_list(current_voters)
            
            # Update vote counts
            if is_upvote:
                self.upvotes += 1
            else:
                self.downvotes += 1
                
            self.calculate_score()
            logger.info(f"Vote added for link {self.id} by voter {voter_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding vote: {str(e)}")
            return False

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