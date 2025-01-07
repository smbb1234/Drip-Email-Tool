import os
from typing import Dict, List
from src.modules import log_event
from src.utils import Validator, Utils

class CampaignManager:
    """Manage email campaigns and track their progress."""
    CONTACT_ALLOWED_STATUSES = {"Not Started", "Pending", "Email Sent", "Reply Received", "Closed"}
    CAMPAIGN_ALLOWED_STATUSES = {"Not Started", "In Progress", "Completed"}

    def __init__(self, campaign_data: Dict | None, store_file: str = "campaigns.json"):
        """Initialize the campaign manager."""
        self.campaigns = {}
        self.store_file = store_file

        # Create a new CampaignManager instance from a store file.
        if campaign_data is None and os.path.exists(self.store_file):
            self.campaigns = Utils.load_json_file(self.store_file)
            log_event("Campaign state file loaded successfully.", "INFO")
            return

        if campaign_data is not None:
            self.initialize_campaign(campaign_data)
            return

        log_event("Failed to initialize CampaignManager instance.", "ERROR")

    @classmethod
    def from_parser(cls, contacts: List[Dict], templates: List[Dict], schedule: List[Dict]):
        """Create a new CampaignManager instance from a parser."""
        if contacts is not None and templates is not None and schedule is not None:
            return cls(cls.build_campaign_data(contacts, templates, schedule))

        log_event("Failed to create CampaignManager instance from parser.", "ERROR")
        return None

    @staticmethod
    def build_campaign_data(contacts: List[Dict], templates: List[Dict], schedule: List[Dict]) -> Dict:
        """Build a new campaign data object."""
        return {
            "contacts": contacts,
            "templates": templates,
            "schedule": schedule
        }

    def initialize_campaign(self, campaign_data: Dict) -> bool:
        """Initialize a new campaign with the provided data."""
        if not Validator.validate_campaign_data(campaign_data):
            log_event("Campaign data validation failed. Initialization aborted.", "ERROR")
            return False

        # Set Email as key
        enriched_contacts = {
            _contact["email"]: {key: value for key, value in _contact.items() if key != "email"}
            for _contact in campaign_data["contacts"]
        }

        template_map = {template["sequence"]: template for template in campaign_data["templates"]}# Create a mapping of sequence number to template
        for campaign in campaign_data["schedule"]:
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
                        "current_stage": 1,
                        "total_stage": len(campaign["sequences"]),
                        "progress": "Not Started"
                    }
                    for contact in enriched_contacts
                },
                "templates": campaign_data["templates"],
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

        for contact in campaign["contacts"]:
            campaign["contacts"][contact]["progress"] = "Pending"

        campaign["status"] = "In Progress"
        self.save_state()
        log_event(f"Campaign {campaign_id} started.", "INFO")
        return True

    def update_campaign_status(self, campaign_id: str, status: str) -> bool:
        """Update the status of the campaign."""
        if campaign_id not in self.campaigns:
            log_event(f"Campaign {campaign_id} does not exist.", "ERROR")
            return False

        if status not in self.CAMPAIGN_ALLOWED_STATUSES:
            log_event(f"Invalid status '{status}' for campaign {campaign_id}. Allowed statuses: {self.CAMPAIGN_ALLOWED_STATUSES}.", "ERROR")
            return False

        campaign = self.campaigns[campaign_id]
        campaign["status"] = status
        self.save_state()

        log_event(f"Updated campaign {campaign_id} to status: {status}.", "INFO")
        return True

    def update_contact_campaign_status(self, campaign_id: str, contact_email: str, status: str) -> bool:
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

    def get_all_contacts(self, campaign_id: str) -> Dict:
        """Retrieve all contacts in the campaign."""
        if campaign_id not in self.campaigns:
            log_event(f"Campaign {campaign_id} does not exist.", "ERROR")
            return {}

        log_event(f"Retrieved all contacts for campaign: {campaign_id}.", "INFO")
        return self.campaigns[campaign_id]["contacts"]

    def get_contact_campaign_status(self, campaign_id: str, contact_email: str) -> Dict:
        """Retrieve the status of a specific contact in the campaign."""
        if campaign_id not in self.campaigns:
            log_event(f"Campaign {campaign_id} does not exist.", "ERROR")
            return {}

        campaign = self.campaigns[campaign_id]
        if contact_email not in campaign["contacts"]:
            log_event(f"Contact {contact_email} not found in campaign {campaign_id}.", "ERROR")
            return {}

        log_event(f"Retrieved data for contact {contact_email} in campaign {campaign_id}.", "INFO")
        return campaign["contacts"][contact_email]

    def get_current_stage(self, campaign_id: str, contact_email: str) -> dict:
        """Get the current stage of a contact in a campaign."""
        if campaign_id not in self.campaigns:
            log_event(f"Campaign {campaign_id} does not exist.", "ERROR")
            return {}

        campaign = self.campaigns[campaign_id]
        if contact_email not in campaign["contacts"]:
            log_event(f"Contact {contact_email} not found in campaign {campaign_id}.", "ERROR")
            return {}

        return campaign["schedule"][campaign["contacts"][contact_email]["current_stage"] - 1]

    def move_to_next_stage(self, campaign_id: str, contact_email: str) -> int:
        """Move a contact to the next stage in the campaign."""
        if campaign_id not in self.campaigns:
            log_event(f"Campaign {campaign_id} does not exist.", "ERROR")
            return -1

        campaign = self.campaigns[campaign_id]
        if contact_email not in campaign["contacts"]:
            log_event(f"Contact {contact_email} not found in campaign {campaign_id}.", "ERROR")
            return -1

        contact = campaign["contacts"][contact_email]
        if contact["current_stage"] >= contact["total_stage"]:
            log_event(f"Contact {contact_email} has reached the end of the campaign {campaign_id}. Current/Total: {contact["current_stage"]}/{contact["total_stage"]}.", "INFO")
            self.update_contact_campaign_status(campaign_id, contact_email, "Closed")
            return 0

        self.update_contact_campaign_status(campaign_id, contact_email, "Pending")
        contact["current_stage"] += 1
        self.save_state()
        log_event(f"Moved contact {contact_email} to the next stage in campaign {campaign_id}.", "INFO")
        return 1

    def get_current_stage_template(self, campaign_id: str, sequence: int) -> dict:
        """Get the template for the current stage of a campaign."""
        if campaign_id not in self.campaigns:
            log_event(f"Campaign {campaign_id} does not exist.", "ERROR")
            return {}

        campaign = self.campaigns[campaign_id]
        if sequence > len(campaign["schedule"]):
            log_event(f"Sequence {sequence} is out of range for campaign {campaign_id}.", "ERROR")
            return {}

        return campaign["templates"][sequence - 1]

    def completed_campaign(self, campaign_id: str) -> bool:
        """Get all completed campaigns."""
        for _, contact in self.campaigns[campaign_id]["contacts"].items():
            if contact["progress"] != "Closed":
                return False
        self.update_campaign_status(campaign_id, "Completed")
        return True

    def completed_all_campaigns(self) -> bool:
        """Get all completed campaigns."""
        for campaign_id, _ in self.campaigns.items():
            if not self.completed_campaign(campaign_id):
                return False
        return True

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

    if os.path.exists("campaigns.json"):
        CampaignManager.delete_state("campaigns.json")

    campaign_data = CampaignManager.build_campaign_data(example_contacts, example_templates, example_schedule)

    manager_1 = CampaignManager(campaign_data)
    # manager_1 = CampaignManager(None)
    # manager_1 = CampaignManager.from_parser(example_contacts, example_templates, example_schedule)

    manager_1.start_campaign("campaign_1")
    manager_1.update_contact_campaign_status("campaign_1", "john.doe@example.com", "Email Sent")
    print(manager_1.get_campaign_status("campaign_1"))
