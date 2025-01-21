from datetime import datetime
from pathlib import Path
from typing import Union, List, Dict

from src.modules import logger


class Validator:

    @staticmethod
    def validate_email_format(email: str) -> bool:
        """Validate the format of an email address using a simple regex."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def check_placeholders_all_exist(placeholders: set, replacement: set) -> bool:
        """Check if all placeholders in a template exist in a dictionary."""
        missing_fields = placeholders - replacement
        if missing_fields:
            logger.log_logic_event(f"Missing fields: {missing_fields}", "ERROR")
            return False
        return True

    @staticmethod
    def is_valid_structure(path: Union[str, Path]) -> bool:
        """
        Check if the directory satisfies the structure:
        """
        path = Path(path)
        if not path.is_dir():
            return False

        # Check if the date_level(first-level) subdirectory contains .json files
        if not any(schedule_file.suffix == ".json" for schedule_file in path.iterdir()):
            return False

        # Check campaign_level(second-level) subdirectories
        for campaign_level in path.iterdir():
            if not campaign_level.is_dir():
                continue

            #  Check if campaign_level subdirectory contains .yaml files
            if not any(templates_file.suffix == ".yaml" for templates_file in campaign_level.iterdir()):
                return False

        # Return True if all conditions are met
        return True

    @staticmethod
    def validate_start_times(schedule: List[Dict]) -> bool:
        """
        Validate the start times in a campaign schedule.

        Args:
            schedule (List[Dict]): A list of campaigns, each containing a "start_time" field.

        Returns:
            bool: True if all start times are valid, False otherwise.
        """
        try:
            if not schedule:
                raise ValueError("The schedule is empty.")

            current_time = datetime.now()

            for campaign in schedule:
                for index, sequence in enumerate(campaign["sequences"]):
                    sequence_time = datetime.fromisoformat(sequence["start_time"])

                    if index == 0:
                        # First sequence must start in the future
                        if sequence_time <= current_time:
                            logger.log_event(
                                f"Campaign: {campaign["campaign_id"]}, first sequence's start_time {sequence_time} is not in the future.",
                                "ERROR")
                            return False
                    else:
                        # Ensure current sequence starts after the previous one
                        previous_time = datetime.fromisoformat(campaign["sequences"][index - 1]["start_time"])
                        if sequence_time <= previous_time:
                            logger.log_event(
                                f"Campaign: {campaign["campaign_id"]}, sequence {index} starts at {sequence_time}, which is not after the previous sequence {previous_time}.")
                            return False

            return True

        except Exception as e:
            print(f"An error occurred during validation: {e}")
            return False
