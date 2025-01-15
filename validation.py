# Import required modules
import re

def is_valid_group_link(url):
    """
    Validate a Telegram group link.
    Returns True if the link is valid, otherwise False.
    """
    # Regex pattern to match Telegram group links
    pattern = r"^(https?:\/\/)?t\.me\/[a-zA-Z0-9_]{5,32}$"

    # Check if the link matches the pattern
    if not re.match(pattern, url):
        return False

    # Reject links containing "bot" (bot links)
    if "bot" in url.lower():
        return False

    # Reject external links (non-Telegram links)
    if not url.startswith(("t.me/", "https://t.me/", "http://t.me/")):
        return False

    return True