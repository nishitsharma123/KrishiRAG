import sys
import logging
from backend.app.core.config import settings

def setup_logging() -> logging.Logger:
    logger = logging.getLogger("krishirag")
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers if reloaded
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

logger = setup_logging()
