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
    def validate_time_exceeded(input_time: datetime) -> bool:
        """Check if the input time has already passed."""
        if input_time <= datetime.now():
            return True
        return False

    @staticmethod
    def validate_stage_time_order(schedule: List[Dict]) -> bool:
        """Check if the stages are in ascending order."""
        try:
            if not schedule:
                raise ValueError("The schedule is empty.")

            for campaign in schedule:
                for sequence_index, sequence in enumerate(campaign["sequences"]):
                    sequence_time = datetime.fromisoformat(sequence["start_time"])

                    if sequence_index == 0:
                        continue

                    prev_sequence_time = datetime.fromisoformat(campaign["sequences"][sequence_index - 1]["start_time"])
                    if sequence_time <= prev_sequence_time:
                        logger.log_event(
                            f"Sequence {sequence_index + 1} of campaign: {campaign['campaign_id']} starts at {sequence_time}, which is not after the previous sequence at {prev_sequence_time}.",
                            "ERROR")
                        return False

            return True

        except Exception as e:
            print(f"An error occurred during validation: {e}")
            return False

    @staticmethod
    def filter_expired_campaign(schedule: List[Dict]) -> List[Dict]:
        """Filter out expired campaigns."""
        try:
            if not schedule:
                raise ValueError("The schedule is empty.")

            for campaign_index, campaign in enumerate(schedule.copy()):
                for sequence_index, rev_sequence in enumerate(reversed(campaign["sequences"])):
                    sequence_time = datetime.fromisoformat(rev_sequence["start_time"])

                    if sequence_index == 0:
                        # Check if the campaign has expired
                        if Validator.validate_time_exceeded(sequence_time):
                            logger.log_event(
                                f"Campaign: {campaign['campaign_id']} expired.",
                                "ERROR")
                            schedule.remove(campaign)
                            break
                    continue

            for campaign_index, campaign in enumerate(schedule.copy()):
                total_stage = len(campaign["sequences"])
                for sequence_index, sequence in enumerate(campaign["sequences"]):
                    sequence_time = datetime.fromisoformat(sequence["start_time"])
                    # Check if the stage has expired
                    if Validator.validate_time_exceeded(sequence_time):
                        logger.log_event(
                            f"Stage: {sequence_index + 1} of campaign: {campaign['campaign_id']} expired.",
                            "ERROR")
                        schedule[campaign_index]["sequences"][sequence_index]["start_time"] = "expired"

            return schedule

        except Exception as e:
            print(f"An error occurred during validation: {e}")
            return []

if __name__ == "__main__":
    # Test the email format validator
    # print(Validator.is_valid_structure("../../data/2025/Jan/16Thu"))
    # print(Validator.is_valid_structure("../../data/2025/Jan/17Fri"))
    # print(Validator.is_valid_structure("../../data/12-01-2025"))

    from src.modules import InputParser
    from config import config

    test_directory = Path("../../" + config.DATA_DIR)
    example_data = InputParser.load_schedule(test_directory / "2025/Jan/12Sun/schedule.json")
    print(example_data)
    print(Validator.validate_stage_time_order(example_data))
    print(Validator.filter_expired_campaign(example_data))
