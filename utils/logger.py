import logging
import sys

# Configure logging with UTF-8 support
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("trading_bot.log", encoding="utf-8"),  # Save logs in UTF-8 format
        logging.StreamHandler(sys.stdout)  # Print logs to console
    ]
)

logger = logging.getLogger(__name__)
