import os
from datetime import datetime
from pathlib import Path
from typing import Dict
from src.modules import log_event
from src.utils import Utils

class CampaignManager:
    """Manage email campaigns and track their progress."""
    CONTACT_ALLOWED_STATUSES = {"Not Started", "Pending", "Email Sent", "Reply Received", "Closed"}
    CAMPAIGN_ALLOWED_STATUSES = {"Not Started", "In Progress", "Completed"}

    def __init__(self, campaign_data: Dict, campaigns_name: str = datetime.now().strftime("%d-%m-%Y"), store_file: str = f"src/campaigns.json"):
        """Initialize the campaign manager."""
        self.campaigns_workflow = {}
        self.store_file = Path(store_file)

        # Create a new CampaignManager instance from a store file.
        if campaign_data is None and os.path.exists(self.store_file):
            self.campaigns_workflow = Utils.load_json_file(self.store_file)
            log_event("Campaign state file loaded successfully.", "INFO")
            return

        if campaign_data is not None:
            self.campaigns_workflow = {
                campaigns_name: campaign_data
            }

            log_event(f"Initialized {campaigns_name}.", "INFO")
            self.save_state()
            return

        log_event("Failed to initialize CampaignManager instance.", "ERROR")

    def add_campaigns(self, campaigns_data: Dict, campaigns_name: str = datetime.now().strftime("%d-%m-%Y")) -> bool:
        """Add new campaigns to the manager."""
        if campaigns_name in self.campaigns_workflow:
            log_event(f"Campaigns {campaigns_name} already exists.", "ERROR")
            return False

        self.campaigns_workflow[campaigns_name] = campaigns_data
        self.save_state()
        log_event(f"Added new campaigns {campaigns_name}.", "INFO")
        return True

    def get_campaigns(self, campaigns_name: str) -> Dict:
        """Retrieve campaigns by campaigns name."""
        if campaigns_name not in self.campaigns_workflow:
            log_event(f"Campaigns {campaigns_name} does not exist.", "ERROR")
            return {}

        log_event("Retrieved campaigns for {campaigns_name}.", "INFO")
        return self.campaigns_workflow[campaigns_name]

    def del_campaigns(self, campaigns_name: str) -> bool:
        """Delete campaigns by campaigns name."""
        if campaigns_name not in self.campaigns_workflow:
            log_event(f"Campaigns {campaigns_name} does not exist.", "ERROR")
            return False

        del self.campaigns_workflow[campaigns_name]
        self.save_state()
        log_event(f"Deleted campaigns {campaigns_name}.", "INFO")
        return True

    def get_campaign(self, campaigns_name: str, campaign_id: str) -> Dict:
        """Retrieve the campaign data."""
        if campaigns_name not in self.campaigns_workflow:
            log_event(f"Campaigns {campaigns_name} does not exist.", "ERROR")
            return {}
        if campaign_id not in self.campaigns_workflow[campaigns_name]:
            log_event(f"Campaign: {campaigns_name} - {campaign_id} does not exist.", "ERROR")
            return {}

        log_event(f"Retrieved data for {campaigns_name} - {campaign_id}.", "INFO")
        return self.campaigns_workflow[campaigns_name][campaign_id]

    def update_campaign_status(self, campaigns_name: str, campaign_id: str, status: str) -> bool:
        """Update the status of the campaign."""
        if campaigns_name not in self.campaigns_workflow:
            log_event(f"Campaigns {campaigns_name} does not exist.", "ERROR")
            return False
        if campaign_id not in self.campaigns_workflow[campaigns_name]:
            log_event(f"Campaign: {campaigns_name} - {campaign_id} does not exist.", "ERROR")
            return False

        if status not in self.CAMPAIGN_ALLOWED_STATUSES:
            log_event(f"Invalid status '{status}' for campaign {campaigns_name} - {campaign_id}. Allowed statuses: {self.CAMPAIGN_ALLOWED_STATUSES}.", "ERROR")
            return False

        self.campaigns_workflow[campaigns_name][campaign_id]["campaign_status"] = status
        self.save_state()

        log_event(f"Updated campaign {campaign_id} to status: {status}.", "INFO")
        return True

    def get_stage(self, campaigns_name: str, campaign_id: str, stage: int) -> Dict:
        """Retrieve the stage data."""
        if campaigns_name not in self.campaigns_workflow:
            log_event(f"Campaigns {campaigns_name} does not exist.", "ERROR")
            return {}
        if campaign_id not in self.campaigns_workflow[campaigns_name]:
            log_event(f"Campaign: {campaigns_name} - {campaign_id} does not exist.", "ERROR")
            return {}
        if stage not in self.campaigns_workflow[campaigns_name][campaign_id]:
            log_event(f"Stage {stage} is out of range for campaign {campaigns_name} - {campaign_id}.", "ERROR")
            return {}

        log_event(f"Retrieved data for stage {stage} in {campaigns_name} - {campaign_id}.", "INFO")
        return self.campaigns_workflow[campaigns_name][campaign_id][stage]

    def update_stage_status(self, campaigns_name: str, campaign_id: str, stage: int, status: str) -> bool:
        """Update the status of the stage."""
        if campaigns_name not in self.campaigns_workflow:
            log_event(f"Campaigns {campaigns_name} does not exist.", "ERROR")
            return False
        if campaign_id not in self.campaigns_workflow[campaigns_name]:
            log_event(f"Campaign: {campaigns_name} - {campaign_id} does not exist.", "ERROR")
            return False
        if stage not in self.campaigns_workflow[campaigns_name][campaign_id]:
            log_event(f"Stage {stage} is out of range for campaign {campaigns_name} - {campaign_id}.", "ERROR")
            return False

        if status not in self.CAMPAIGN_ALLOWED_STATUSES:
            log_event(f"Invalid status '{status}' for stage {stage} in campaign {campaigns_name} - {campaign_id}. Allowed statuses: {self.CAMPAIGN_ALLOWED_STATUSES}.", "ERROR")
            return False

        self.campaigns_workflow[campaigns_name][campaign_id][stage]["sequence_status"] = status
        self.save_state()

        log_event(f"Updated stage {stage} in {campaigns_name} - {campaign_id} to status: {status}.", "INFO")
        return True

    def get_contact(self, campaigns_name: str, campaign_id: str, stage: int, contact_email: str) -> Dict:
        """Retrieve the contact data."""
        sequence = self.get_stage(campaigns_name, campaign_id, stage)

        if not sequence:
            return {}
        if contact_email not in sequence["contacts"]:
            log_event(f"Contact {contact_email} not found in stage {stage} of campaign {campaigns_name} - {campaign_id}.", "ERROR")
            return {}

        log_event(f"Retrieved data for contact {contact_email} in stage {stage} of {campaigns_name} - {campaign_id}.", "INFO")
        return sequence["contacts"][contact_email]

    def update_contact_status(self, campaigns_name: str, campaign_id: str, stage: int, contact_email: str, status: str) -> bool:
        """Update the status of the contact."""
        sequence = self.get_stage(campaigns_name, campaign_id, stage)

        if not sequence:
            return False
        if contact_email not in sequence["contacts"]:
            log_event(
                f"Contact {contact_email} not found in stage {stage} of campaign {campaigns_name} - {campaign_id}.",
                "ERROR")
            return False

        if status not in self.CONTACT_ALLOWED_STATUSES:
            log_event(f"Invalid status '{status}' for contact {contact_email} in stage {stage} of campaign {campaigns_name} - {campaign_id}. Allowed statuses: {self.CONTACT_ALLOWED_STATUSES}.", "ERROR")
            return False

        sequence["contacts"][contact_email]["progress"] = status
        self.save_state()

        log_event(f"Updated contact {contact_email} in stage {stage} of {campaigns_name} - {campaign_id} to status: {status}.", "INFO")
        return True

    def get_current_stage(self, campaigns_name: str, campaign_id: str):
        """Get the current stage of a contact in a campaign."""
        campaign = self.get_campaign(campaigns_name, campaign_id)

        if not campaign:
            return 0, 0

        total_stage = len(campaign) - 1

        if campaign["campaign_status"] == "Not Started":
            return 1, total_stage

        for sequence_id in range(total_stage, 0, -1):
            if campaign[sequence_id]["sequence_status"] != "Not Started":
                return sequence_id, total_stage

    def get_current_stage_template(self, campaigns_name: str, campaign_id: str, stage: int) -> Dict:
        """Get the template for the current stage of a campaign."""
        sequence = self.get_stage(campaigns_name, campaign_id, stage)

        if not sequence:
            return {}

        return sequence["template"]

    def get_campaign_start_time(self, campaigns_name: str, campaign_id: str):
        """
        Get the start time for the campaign.
        The start time of the first stage is agreed to be the start time of the campaign
        """
        return self.get_stage_start_time(campaigns_name, campaign_id, 1)

    def get_stage_start_time(self, campaigns_name: str, campaign_id: str, stage: int):
        """Get the start time for the stage."""
        sequence = self.get_stage(campaigns_name, campaign_id, stage)

        if not sequence:
            return None

        return datetime.fromisoformat(sequence["start_time"])

    def get_stage_interval(self, campaigns_name: str, campaign_id: str, stage: int) -> int:
        """Get the interval for the stage."""
        sequence = self.get_stage(campaigns_name, campaign_id, stage)

        if not sequence:
            return 0

        return sequence["interval"]

    def is_end_of_stage(self, campaigns_name: str, campaign_id: str) -> bool:
        """Check if the stage is the last stage in the campaign."""
        current_stage, total_stage = self.get_current_stage(campaigns_name, campaign_id)

        if current_stage == 0 or total_stage == 0:
            return False

        return current_stage >= total_stage

    def get_next_stage_start_time(self, campaigns_name: str, campaign_id: str):
        """Get the start time for the next stage in the campaign."""
        if self.is_end_of_stage(campaigns_name, campaign_id):
            return None

        current_stage, total_stage = self.get_current_stage(campaigns_name, campaign_id)

        return self.get_stage_start_time(campaigns_name, campaign_id, current_stage + 1)

    def start_campaign(self, campaigns_name: str, campaign_id: str) -> bool:
        """Start the campaign by updating its status."""
        campaign = self.get_campaign(campaigns_name, campaign_id)

        if not campaign:
            return False

        if campaign["campaign_status"] != "Not Started":
            log_event(f"{campaigns_name} - {campaign_id} has already started.", "WARNING")

        current_stage, total_stage = self.get_current_stage(campaigns_name, campaign_id)
        sequence = self.get_stage(campaigns_name, campaign_id, current_stage)

        if not sequence:
            log_event(f"Fail to start {campaigns_name} - {campaign_id} - {current_stage}.", "ERROR")
            return False

        for contact_email, contact in sequence["contacts"].items():
            if contact["progress"] != "Not Started":
                log_event(f"{campaigns_name} - {campaign_id} - {current_stage} - {contact} has already started.", "WARNING")
            self.update_contact_status(campaigns_name, campaign_id, current_stage, contact_email, "Pending")

        self.update_stage_status(campaigns_name, campaign_id, current_stage, "In Progress")
        self.update_campaign_status(campaigns_name, campaign_id, "In Progress")
        log_event(f"Campaign {campaign_id} started.", "INFO")
        return True

    def move_to_next_stage(self, campaigns_name: str, campaign_id: str) -> bool:
        """Start to the next stage in the campaign."""
        campaign = self.get_campaign(campaigns_name, campaign_id)

        if not campaign:
            return False
        if self.is_end_of_stage(campaigns_name, campaign_id):
            return False

        current_stage, _ = self.get_current_stage(campaigns_name, campaign_id)
        next_stage = current_stage + 1
        sequence = self.get_stage(campaigns_name, campaign_id, next_stage)

        for contact_email, contact in sequence["contacts"].items():
            if contact["progress"] != "Not Started":
                log_event(f"{campaigns_name} - {campaign_id} - {next_stage} - {contact} has already started.", "WARNING")
            self.update_contact_status(campaigns_name, campaign_id, next_stage, contact_email, "Pending")

        self.update_stage_status(campaigns_name, campaign_id, next_stage, "In Progress")
        log_event(f"Moved to next stage {next_stage} in {campaigns_name} - {campaign_id}.", "INFO")
        return True

    def completed_stage(self, campaigns_name: str, campaign_id: str, stage: int) -> bool:
        """Get all stages completed."""
        sequence = self.get_stage(campaigns_name, campaign_id, stage)

        if not sequence:
            return False

        for _, contact in sequence["contacts"].items():
            if contact["progress"] not in {
                "Email Sent",
                "Reply Received",
                "Closed"
            }:
                return False
        self.update_stage_status(campaigns_name, campaign_id, stage, "Completed")
        log_event(f"Stage {stage} in {campaigns_name} - {campaign_id} completed.", "INFO")
        return True

    def completed_campaign(self, campaigns_name: str, campaign_id: str) -> bool:
        """Get all campaigns completed."""
        campaign = self.get_campaign(campaigns_name, campaign_id)

        if not campaign:
            return False

        _, total_stage = self.get_current_stage(campaigns_name, campaign_id)

        if total_stage == 0:
            return False

        for sequence_id in range(1, total_stage + 1):
            sequence = self.get_stage(campaigns_name, campaign_id, sequence_id)
            if sequence["sequence_status"] != "Completed":
                return False

        self.update_campaign_status(campaigns_name, campaign_id, "Completed")
        log_event(f"{campaign_id} in {campaigns_name} completed.", "INFO")
        return True

    def completed_all_campaigns(self, campaigns_name: str) -> bool:
        """Get all campaigns completed."""
        campaigns = self.get_campaigns(campaigns_name)

        if not campaigns:
            return False

        for _, campaign_id in campaigns.items():
            campaign = self.get_campaign(campaigns_name, campaign_id)
            if campaign["campaign_status"] != "Completed":
                return False

        log_event(f"All campaigns in {campaigns_name} completed.", "INFO")
        return True

    def save_state(self):
        """Save the current campaign state to the state file."""
        Utils.save_json_file(self.store_file, self.campaigns_workflow)
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

    if os.path.exists("campaigns.json"):
        CampaignManager.delete_state("campaigns.json")

    from src.modules import InputParser
    example_campaigns1 = InputParser.build_campaign_data(Path("../../data/12-01-2025"))
    manager = CampaignManager(example_campaigns1, "12-01-2025", "campaigns.json")

    example_campaigns2 = InputParser.build_campaign_data(Path("../../data/12-01-2025"))
    print(manager.add_campaigns(example_campaigns2, "12-02-2025"))

    print(manager.get_campaigns("12-01-2025"))
    print(manager.get_campaign("12-01-2025", "campaign_1"))
    print(manager.get_stage("12-01-2025", "campaign_1", 1))
    print(manager.get_contact("12-01-2025", "campaign_1", 1, "john.doe@example.com"))

    print(manager.get_current_stage("12-01-2025", "campaign_1"))
    print(manager.start_campaign("12-01-2025", "campaign_1"))
    print(manager.get_campaign("12-01-2025", "campaign_1"))

    print(manager.move_to_next_stage("12-01-2025", "campaign_1"))
    print(manager.get_current_stage("12-01-2025", "campaign_1"))
    print(manager.get_current_stage_template("12-01-2025", "campaign_1", 2))
    print(manager.get_stage_start_time("12-01-2025", "campaign_1", 2))
    print(manager.get_stage_interval("12-01-2025", "campaign_1", 2))
    print(manager.is_end_of_stage("12-01-2025", "campaign_1"))
    print(manager.move_to_next_stage("12-01-2025", "campaign_1"))
    print(manager.get_current_stage("12-01-2025", "campaign_1"))

    print(manager.update_stage_status("12-01-2025", "campaign_1", 1, "Completed"))
    print(manager.update_stage_status("12-01-2025", "campaign_1", 2, "Completed"))
    print(manager.completed_campaign("12-01-2025", "campaign_1"))
