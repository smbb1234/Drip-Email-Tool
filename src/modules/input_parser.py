import os
import pandas as pd
import json
import yaml
from typing import List, Dict
from src.modules import log_event
from src.utils import Validator

class InputParser:
    """Utility class for parsing input data."""
    @staticmethod
    def load_contacts(file_path: str) -> List[Dict]:
        """Load and validate contacts from a CSV file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Contacts file not found: {file_path}")

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Failed to read contacts file: {e}")

        required_columns = {"name", "email"}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"Contacts file must contain the following columns: {required_columns}")

        _contacts = []
        for _, row in df.iterrows():
            if not Validator.validate_email_format(row["email"]):
                log_event(f"Invalid email skipped: {row['email']}", "WARNING")
                continue  # Skip invalid email
            _contacts.append({
                "name": row["name"],
                "email": row["email"],
                "company": row.get("company", None),
                "role": row.get("role", None),
            })

        return _contacts

    @staticmethod
    def load_templates(file_path: str) -> List[Dict]:
        """Load email templates from a YAML file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Templates file not found: {file_path}")

        _templates = []
        try:
            with open(file_path, "r") as f:
                _templates = yaml.safe_load(f)
            if not isinstance(_templates, list):
                raise ValueError("Templates file must contain a list of templates.")
        except Exception as e:
            raise ValueError(f"Failed to read templates file: {e}")

        return _templates

    @staticmethod
    def load_schedule(file_path: str) -> List[Dict]:
        """Load campaign schedules from a JSON file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Schedule file not found: {file_path}")

        _schedule = []
        try:
            with open(file_path, "r") as f:
                _schedule = json.load(f)
            if not isinstance(_schedule, list):
                raise ValueError("Schedule file must contain a list of campaigns.")

            for campaign in _schedule:
                if "campaign_id" not in campaign or "sequences" not in campaign:
                    raise ValueError(f"Campaign missing required fields: {campaign}")

                for sequence in campaign["sequences"]:
                    if "sequence" not in sequence or "start_time" not in sequence or "interval" not in sequence:
                        raise ValueError(f"Sequence missing required fields: {sequence}")

        except Exception as e:
            raise ValueError(f"Failed to read schedule file: {e}")

        return _schedule

# Example usage (to be integrated into the larger system):
if __name__ == "__main__":
    contacts_file = "../../config/sample_contacts.csv"
    templates_file = "../../config/sample_templates.yaml"
    schedule_file = "../../config/sample_schedule.json"

    try:
        contacts = InputParser.load_contacts(contacts_file)
        templates = InputParser.load_templates(templates_file)
        schedule = InputParser.load_schedule(schedule_file)

        print("Loaded contacts:", contacts)
        print("Loaded templates:", templates)
        print("Loaded schedule:", schedule)
    except Exception as e:
        log_event(f"Error during processing: {e}", "ERROR")


