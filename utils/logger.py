import logging
import sys
from logging.handlers import RotatingFileHandler

# Configure logging with UTF-8 support and log rotation
log_handler = RotatingFileHandler("trading_bot.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler, console_handler]
)

logger = logging.getLogger(__name__)

# Example usage
logger.debug("This is a debug message")
logger.info("Logging system initialized successfully")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical error message")