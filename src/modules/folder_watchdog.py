from pathlib import Path
from typing import Union, Callable

from watchdog.events import FileSystemEventHandler

from src.modules import logger
from src.utils import Validator


# Data folder monitoring processor
class DataFolderHandler(FileSystemEventHandler):
    def __init__(self, process_callback: Callable, **kwargs):
        self.process_callback = process_callback  # Methods for processing directories that meet the conditions
        self.kwargs = kwargs # Campaign manager instance

    def on_created(self, event):
        """Handle new file events"""
        event_path = Path(event.src_path)
        if not event.is_directory:
            logger.log_logic_event(f"New file detected: {event_path.resolve()}", "INFO")
            self.check_and_process(event_path)

    def check_and_process(self, file_path: Union[str, Path]):
        """Check the directory structure and process"""
        file_path = Path(file_path)
        if file_path.suffix == ".json" and Validator.is_valid_structure(file_path.parent):
            self.process_callback(file_path.parent, **self.kwargs)
            logger.log_logic_event(f"A new json file was detected {file_path.resolve()}, verifying the directory contents", "INFO")

        if file_path.suffix == ".yaml" and Validator.is_valid_structure(file_path.parents[1]):
            self.process_callback(file_path.parents[1], **self.kwargs)
            logger.log_logic_event(f"A new yaml file was detected {file_path.resolve()}, verifying the directory contents", "INFO")

        if file_path.suffix == ".csv" and Validator.is_valid_structure(file_path.parents[2]):
            self.process_callback(file_path.parents[2], **self.kwargs)
            logger.log_logic_event(f"A new csv file was detected {file_path.resolve()}, verifying the directory contents", "INFO")


if __name__ == "__main__":
    import threading

    event = threading.Event()

    from src.modules import InputParser


    # Process directories that meet the conditions
    def process_directory(path: Union[str, Path], **kwargs):
        try:
            temp = InputParser.build_campaign_data(path)
            print(f"{temp}")
            print(kwargs)
            event.set()
        except Exception as e:
            log_event(f"{e}", "ERROR")


    from watchdog.observers import Observer

    # from src.modules import Logger

    # logger = Logger("../../logs")
    # Directories to monitor
    monitor_dir = Path("../../data")

    # Creating an event handler
    observer = Observer()
    observer.schedule(
        DataFolderHandler(process_directory, arg1="scheduler", arg2="email_sender"),
        path=str(monitor_dir),
        recursive=True
    )

    # Start the observer
    observer.start()
    print(f"Start monitoring the directory: {monitor_dir.resolve()}")

    try:
        while True:
            event.wait()
            print("Event is set")
            event.clear()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
