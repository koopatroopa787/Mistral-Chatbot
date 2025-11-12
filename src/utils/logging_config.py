"""Logging configuration"""

import logging
from pathlib import Path
from datetime import datetime


def setup_logging(log_dir: Path = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging configuration

    Args:
        log_dir: Directory for log files (default: logs/)
        level: Logging level (default: INFO)

    Returns:
        Logger instance
    """
    if log_dir is None:
        log_dir = Path("logs")

    log_dir.mkdir(exist_ok=True)

    # Create log filename with timestamp
    log_file = log_dir / f"chatbot_{datetime.now().strftime('%Y%m%d')}.log"

    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger("universal_ai_chatbot")
    return logger
