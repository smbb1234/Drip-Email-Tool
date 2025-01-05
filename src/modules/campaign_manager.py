import os
from typing import Dict, List
from src.modules import log_event
from src.utils import validate_campaign_data, Utils

class CampaignManager:
    """Manage email campaigns and track their progress."""
    CONTACT_ALLOWED_STATUSES = {"Pending", "Email Sent", "Reply Received"}
    CAMPAIGN_ALLOWED_STATUSES = {"Not Started", "In Progress", "Completed"}

    def __init__(self, **kwargs):
        """Initialize the campaign manager."""
        self.campaigns = {}
        self.store_file = kwargs.get("store_file")

        if self.store_file is None:
            self.store_file = "campaigns.json"

        _campaign_data = kwargs.get("campaign_data")
        _contacts = kwargs.get("contacts")
        _templates = kwargs.get("templates")
        _schedule = kwargs.get("schedule")

        if _campaign_data is not None:
            self.initialize_campaign(_campaign_data)
            return

        if _contacts is not None and _templates is not None and _schedule is not None:
            self.initialize_campaign(self.build_campaign_data(_contacts, _templates, _schedule))
            return

        if os.path.exists(self.store_file):
            self.campaigns = Utils.load_json_file(self.store_file)
            log_event("Loaded campaign state from file.", "INFO")
        else:
            log_event("No campaign state file found. Initializing an empty campaign manager.", "WARNING")

    @staticmethod
    def build_campaign_data(contacts: List[Dict], templates: List[Dict], schedule: List[Dict]) -> Dict:
        """Build a new campaign data object."""
        return {
            "contacts": contacts,
            "templates": templates,
            "schedule": schedule
        }

    def initialize_campaign(self, _campaign_data: Dict) -> bool:
        """Initialize a new campaign with the provided data."""
        if not validate_campaign_data(_campaign_data):
            log_event("Campaign data validation failed. Initialization aborted.", "ERROR")
            return False

        # Set Email as key
        enriched_contacts = {
            _contact["email"]: {key: value for key, value in _contact.items() if key != "email"}
            for _contact in _campaign_data["contacts"]
        }

        template_map = {template["sequence"]: template for template in _campaign_data["templates"]}# Create a mapping of sequence number to template
        for campaign in _campaign_data["schedule"]:
            if campaign["campaign_id"] in self.campaigns:
                log_event(
                    f"Duplicate campaign ID {campaign['campaign_id']} detected. Skipping initialization for this campaign.",
                    "WARNING")
                continue

            for sequence in campaign["sequences"]:
                sequence_number = sequence.get("sequence")
                if sequence_number not in template_map:
                    log_event(
                        f"No matching template for sequence: {sequence_number} in campaign: {campaign['campaign_id']}.",
                        "WARNING")

            self.campaigns[campaign["campaign_id"]] = {
                "contacts": {
                    contact: {
                        "info": enriched_contacts[contact],
                        "stage": 1,
                        "progress": "Pending"
                    }
                    for contact in enriched_contacts
                },
                "templates": _campaign_data["templates"],
                "schedule": campaign["sequences"],
                "status": "Not Started"
            }

            log_event(f"Initialized campaign {campaign["campaign_id"]}.", "INFO")

        self.save_state()
        return True

    def start_campaign(self, campaign_id: str) -> bool:
        """Start the campaign by updating its status."""
        if campaign_id not in self.campaigns:
            log_event(f"Campaign {campaign_id} does not exist.", "ERROR")
            return False

        campaign = self.campaigns[campaign_id]
        if campaign["status"] != "Not Started":
            log_event(f"Campaign {campaign_id} cannot be started. Current status: {campaign['status']}", "WARNING")
            return False

        campaign["status"] = "In Progress"
        self.save_state()
        log_event(f"Campaign {campaign_id} started.", "INFO")
        return True

    def update_campaign_status(self, campaign_id: str, contact_email: str, status: str) -> bool:
        """Update the status of a specific contact in the campaign."""
        if campaign_id not in self.campaigns:
            log_event(f"Campaign {campaign_id} does not exist.", "ERROR")
            return False

        if status not in self.CONTACT_ALLOWED_STATUSES:
            log_event(
                f"Invalid status '{status}' for contact {contact_email}. Allowed statuses: {self.CONTACT_ALLOWED_STATUSES}.",
                "ERROR")
            return False

        campaign = self.campaigns[campaign_id]
        if contact_email not in campaign["contacts"]:
            log_event(f"Contact {contact_email} not found in campaign {campaign_id}.", "ERROR")
            return False

        campaign["contacts"][contact_email]["progress"] = status
        self.save_state()
        log_event(f"Updated contact {contact_email} in campaign {campaign_id} to status: {status}.", "INFO")
        return True

    def get_campaign_status(self, campaign_id: str) -> Dict:
        """Retrieve the campaign data."""
        if campaign_id not in self.campaigns:
            log_event(f"Campaign: {campaign_id} does not exist.", "ERROR")
            return {}

        log_event(f"Retrieved data for campaign: {campaign_id}.", "INFO")
        return self.campaigns[campaign_id]

    def save_state(self):
        """Save the current campaign state to the state file."""
        Utils.save_json_file(self.store_file, self.campaigns)
        log_event("Saved campaign state to file.", "INFO")

    @staticmethod
    def delete_state(store_file: str):
        """Delete the state file."""
        if os.path.exists(store_file):
            os.remove(store_file)
            log_event("Deleted campaign state file.", "INFO")
        else:
            log_event("Campaign state file not found.", "WARNING")

if __name__ == "__main__":
    # from src.modules import initialize_logger
    # initialize_logger()

    # Example Usage
    example_contacts = [
        {"name": "John Doe", "email": "john.doe@example.com"},
        {"name": "Jane Smith", "email": "jane.smith@example.com"},
        {"name": "Alice Johnson", "email": "alice.johnson@example.com"}
    ]

    example_templates = [
        {"sequence": 1, "subject": "Hello {name}", "content": "Hi {name}, let's connect!"},
        {"sequence": 2, "subject": "Follow-up", "content": "Just checking in!"},
        {"sequence": 3, "subject": "Final Reminder", "content": "Last chance to connect!"}
    ]

    example_schedule = [
        {"campaign_id": "campaign_1", "sequences": [
            {"sequence": 1, "start_time": "2025-01-02T09:00:00", "interval": 1},
            {"sequence": 2, "start_time": "2025-01-03T09:00:00", "interval": 2}
        ]},
        {"campaign_id": "campaign_2", "sequences": [
            {"sequence": 1, "start_time": "2025-01-04T09:00:00", "interval": 5},
            {"sequence": 2, "start_time": "2025-01-05T09:00:00", "interval": 3},
            {"sequence": 3, "start_time": "2025-01-06T09:00:00", "interval": 4}
        ]},
        {"campaign_id": "campaign_3", "sequences": [
            {"sequence": 1, "start_time": "2025-01-07T09:00:00", "interval": 6}
        ]}
    ]

    CampaignManager.delete_state("campaigns.json")

    campaign_data = CampaignManager.build_campaign_data(example_contacts, example_templates, example_schedule)

    manager_1 = CampaignManager(campaign_data=campaign_data)

    # manager_1 = CampaignManager(store_file="campaigns.json")
    # manager_1.initialize_campaign(campaign_data)

    # manager_1 = CampaignManager(contacts=example_contacts, templates=example_templates, schedule=example_schedule)

    manager_1.start_campaign("campaign_1")
    manager_1.update_campaign_status("campaign_1", "john.doe@example.com", "Email Sent")
    print(manager_1.get_campaign_status("campaign_1"))
