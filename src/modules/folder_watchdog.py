from watchdog.events import FileSystemEventHandler
from src.modules import log_event
from src.utils import Validator
from pathlib import Path
from typing import Union

# Data folder monitoring processor
class DataFolderHandler(FileSystemEventHandler):
    def __init__(self, process_callback):
        self.process_callback = process_callback  # Methods for processing directories that meet the conditions

    def on_created(self, event):
        """Handle new file events"""
        event_path = Path(event.src_path)
        if not event.is_directory:
            log_event(f"New file detected: {event_path.resolve()}", "INFO")
            self.check_and_process(event_path)

    def check_and_process(self, file_path: Union[str, Path]):
        """Check the directory structure and process"""
        file_path = Path(file_path)
        if file_path.suffix == ".json" and Validator.is_valid_structure(file_path.parent):
            self.process_callback(file_path.parent)
            log_event(f"A new json file was detected {file_path.resolve()}, verifying the directory contents", "INFO")

        if file_path.suffix == ".yaml" and Validator.is_valid_structure(file_path.parent.parent):
            self.process_callback(file_path.parents[1])
            log_event(f"A new yaml file was detected {file_path.resolve()}, verifying the directory contents", "INFO")

        if file_path.suffix == ".csv" and Validator.is_valid_structure(file_path.parent.parent.parent):
            self.process_callback(file_path.parents[2])
            log_event(f"A new csv file was detected {file_path.resolve()}, verifying the directory contents", "INFO")

if __name__ == "__main__":
    from src.modules import InputParser
    # Process directories that meet the conditions
    def process_directory(path: Union[str, Path]):
        try:
            temp = InputParser.build_campaign_data(path)
            print(f"{temp}")
        except Exception as e:
            log_event(f"{e}", "ERROR")

    import time
    from watchdog.observers import Observer
    from src.modules import initialize_logger

    initialize_logger("../../logs", "folder_watchdog.log")
    # Directories to monitor
    monitor_dir = Path("../../data")

    # Creating an event handler
    observer = Observer()
    observer.schedule(DataFolderHandler(process_directory), path=str(monitor_dir), recursive=True)

    # Start the observer
    observer.start()
    print(f"Start monitoring the directory: {monitor_dir.resolve()}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
