import logging
from pathlib import Path
from functools import wraps
from config import config

# Logger setup with dual storage
def initialize_logger(log_path: str = None):
    """Initialize the logging configuration with separate handlers for business and logic logs."""
    log_path = Path(log_path) or Path(config.LOG_DIR)
    if not log_path.exists():
        log_path.mkdir(parents=True)

    # Business log setup
    business_log_file = log_path / config.BUSINESS_LOG_FILE
    business_handler = logging.FileHandler(business_log_file)
    business_handler.setLevel(logging.INFO)
    business_formatter = logging.Formatter("%(asctime)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
    business_handler.setFormatter(business_formatter)
    business_logger = logging.getLogger("business")
    business_logger.setLevel(logging.INFO)
    business_logger.addHandler(business_handler)

    # Logic log setup
    logic_log_file = log_path / config.LOGIC_LOG_FILE
    logic_handler = logging.FileHandler(logic_log_file)
    logic_handler.setLevel(logging.DEBUG if config.DEBUG_MODE else logging.WARNING)
    logic_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    logic_handler.setFormatter(logic_formatter)
    logic_logger = logging.getLogger("logic")
    logic_logger.setLevel(logging.DEBUG if config.DEBUG_MODE else logging.WARNING)
    logic_logger.addHandler(logic_handler)

    # Console log setup (for debugging)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if config.DEBUG_MODE else logging.INFO)
    console_formatter = logic_formatter if config.DEBUG_MODE else business_formatter
    console_handler.setFormatter(console_formatter)

    # Attach console handler to both loggers
    business_logger.addHandler(console_handler)
    logic_logger.addHandler(console_handler)

def log_event(event: str, level: str):
    """Log a specific event with a given severity level."""
    level = level.upper()
    logic_logger = logging.getLogger("logic")
    if level == "INFO":
        logic_logger.info(event)
    elif level == "WARNING":
        logic_logger.warning(event)
    elif level == "ERROR":
        logic_logger.error(event)
    elif level == "DEBUG":
        logic_logger.debug(event)
    else:
        logic_logger.info(f"[UNDEFINED LEVEL] {event}")

def log_business_event(event: str):
    """Log business-related events."""
    logging.getLogger("business").info(event)

# Decorator for logging
# def log_function_call(func):
#     """Decorator to log function calls and their results."""
#
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         logging.info(f"Function {func.__name__} called with arguments {args} and kwargs {kwargs}")
#         try:
#             _result = func(*args, **kwargs)
#             logging.info(f"Function {func.__name__} completed successfully. Result: {_result}")
#             return _result
#         except Exception as _e:
#             logging.error(f"Function {func.__name__} raised an exception: {_e}", exc_info=True)
#             raise
#
#     return wrapper

# Example usage of the logger

if __name__ == "__main__":
    initialize_logger('logs')

    # Log business events
    log_business_event("Application started")

    # Log custom events
    log_event("Application started", "INFO")
    log_event("This is a debug message", "DEBUG")
    log_event("Warning: Disk space low", "WARNING")
    log_event("Critical error occurred", "ERROR")

    # @log_function_call
    # def add_function(a, b):
    #     """Add function to demonstrate logging."""
    #     return a + b
    # result = add_function(5, 10)
    # print(f"Result: {result}")
    #
    # @log_function_call
    # def division_function(a, b):
    #     return a / b
    # # Call the sample function
    # try:
    #     result = division_function(5, 0)
    #     print(f"Result: {result}")
    # except Exception as e:
    #     print(f"An error occurred: {e}")
