import logging
import sys
from pythonjsonlogger import jsonlogger

def get_logger(name: str = "brisq") -> logging.Logger:
    logger = logging.getLogger(name)
    
    # Avoid duplicating handlers if already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        
        # Use python-json-logger to format all log messages as JSON strings
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%SZ'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
    return logger

logger = get_logger()
