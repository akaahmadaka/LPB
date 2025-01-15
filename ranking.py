# Import required modules
from datetime import datetime, timedelta

def calculate_link_score(link):
    """
    Calculate the score for a link based on clicks, upvotes, downvotes, and freshness.
    """
    # Weights for clicks, upvotes, and downvotes
    W1, W2, W3 = 0.3, 0.5, 0.7

    # Freshness bonus for links submitted in the last 24 hours
    if datetime.now() - link.submission_time <= timedelta(hours=24):
        freshness_bonus = 0.5
    else:
        freshness_bonus = 0

    # Calculate the score
    score = (link.clicks * W1) + (link.upvotes * W2) - (link.downvotes * W3) + freshness_bonus
    return score