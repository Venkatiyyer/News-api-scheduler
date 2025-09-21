import logging
import sys

# Create a logger
logger = logging.getLogger("news_api")
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
console_handler.setFormatter(formatter)

# Add handler
logger.addHandler(console_handler)
