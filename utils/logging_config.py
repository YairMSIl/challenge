"""Logging Configuration
====================

Configures logging for the entire project with color-coded output and appropriate log levels.

Public Components:
- get_logger(): Function to get a configured logger instance
- LOG_LEVELS: Dict mapping environment names to logging levels

Design Decisions:
- Uses colorlog for enhanced readability with color-coded output
- Configures both file and console handlers
- File logs contain more detailed information for debugging
- Console output is color-coded by log level for better visibility
- Default log level is INFO in production, DEBUG in development

Integration Notes:
- Import and use get_logger() to obtain a logger instance
- Configure log level via LOG_LEVEL environment variable
- Log files are created in the logs directory
"""

import os
import sys
import logging
import colorlog
from pathlib import Path

# Configure log levels for different environments
LOG_LEVELS = {
    'development': logging.DEBUG,
    'testing': logging.INFO,
    'production': logging.WARNING,
}

def setup_log_directory():
    """Create logs directory if it doesn't exist."""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    return log_dir

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a configured logger instance with color output.
    
    Args:
        name: The name for the logger. If None, returns the root logger.
        
    Returns:
        A configured logger instance with both file and console handlers.
    """
    # Create logger
    logger = logging.getLogger(name or 'root')
    if logger.handlers:  # Return if logger is already configured
        return logger
        
    # Determine log level from environment
    env = os.getenv('ENVIRONMENT', 'development').lower()
    log_level = os.getenv('LOG_LEVEL', LOG_LEVELS.get(env, logging.INFO))
    logger.setLevel(log_level)
    
    # Create console handler with color formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Color scheme for different log levels
    color_scheme = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
    
    # Create color formatter
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        log_colors=color_scheme,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # Create file handler
    log_dir = setup_log_directory()
    file_handler = logging.FileHandler(log_dir / 'app.log')
    file_handler.setLevel(log_level)
    
    # Create file formatter
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Create a default logger instance
logger = get_logger() 