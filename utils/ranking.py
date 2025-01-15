import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from models.link_model import Link

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ranking.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RankingCalculator:
    """Class to handle link ranking calculations."""
    
    def __init__(self):
        # Ranking weights
        self.WEIGHTS = {
            'upvotes': 1.5,
            'downvotes': 1.0,
            'clicks': 0.8,
            'recent_bonus': 1.2,
            'verified_bonus': 1.3,
            'report_penalty': 0.7
        }
        
        # Time windows
        self.RECENT_WINDOW = timedelta(hours=24)
        self.TRENDING_WINDOW = timedelta(hours=6)

    def calculate_link_score(self, link: Link) -> float:
        """
        Calculate the score for a link based on various metrics.
        
        Args:
            link (Link): Link object to score
            
        Returns:
            float: Calculated score
        """
        try:
            # Base score from interactions
            base_score = (
                (link.upvotes * self.WEIGHTS['upvotes']) -
                (link.downvotes * self.WEIGHTS['downvotes']) +
                (link.clicks * self.WEIGHTS['clicks'])
            )

            # Apply time decay
            time_factor = self._calculate_time_factor(link.submission_time)
            score = base_score * time_factor

            # Apply bonuses and penalties
            if link.is_verified:
                score *= self.WEIGHTS['verified_bonus']
            
            if link.reported_count > 0:
                score *= (self.WEIGHTS['report_penalty'] ** link.reported_count)

            return max(score, 0)  # Ensure non-negative score
            
        except Exception as e:
            logger.error(f"Error calculating link score: {str(e)}")
            return 0.0

    def _calculate_time_factor(self, submission_time: datetime) -> float:
        """
        Calculate time decay factor for scoring.
        
        Args:
            submission_time (datetime): Time when link was submitted
            
        Returns:
            float: Time decay factor
        """
        try:
            age = datetime.utcnow() - submission_time
            
            # Recent content bonus
            if age <= self.RECENT_WINDOW:
                return self.WEIGHTS['recent_bonus']
            
            # Logarithmic decay after recent window
            days_old = age.total_seconds() / (24 * 3600)
            return 1.0 / (1 + days_old)
            
        except Exception as e:
            logger.error(f"Error calculating time factor: {str(e)}")
            return 1.0

    def get_trending_links(self, links: List[Link], limit: int = 10) -> List[Link]:
        """
        Get trending links based on recent activity.
        
        Args:
            links (List[Link]): List of links to analyze
            limit (int): Maximum number of links to return
            
        Returns:
            List[Link]: Sorted list of trending links
        """
        try:
            trending_threshold = datetime.utcnow() - self.TRENDING_WINDOW
            
            # Filter recent links
            recent_links = [
                link for link in links 
                if link.last_updated >= trending_threshold
            ]
            
            # Sort by score
            scored_links = [
                (link, self.calculate_link_score(link))
                for link in recent_links
            ]
            
            sorted_links = sorted(
                scored_links,
                key=lambda x: x[1],
                reverse=True
            )
            
            return [link for link, _ in sorted_links[:limit]]
            
        except Exception as e:
            logger.error(f"Error getting trending links: {str(e)}")
            return []

    def get_top_links(self, links: List[Link], 
                     time_window: Optional[timedelta] = None,
                     limit: int = 10) -> List[Link]:
        """
        Get top links within a time window.
        
        Args:
            links (List[Link]): List of links to analyze
            time_window (Optional[timedelta]): Time window to consider
            limit (int): Maximum number of links to return
            
        Returns:
            List[Link]: Sorted list of top links
        """
        try:
            if time_window:
                threshold = datetime.utcnow() - time_window
                filtered_links = [
                    link for link in links 
                    if link.submission_time >= threshold
                ]
            else:
                filtered_links = links

            # Sort by score
            scored_links = [
                (link, self.calculate_link_score(link))
                for link in filtered_links
            ]
            
            sorted_links = sorted(
                scored_links,
                key=lambda x: x[1],
                reverse=True
            )
            
            return [link for link, _ in sorted_links[:limit]]
            
        except Exception as e:
            logger.error(f"Error getting top links: {str(e)}")
            return []