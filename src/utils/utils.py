import json
import os
from datetime import datetime

class Utils:
    @staticmethod
    def load_json_file(file_path: str):
        """Load a JSON file and return its content."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format in {file_path}: {e}")

    @staticmethod
    def save_json_file(file_path: str, data):
        """Save data to a JSON file."""
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)


# def calculate_delay(start_time: str) -> int:
#     """Calculate the delay in seconds from now to the given start time."""
#     try:
#         start_datetime = datetime.fromisoformat(start_time)
#         delay = (start_datetime - datetime.now()).total_seconds()
#         return max(0, int(delay))
#     except ValueError as e:
#         raise ValueError(f"Invalid datetime format: {start_time}. Use ISO 8601 format.")