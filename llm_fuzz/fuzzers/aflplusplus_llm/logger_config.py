import logging
import os
from datetime import datetime

log_dir = "/logs"
os.makedirs(log_dir, exist_ok=True)

log_filename = os.path.join(log_dir, "mutation_logs.txt")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode='a'), 
        logging.StreamHandler()  # Print logs to console
    ]
)

def get_logger(name=__name__):
    """Returns the configured logger."""
    return logging.getLogger(name)