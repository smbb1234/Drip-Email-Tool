import os
import pandas as pd
import json
import yaml
from typing import List, Dict

def validate_email_format(email: str) -> bool:
    """Validate the format of an email address using a simple regex."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

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
        if not validate_email_format(row["email"]):
            continue  # Skip invalid email
        _contacts.append({
            "name": row["name"],
            "email": row["email"],
            "company": row.get("company", None),
            "role": row.get("role", None),
        })

    return _contacts

def load_templates(file_path: str) -> List[Dict]:
    """Load email templates from a YAML or JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Templates file not found: {file_path}")

    _templates = []
    try:
        if file_path.endswith(".yaml") or file_path.endswith(".yml"):
            with open(file_path, "r") as f:
                _templates = yaml.safe_load(f)
        elif file_path.endswith(".json"):
            with open(file_path, "r") as f:
                _templates = json.load(f)
        else:
            raise ValueError("Unsupported template file format. Use .yaml, .yml, or .json.")
    except Exception as e:
        raise ValueError(f"Failed to read templates file: {e}")

    if not isinstance(_templates, list):
        raise ValueError("Templates file must contain a list of templates.")

    return _templates

def load_schedule(file_path: str) -> List[Dict]:
    """Load campaign schedules from a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Schedule file not found: {file_path}")

    _schedule = []
    try:
        with open(file_path, "r") as f:
            _schedule = json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to read schedule file: {e}")

    if not isinstance(_schedule, list):
        raise ValueError("Schedule file must contain a list of schedules.")

    for entry in _schedule:
        if "campaign_id" not in entry or "start_time" not in entry:
            raise ValueError("Each schedule entry must contain 'campaign_id' and 'start_time'.")

    return _schedule

# Example usage (to be integrated into the larger system):
if __name__ == "__main__":
    contacts = load_contacts("../../config/sample_contacts.csv")
    templates = load_templates("../../config/sample_templates.yaml")
    schedule = load_schedule("../../config/sample_schedule.json")

    print("Loaded contacts:", contacts)
    print("Loaded templates:", templates)
    print("Loaded schedule:", schedule)
