import logging
import os
from functools import wraps


# Logger setup
def initialize_logger(log_file: str = "app.log", log_level: int = logging.DEBUG):
    log_path = "../../logs"
    """Initialize the logging configuration."""
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    log_file_path = os.path.join(log_path, log_file)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()
        ]
    )


# Decorator for logging
def log_function_call(func):
    """Decorator to log function calls and their results."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Function {func.__name__} called with arguments {args} and kwargs {kwargs}")
        try:
            _result = func(*args, **kwargs)
            logging.info(f"Function {func.__name__} completed successfully. Result: {_result}")
            return _result
        except Exception as _e:
            logging.error(f"Function {func.__name__} raised an exception: {_e}", exc_info=True)
            raise

    return wrapper


def log_event(event: str, level: str = "INFO"):
    """Log a specific event with a given severity level."""
    level = level.upper()
    if level == "INFO":
        logging.info(event)
    elif level == "WARNING":
        logging.warning(event)
    elif level == "ERROR":
        logging.error(event)
    elif level == "DEBUG":
        logging.debug(event)
    else:
        logging.info(f"[UNDEFINED LEVEL] {event}")


# Example usage of the logger
if __name__ == "__main__":
    initialize_logger()

    # Log custom events
    log_event("Application started", "INFO")
    log_event("This is a debug message", "DEBUG")
    log_event("Warning: Disk space low", "WARNING")
    log_event("Critical error occurred", "ERROR")

    @log_function_call
    def add_function(a, b):
        """Add function to demonstrate logging."""
        return a + b
    result = add_function(5, 10)
    print(f"Result: {result}")

    @log_function_call
    def division_function(a, b):
        return a / b
    # Call the sample function
    try:
        result = division_function(5, 0)
        print(f"Result: {result}")
    except Exception as e:
        print(f"An error occurred: {e}")
