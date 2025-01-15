import re
import logging
from urllib.parse import urlparse
from typing import Tuple, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def is_valid_group_link(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a Telegram group link.
    
    Args:
        url (str): The URL to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        # Basic URL validation
        if not url:
            return False, "URL cannot be empty"

        # Clean and normalize the URL
        url = url.strip().lower()

        # Check URL scheme
        if not url.startswith(('https://', 'http://', 't.me/')):
            return False, "URL must start with 'https://', 'http://', or 't.me/'"

        # Parse the URL
        parsed_url = urlparse(url if '://' in url else f'https://{url}')

        # Validate domain
        if parsed_url.netloc not in ['t.me', 'telegram.me']:
            return False, "URL must be from t.me or telegram.me domain"

        # Extract and validate path
        path = parsed_url.path.strip('/')
        
        # Handle private group links
        if path.startswith('joinchat/'):
            invite_code = path.split('/')[-1]
            if not re.match(r'^[a-zA-Z0-9_-]{16,}$', invite_code):
                return False, "Invalid private group invite code"
            return True, None

        # Validate public group username
        if not re.match(r'^[a-zA-Z0-9_]{5,32}$', path):
            return False, "Invalid public group username format"

        # Check for reserved words
        reserved_words = {
            'admin', 'support', 'telegram', 'abuse', 'contact', 
            'spam', 'scam', 'fake', 'official', 'help', 'bot',
            'service', 'security', 'verification'
        }
        
        if any(word in path.lower() for word in reserved_words):
            return False, "Username contains reserved word"

        # Security checks
        security_patterns = [
            (r'javascript:', 'JavaScript injection attempt detected'),
            (r'data:', 'Data URI not allowed'),
            (r'<.*?>', 'HTML tags not allowed'),
            (r'[\'";\\\{\}]', 'Special characters not allowed'),
            (r'file:', 'File protocol not allowed'),
            (r'about:', 'About protocol not allowed'),
            (r'vbscript:', 'VBScript not allowed')
        ]
        
        for pattern, error_msg in security_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                logger.warning(f"Security violation in URL: {error_msg}")
                return False, f"Security violation: {error_msg}"

        logger.info(f"Valid group link validated: {url}")
        return True, None

    except Exception as e:
        logger.error(f"Error validating URL {url}: {str(e)}")
        return False, "Error validating URL"

def is_valid_title(title: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a link title.
    
    Args:
        title (str): The title to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        # Basic title validation
        if not title:
            return False, "Title cannot be empty"

        # Clean the title
        title = title.strip()

        # Length validation
        if len(title) < 3:
            return False, "Title must be at least 3 characters long"
        if len(title) > 100:
            return False, "Title must not exceed 100 characters"

        # Character validation
        if re.search(r'[<>{}[\]\\/@#$%^&*()]', title):
            return False, "Title contains invalid characters"

        # Content validation
        spam_patterns = {
            r'\b(?:buy|sell|spam)\b': 'Commercial spam detected',
            r'\b(?:xxx|porn|adult)\b': 'Adult content not allowed',
            r'\b(?:hack|crack|cheat)\b': 'Malicious content detected',
            r'\b(?:free.*money|easy.*cash)\b': 'Suspicious promotional content',
            r'\b(?:bitcoin|crypto.*invest)\b': 'Cryptocurrency spam detected'
        }

        for pattern, error_msg in spam_patterns.items():
            if re.search(pattern, title, re.IGNORECASE):
                logger.warning(f"Spam detected in title: {error_msg}")
                return False, f"Invalid content: {error_msg}"

        logger.info(f"Valid title validated: {title}")
        return True, None

    except Exception as e:
        logger.error(f"Error validating title: {str(e)}")
        return False, "Error validating title"

def is_valid_message(message: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a message content.
    
    Args:
        message (str): The message to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        if not message:
            return False, "Message cannot be empty"

        # Length validation
        if len(message) > 4096:  # Telegram message limit
            return False, "Message exceeds maximum length of 4096 characters"

        # Security validation
        security_patterns = [
            (r'<script.*?>.*?</script>', 'Script tags not allowed'),
            (r'javascript:', 'JavaScript code not allowed'),
            (r'onclick|onload|onerror', 'Event handlers not allowed'),
            (r'data:.*?base64', 'Base64 data not allowed')
        ]

        for pattern, error_msg in security_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                logger.warning(f"Security violation in message: {error_msg}")
                return False, f"Security violation: {error_msg}"

        return True, None

    except Exception as e:
        logger.error(f"Error validating message: {str(e)}")
        return False, "Error validating message"

def sanitize_input(text: str) -> str:
    """
    Sanitize user input by removing potentially dangerous characters.
    
    Args:
        text (str): The text to sanitize
        
    Returns:
        str: Sanitized text
    """
    try:
        if not text:
            return ""

        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32)

        # Remove potentially dangerous characters
        text = re.sub(r'[<>{}[\]\\]', '', text)

        # Remove multiple spaces
        text = ' '.join(text.split())

        return text.strip()

    except Exception as e:
        logger.error(f"Error sanitizing input: {str(e)}")
        return ""