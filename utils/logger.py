"""Logging configuration for the Discord bot."""
import logging
import sys

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Set up logging configuration."""
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Silence verbose third-party loggers
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('WDM').setLevel(logging.WARNING)
    logging.getLogger('yt_dlp').setLevel(logging.WARNING)
    
    return root_logger

