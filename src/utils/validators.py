from src.modules import log_event
from pathlib import Path
from typing import Union

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
            log_event(f"Missing fields: {missing_fields}", "ERROR")
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

if __name__ == "__main__":
    # Test the email format validator
    print(Validator.is_valid_structure("../../data/2025/Jan/16Thu"))
    print(Validator.is_valid_structure("../../data/2025/Jan/17Fri"))
    print(Validator.is_valid_structure("../../data/12-01-2025"))