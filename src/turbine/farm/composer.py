import logging
import os

logger = logging.getLogger(__name__)


def get_or_create_farm():
    """Initialize or get the farm"""
    farm_path = os.path.join(os.getcwd(), "farm")
    if not os.path.exists(farm_path):
        os.makedirs(farm_path, exist_ok=True)
        logger.info("Farm directory created.")
    else:
        logger.info("Farm directory already exists.")
    return farm_path
