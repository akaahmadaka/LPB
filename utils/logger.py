import logging

def setup_logger(name='LPB'):
    """
    Set up a simple console-only logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Console handler only
    console_handler = logging.StreamHandler()
    
    # Create formatter and add it to handler
    log_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(log_format)
    
    # Add handler to the logger
    logger.addHandler(console_handler)
    
    return logger

# Create main logger instance
logger = setup_logger()