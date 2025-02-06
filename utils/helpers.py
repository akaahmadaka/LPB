import re
from utils.logger import logger
from functools import wraps
from time import time
from typing import Callable, Any, Dict, Optional
from datetime import datetime, timedelta
from config import ADMINS

def is_admin(user_id: int) -> bool:
    """
    Check if a user is an admin with additional logging.

    Args:
        user_id (int): The user's Telegram ID

    Returns:
        bool: True if user is admin, False otherwise
    """
    try:
        admin_status = user_id in ADMINS
        if admin_status:
            logger.info(f"Admin action performed by user {user_id}")
        return admin_status
    except Exception as e:
        logger.error(f"Error checking admin status: {str(e)}")
        return False

def rate_limit(seconds: int) -> Callable:
    """
    Decorator to rate limit function calls per user.

    Args:
        seconds (int): Minimum seconds between function calls

    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        last_called: Dict[int, float] = {}

        @wraps(func)
        def wrapper(message: Any, *args: Any, **kwargs: Any) -> Any:
            user_id = message.from_user.id
            current_time = time()

            if user_id in last_called and current_time - last_called[user_id] < seconds:
                remaining = int(seconds - (current_time - last_called[user_id]))
                logger.warning(f"Rate limit hit for user {user_id} on {func.__name__}")
                return f"Please wait {remaining} seconds before trying again."

            last_called[user_id] = current_time
            return func(message, *args, **kwargs)

        return wrapper
    return decorator

def format_timestamp(timestamp: datetime) -> str:
    """
    Format a timestamp into a readable string.

    Args:
        timestamp (datetime): Timestamp to format

    Returns:
        str: Formatted timestamp string
    """
    try:
        return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception as e:
        logger.error(f"Error formatting timestamp: {str(e)}")
        return "Invalid timestamp"

def get_time_difference(timestamp: datetime) -> str:
    """
    Get a human-readable time difference from now.

    Args:
        timestamp (datetime): Timestamp to compare

    Returns:
        str: Human-readable time difference
    """
    try:
        now = datetime.utcnow()
        diff = now - timestamp

        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=30):
            days = diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return format_timestamp(timestamp)
    except Exception as e:
        logger.error(f"Error calculating time difference: {str(e)}")
        return "unknown time ago"

def sanitize_html(text: str) -> str:
    """
    Remove HTML tags from text.

    Args:
        text (str): Text to sanitize

    Returns:
        str: Sanitized text
    """
    try:
        return re.sub(r'<[^>]+>', '', text)
    except Exception as e:
        logger.error(f"Error sanitizing HTML: {str(e)}")
        return ""

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length.

    Args:
        text (str): Text to truncate
        max_length (int): Maximum length

    Returns:
        str: Truncated text
    """
    try:
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    except Exception as e:
        logger.error(f"Error truncating text: {str(e)}")
        return text

def format_number(number: int) -> str:
    """
    Format large numbers for display.

    Args:
        number (int): Number to format

    Returns:
        str: Formatted number string
    """
    try:
        if number < 1000:
            return str(number)
        elif number < 1000000:
            return f"{number/1000:.1f}K"
        else:
            return f"{number/1000000:.1f}M"
    except Exception as e:
        logger.error(f"Error formatting number: {str(e)}")
        return str(number)

def validate_username(username: str) -> bool:
    """
    Validate Telegram username format.

    Args:
        username (str): Username to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if not username:
            return False
        return bool(re.match(r'^[a-zA-Z0-9_]{5,32}$', username))
    except Exception as e:
        logger.error(f"Error validating username: {str(e)}")
        return False

def escape_markdown(text: str) -> str:
    """
    Escape special characters for Markdown formatting.

    Args:
        text (str): Text to escape

    Returns:
        str: Escaped text
    """
    try:
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        return ''.join(f'\\{c}' if c in escape_chars else c for c in text)
    except Exception as e:
        logger.error(f"Error escaping markdown: {str(e)}")
        return text
