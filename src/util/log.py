import os
import logging 
from rich.logging import RichHandler 
# Determine the root directory of the project. 
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(ROOT_DIR, "logs")

def setup_logger(name: str, file_path: str, level=logging.DEBUG, console_logging: bool = True) -> logging.Logger:
    """
    Sets up a logger with:
    - File logging (plain text, no color)
    - RichHandler for colored console output (optional)
    Only sets up handlers once per logger.

    Args:
        name (str): Logger name (usually module name).
        file_path (str): Log file name to store logs.
        level (int): Logging level (e.g., logging.INFO).
        console_logging (bool): Enable console output. Defaults to True.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding multiple handlers on repeated calls
    if not logger.handlers:
        os.makedirs(LOGS_DIR, exist_ok=True)

        # Setup file handler (logs to logs/<file_path>)
        log_file_path = os.path.join(LOGS_DIR, file_path)
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Setup rich console handler (colored, timestamped output) if enabled
        if console_logging:
            console_handler = RichHandler(
                rich_tracebacks=True,
                show_time=True,
                show_level=True,
                show_path=True
            )
            console_handler.setLevel(level)
            logger.addHandler(console_handler)

    return logger