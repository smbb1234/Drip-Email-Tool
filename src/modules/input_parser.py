import os
import pandas as pd
import json
import yaml
import re
from pathlib import Path
from typing import List, Dict
from src.modules import log_event
from src.utils import Validator

class InputParser:
    """Utility class for parsing input data."""
    @staticmethod
    def load_contacts(file_path: Path) -> List[Dict]:
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

        def filter_invalidate_email(email):
            if not Validator.validate_email_format(email):
                log_event(f"Invalid email skipped: {email}", "WARNING")
                return False
            return True

        # Filter out rows with invalid email addresses
        filtered_df = df[df["email"].apply(filter_invalidate_email)]

        return filtered_df.to_dict(orient='records') # Convert to list of dictionaries

    @staticmethod
    def load_templates(file_path: Path) -> List[Dict]:
        """Load email templates from a YAML file."""
        required_keys = {"sequence", "subject", "content"} # Required keys for each template
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Templates file not found: {file_path}")

        templates = []
        try:
            with open(file_path, "r") as f:
                templates = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to read templates file: {e}")

        if not isinstance(templates, list):
            raise ValueError("Templates file must contain a list of templates.")

        # Validate that each template contains the required keys
        for template in templates:
            if not required_keys.issubset(template.keys()):
                raise ValueError(f"Templates must contain the following keys: {required_keys}, {template} missing required fields.")

        return templates

    @staticmethod
    def load_schedule(file_path: Path) -> List[Dict]:
        """Load campaign schedules from a JSON file."""
        required_keys = {"campaign_id", "sequences"} # Required keys for each campaign
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Schedule file not found: {file_path}")

        try:
            with open(file_path, "r") as f:
                schedule = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to read schedule file: {e}")

        if not isinstance(schedule, list):
            raise ValueError("Schedule file must contain a list of campaigns.")

        for campaign in schedule:
            if not required_keys.issubset(campaign.keys()):
                raise ValueError(f"Campaign must contain the following keys: {required_keys}, {campaign} missing required fields.")
            if len(campaign["sequences"]) == 0:
                raise ValueError(f"Campaign must contain at least one sequence: {campaign['campaign_id']}")

        return schedule

    @staticmethod
    def extract_placeholders(template_content: str) -> List[str]:
        """
        Extract placeholders in templates
        For example: Hi {name}, your {topic} -> ['name', 'topic']
        """
        return re.findall(r"\{(.*?)}", template_content)

    @staticmethod
    def build_campaign_data(base_path: Path) -> Dict:
        """
        Parse schedule.json and templates.yaml in the directory, dynamically associate sequence with template, and record placeholders.
        Load the contacts into the corresponding campaign and sequence
        """
        schedule_file = base_path / "schedule.json"

        # Parsing schedules and templates
        schedule = InputParser.load_schedule(schedule_file)

        campaigns_data = {}
        for campaign in schedule:
            campaign_id = campaign["campaign_id"]
            campaigns_data[campaign_id] = {}
            campaigns_data[campaign_id]["campaign_status"] = "Not Started"

            # Load each campaign’s templates.yaml
            templates_path = base_path / campaign_id / "templates.yaml"
            templates = InputParser.load_templates(templates_path)

            # Create a sequence-to-template mapping
            sequence_template_mapping = {}
            for template in templates:
                sequence_id = template["sequence"]
                placeholders = {
                    "subject": InputParser.extract_placeholders(template["subject"]),
                    "content": InputParser.extract_placeholders(template["content"])
                }
                sequence_template_mapping[sequence_id] = {
                    "subject": template["subject"],
                    "content": template["content"],
                    "placeholders": placeholders
                }

            for seq in campaign["sequences"]:
                sequence_id = seq["sequence"]
                contacts_path = base_path / campaign_id / f"{sequence_id}" / "contacts.csv"

                # Use the same contact as in the previous stage if contacts file does not exist
                if not os.path.exists(contacts_path):
                    if sequence_id == 1:
                        log_event(f"Contacts file not found for {base_path.resolve()}\\{campaign_id}\\{sequence_id}, skipping the campaign", "ERROR")
                        break
                    log_event(f"Contacts file not found for {base_path.resolve()}\\{campaign_id}\\{sequence_id}, using previous contacts", "WARNING")
                    contacts_temp = {
                        contact: {
                            **value,
                            "progress": "Not Started"
                        }
                        for contact, value in campaigns_data[campaign_id][sequence_id - 1]["contacts"].items()
                    }
                else:
                    contacts = InputParser.load_contacts(contacts_path)
                    contacts_temp = {  # Set Email as key
                        contact["email"]: {
                            "info": {
                                key: value for key, value in contact.items() if key != "email"
                            },
                            "progress": "Not Started"
                        }
                        for contact in contacts
                    }

                # Load contacts for the sequence
                template = sequence_template_mapping.get(sequence_id)

                if template:
                    campaigns_data[campaign_id][sequence_id] = {
                        "sequence_status": "Not Started",
                        "start_time": seq['start_time'],
                        "interval": seq['interval'],
                        "template": template,
                        "contacts": contacts_temp
                    }
                else:
                    log_event(f"Template not found for {campaign_id} / {sequence_id}", "ERROR")
        return campaigns_data

# Example usage (to be integrated into the larger system):
if __name__ == "__main__":
    base_directory = Path("../../data/")

    # contacts_file = base_directory / "12-01-2025"/ "campaign_1"/ "1" / "contacts.csv"
    # templates_file = base_directory / "12-01-2025"/ "campaign_1"/ "templates.yaml"
    # schedule_file = base_directory / "12-01-2025"/ "schedule.json"
    #
    # try:
    #     contacts = InputParser.load_contacts(contacts_file)
    #     templates = InputParser.load_templates(templates_file)
    #     schedule = InputParser.load_schedule(schedule_file)
    #
    #     print("Loaded contacts:", contacts)
    #     print("Loaded templates:", templates)
    #     for template in templates:
    #         print("Extracted placeholders:", InputParser.extract_placeholders(template["content"]))
    #     print("Loaded schedule:", schedule)
    # except Exception as e:
    #     log_event(f"Error during processing: {e}", "ERROR")

    # Build campaign data
    campaigns_file = base_directory / "12-01-2025"
    campaign_data = InputParser.build_campaign_data(campaigns_file)
    print("Campaign data:", campaign_data)
    # with open(base_directory / "campaigns.json", "w") as f:
    #     json.dump(campaign_data, f, indent=2)


