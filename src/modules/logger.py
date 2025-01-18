import logging
from pathlib import Path

from config import config


class Logger:
    def __init__(self, log_path: str = None):
        """Initialize the logging configuration with separate handlers for business and logic logs."""
        self.log_path = Path(log_path or Path(config.LOG_DIR))
        if not self.log_path.exists():
            self.log_path.mkdir(parents=True)

        # Logic log setup
        logic_log_file = self.log_path / config.LOGIC_LOG_FILE
        logic_handler = logging.FileHandler(logic_log_file)
        logic_handler.setLevel(logging.DEBUG if config.DEBUG_MODE else logging.WARNING)
        logic_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        logic_handler.setFormatter(logic_formatter)
        self.logic_logger = logging.getLogger("logic")
        self.logic_logger.setLevel(logging.DEBUG if config.DEBUG_MODE else logging.WARNING)
        self.logic_logger.addHandler(logic_handler)

        # Business log setup (disabled if DEBUG_MODE is True)
        business_formatter = logging.Formatter("%(asctime)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
        self.business_logger = None
        self.log_business_event = lambda event: None
        if not config.DEBUG_MODE:
            business_log_file = self.log_path / config.BUSINESS_LOG_FILE
            business_handler = logging.FileHandler(business_log_file)
            business_handler.setLevel(logging.INFO)
            business_handler.setFormatter(business_formatter)
            self.business_logger = logging.getLogger("business")
            self.business_logger.setLevel(logging.INFO)
            self.business_logger.addHandler(business_handler)

            self.log_business_event = lambda event: self.business_logger.info(event)
            """Log business-related events. (disabled in debug mode)"""

        # Console log setup (for debugging)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if config.DEBUG_MODE else logging.INFO)
        console_formatter = logic_formatter if config.DEBUG_MODE else business_formatter
        console_handler.setFormatter(console_formatter)

        # Attach console handler to both loggers
        if config.DEBUG_MODE:
            self.logic_logger.addHandler(console_handler)
        else:
            self.business_logger.addHandler(console_handler)

    def log_logic_event(self, event: str, level: str):
        """Log a specific event with a given severity level."""
        level = level.upper()
        self.logic_logger = logging.getLogger("logic")
        if level == "INFO":
            self.logic_logger.info(event)
        elif level == "WARNING":
            self.logic_logger.warning(event)
        elif level == "ERROR":
            self.logic_logger.error(event)
        elif level == "DEBUG":
            self.logic_logger.debug(event)
        else:
            self.logic_logger.info(f"[UNDEFINED LEVEL] {event}")

    def log_event(self, event: str, level: str = "INFO"):
        """Common events."""
        self.log_business_event(event)
        self.log_logic_event(event, level)


