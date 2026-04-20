"""
File description: Utility module providing logging functionalities for parsing
Purpose: Ensures unified and standard logging formats across the parsing domain
How it works: Configures the root Python logger with a consistent timestamp and level format, returning a named logger instance
"""
import logging

def setup_logger(name: str = "app") -> logging.Logger:
    # Creates and configures a standardized logger instance
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(name)
