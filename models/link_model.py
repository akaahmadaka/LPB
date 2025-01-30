from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from utils.logger import logger
from .user_model import Base


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
    # Add clicker_ids column
    clicker_ids = Column(String(1000), default='')

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
        self.clicker_ids = ''
        self.upvotes = 0
        self.downvotes = 0
        self.clicks = 0
        self.calculate_score()  # Initialize the score using the calculate_score method

    def is_expired(self) -> bool:
        """
        Check if the link has expired.

        Returns:
            bool: True if link has expired, False otherwise
        """
        try:
            current_time = datetime.utcnow()
            link_age = current_time - self.submit_date
            return link_age > timedelta(days=3)  # Use your configured cleanup_days
        except Exception as e:
            logger.error(f"Error checking link expiry: {str(e)}")
            return False

    def time_until_expiry(self) -> timedelta:
        """
        Calculate time remaining until link expires.

        Returns:
            timedelta: Time remaining until expiry
        """
        try:
            current_time = datetime.utcnow()
            link_age = current_time - self.submit_date
            cleanup_days = 3  # Get this from your config
            return max(timedelta(days=cleanup_days) - link_age, timedelta(0))
        except Exception as e:
            logger.error(f"Error calculating expiry time: {str(e)}")
            return timedelta(0)

    def _get_voter_id_list(self):
        """Convert voter_ids string to list of integers"""
        if not self.voter_ids:
            return []
        return [int(id_) for id_ in self.voter_ids.split(',') if id_]

    def _save_voter_id_list(self, id_list):
        """Convert list of voter IDs to comma-separated string"""
        self.voter_ids = ','.join(str(id_) for id_ in id_list)

    def _get_clicker_id_list(self):
        """Convert clicker_ids string to list of integers"""
        if not self.clicker_ids:
            return []
        return [int(id_) for id_ in self.clicker_ids.split(',') if id_]

    def _save_clicker_id_list(self, id_list):
        """Convert list of clicker IDs to comma-separated string"""
        self.clicker_ids = ','.join(str(id_) for id_ in id_list)

    def has_voter_voted(self, voter_id: int) -> bool:
        """Check if voter has already voted."""
        return str(voter_id) in self.voter_ids.split(',') if self.voter_ids else False

    def has_user_clicked(self, user_id: int) -> bool:
        """Check if user has already clicked."""
        return str(user_id) in self.clicker_ids.split(',') if self.clicker_ids else False

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

    def add_click(self, user_id: int) -> bool:
        """Add a click if user hasn't clicked before."""
        try:
            # Check if user has already clicked
            if self.has_user_clicked(user_id):
                logger.info(f"User {user_id} has already clicked on link {self.id}")
                return False

            # Add user ID to clickers
            current_clickers = self._get_clicker_id_list()
            current_clickers.append(user_id)
            self._save_clicker_id_list(current_clickers)

            # Increment click counter
            self.clicks += 1
            self.calculate_score()
            logger.info(f"Click added for link {self.id} by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding click: {str(e)}")
            return False

    def calculate_score(self) -> float:
        """Calculate link score with a base value."""
        base_score = 2.0  # Default base score for every link
        self.score = (
            base_score +
            (self.upvotes * 1.5) -
            (self.downvotes * 1.0) +
            (self.clicks * 0.5)
        )
        return self.score

    def __repr__(self):
        """String representation of Link."""
        return f"<Link(id={self.id}, title='{self.title}', clicks={self.clicks})>"
