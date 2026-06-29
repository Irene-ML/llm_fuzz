import logging
import os
from datetime import datetime

log_dir = "/logs"
os.makedirs(log_dir, exist_ok=True)

log_filename = os.path.join(log_dir, "mutation_logs.txt")

file_handler = logging.FileHandler(log_filename, mode='a')

# Force instant disk writes on every single log call
original_emit = file_handler.emit
def emit_and_flush(record):
    original_emit(record)
    file_handler.flush()
file_handler.emit = emit_and_flush

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        file_handler,
        logging.StreamHandler()  # Print logs to console
    ]
)

def get_logger(name=__name__):
    """Returns the configured logger."""
    return logging.getLogger(name)