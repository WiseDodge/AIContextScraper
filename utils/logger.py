"""Logging utility for AIContextScraper."""

import logging
from datetime import datetime, UTC
import os
from typing import Optional, Union
import traceback

class ScraperLogger:
    def __init__(self, output_dir: str):
        self.logger = logging.getLogger('AIContextScraper')
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(output_dir, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # File handler
        log_file = os.path.join(logs_dir, f'scraper_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str) -> None:
        """Log info level message."""
        self.logger.info(message)
    
    def error(self, message: str, exc_info: Union[Exception, bool, None] = None) -> None:
        """Log error level message with exception info.
        
        Args:
            message: The error message to log
            exc_info: Exception object, or True to include current exception info,
                     or None/False to exclude exception info
        """
        self.logger.error(message, exc_info=bool(exc_info))
    
    def warning(self, message: str) -> None:
        """Log warning level message."""
        self.logger.warning(message)
    
    def debug(self, message: str) -> None:
        """Log debug level message."""
        self.logger.debug(message)