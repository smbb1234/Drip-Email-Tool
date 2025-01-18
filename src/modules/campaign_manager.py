from datetime import datetime
from pathlib import Path
from typing import Dict, Union

from config import config
from src.modules import logger
from src.utils import Utils


class CampaignManager:
    """Manage email campaigns and track their progress."""
    CONTACT_ALLOWED_STATUSES = {"Not Started", "Pending", "Email Sent", "Reply Received", "Closed"}
    CAMPAIGN_ALLOWED_STATUSES = {"Not Started", "In Progress", "Completed"}

    def __init__(self, campaign_data: Dict = None, campaigns_name: str = datetime.now().strftime("%d-%m-%Y"), file_persistence: bool = config.FILE_PERSISTENCE, store_file: str = config.CAMPAIGN_PATH):
        """Initialize the campaign manager."""
        self.campaigns_workflow = {}
        self.load_file = file_persistence
        self.store_file = Path(store_file)

        # Create a new CampaignManager instance from a store file.
        if self.store_file.exists():
            if self.load_file:
                self.campaigns_workflow = Utils.load_json_file(self.store_file)
                logger.log_logic_event("Campaign state file loaded successfully.", "INFO")
                return
            else:
                self.store_file.unlink()
        logger.log_logic_event("Campaign store file not found.", "WARNING")

        if campaign_data is not None:
            self.campaigns_workflow = {
                campaigns_name: campaign_data
            }

            logger.log_event(f"Initialized {campaigns_name}.", "INFO")
            self.save_state()
            return

    def add_campaigns(self, campaigns_data: Dict, campaigns_name: str = datetime.now().strftime("%d-%m-%Y")) -> bool:
        """Add new campaigns to the manager."""
        if campaigns_name in self.campaigns_workflow:
            logger.log_event(f"Campaigns {campaigns_name} already exists.", "ERROR")
            return False

        self.campaigns_workflow[campaigns_name] = campaigns_data
        self.save_state()
        logger.log_event(f"Added new campaigns {campaigns_name}.", "INFO")
        return True

    def get_campaigns(self, campaigns_name: str) -> Dict:
        """Retrieve campaigns by campaigns name."""
        if campaigns_name not in self.campaigns_workflow:
            logger.log_event(f"Campaigns {campaigns_name} does not exist.", "ERROR")
            return {}

        logger.log_logic_event(f"Retrieved campaigns for {campaigns_name}.", "INFO")
        return self.campaigns_workflow[campaigns_name]

    def del_campaigns(self, campaigns_name: str) -> bool:
        """Delete campaigns by campaigns name."""
        if campaigns_name not in self.campaigns_workflow:
            logger.log_event(f"Campaigns {campaigns_name} does not exist.", "ERROR")
            return False

        del self.campaigns_workflow[campaigns_name]
        self.save_state()
        logger.log_event(f"Deleted campaigns {campaigns_name}.", "INFO")
        return True

    def get_campaign(self, campaigns_name: str, campaign_id: str) -> Dict:
        """Retrieve the campaign data."""
        if campaigns_name not in self.campaigns_workflow:
            logger.log_event(f"Campaigns {campaigns_name} does not exist.", "ERROR")
            return {}
        if campaign_id not in self.campaigns_workflow[campaigns_name]:
            logger.log_event(f"Campaign: {campaign_id} in {campaigns_name} does not exist.", "ERROR")
            return {}

        logger.log_logic_event(f"Retrieved data for {campaigns_name} - {campaign_id}.", "INFO")
        return self.campaigns_workflow[campaigns_name][campaign_id]

    def update_campaign_status(self, campaigns_name: str, campaign_id: str, status: str) -> bool:
        """Update the status of the campaign."""
        if campaigns_name not in self.campaigns_workflow:
            logger.log_event(f"Campaigns {campaigns_name} does not exist.", "ERROR")
            return False
        if campaign_id not in self.campaigns_workflow[campaigns_name]:
            logger.log_event(f"Campaign: {campaign_id} in {campaigns_name} does not exist.", "ERROR")
            return False

        if status not in self.CAMPAIGN_ALLOWED_STATUSES:
            logger.log_logic_event(f"Invalid status '{status}' for campaign {campaigns_name} - {campaign_id}. Allowed statuses: {self.CAMPAIGN_ALLOWED_STATUSES}.", "ERROR")
            return False

        if self.campaigns_workflow[campaigns_name][campaign_id]["campaign_status"] != status:
            self.campaigns_workflow[campaigns_name][campaign_id]["campaign_status"] = status
            self.save_state()

        logger.log_logic_event(f"Updated campaign {campaign_id} to status: {status}.", "INFO")
        return True

    def get_stage(self, campaigns_name: str, campaign_id: str, stage: int) -> Dict:
        """Retrieve the stage data."""
        if campaigns_name not in self.campaigns_workflow:
            logger.log_event(f"Campaigns {campaigns_name} does not exist.", "ERROR")
            return {}
        if campaign_id not in self.campaigns_workflow[campaigns_name]:
            logger.log_event(f"Campaign: {campaign_id} in {campaigns_name} does not exist.", "ERROR")
            return {}
        if str(stage) not in self.campaigns_workflow[campaigns_name][campaign_id]:
            logger.log_event(f"Sequence {stage} is out of range for campaign {campaign_id} in {campaigns_name}.", "ERROR")
            return {}

        logger.log_logic_event(f"Retrieved data for stage {stage} in {campaigns_name} - {campaign_id}.", "INFO")
        return self.campaigns_workflow[campaigns_name][campaign_id][str(stage)]

    def update_stage_status(self, campaigns_name: str, campaign_id: str, stage: int, status: str) -> bool:
        """Update the status of the stage."""
        if campaigns_name not in self.campaigns_workflow:
            logger.log_event(f"Campaigns {campaigns_name} does not exist.", "ERROR")
            return False
        if campaign_id not in self.campaigns_workflow[campaigns_name]:
            logger.log_event(f"Campaign: {campaign_id} in {campaigns_name} does not exist.", "ERROR")
            return False
        if str(stage) not in self.campaigns_workflow[campaigns_name][campaign_id]:
            logger.log_event(f"Sequence {stage} is out of range for campaign {campaign_id} in {campaigns_name}.", "ERROR")
            return False

        if status not in self.CAMPAIGN_ALLOWED_STATUSES:
            logger.log_logic_event(f"Invalid status '{status}' for stage {stage} in campaign {campaigns_name} - {campaign_id}. Allowed statuses: {self.CAMPAIGN_ALLOWED_STATUSES}.", "ERROR")
            return False

        if self.campaigns_workflow[campaigns_name][campaign_id][str(stage)]["sequence_status"] != status:
            self.campaigns_workflow[campaigns_name][campaign_id][str(stage)]["sequence_status"] = status
            self.save_state()

        logger.log_logic_event(f"Updated stage {stage} in {campaigns_name} - {campaign_id} to status: {status}.", "INFO")
        return True

    def get_contact(self, campaigns_name: str, campaign_id: str, stage: int, contact_email: str) -> Dict:
        """Retrieve the contact data."""
        sequence = self.get_stage(campaigns_name, campaign_id, stage)

        if not sequence:
            return {}
        if contact_email not in sequence["contacts"]:
            logger.log_event(f"Contact email {contact_email} not found in sequence {stage} of campaign {campaign_id} in {campaigns_name}.", "ERROR")
            return {}

        logger.log_logic_event(f"Retrieved data for contact {contact_email} in stage {stage} of {campaigns_name} - {campaign_id}.", "INFO")
        return sequence["contacts"][contact_email]

    def update_contact_status(self, campaigns_name: str, campaign_id: str, stage: int, contact_email: str, status: str) -> bool:
        """Update the status of the contact."""
        sequence = self.get_stage(campaigns_name, campaign_id, stage)

        if not sequence:
            return False
        if contact_email not in sequence["contacts"]:
            logger.log_event(f"Contact email {contact_email} not found in sequence {stage} of campaign {campaign_id} in {campaigns_name}.", "ERROR")
            return False

        if status not in self.CONTACT_ALLOWED_STATUSES:
            logger.log_logic_event(f"Invalid status '{status}' for contact {contact_email} in stage {stage} of campaign {campaigns_name} - {campaign_id}. Allowed statuses: {self.CONTACT_ALLOWED_STATUSES}.", "ERROR")
            return False

        if sequence["contacts"][contact_email]["progress"] != status:
            sequence["contacts"][contact_email]["progress"] = status
            self.save_state()

        logger.log_logic_event(f"Updated contact {contact_email} in stage {stage} of {campaigns_name} - {campaign_id} to status: {status}.", "INFO")
        return True

    def get_current_stage(self, campaigns_name: str, campaign_id: str):
        """Get the current stage and total stage of the campaign."""
        campaign = self.get_campaign(campaigns_name, campaign_id)

        if not campaign:
            return 0, 0

        total_stage = len(campaign) - 1

        if campaign["campaign_status"] == "Not Started":
            return 1, total_stage

        for sequence_id in range(total_stage, 0, -1):
            if campaign[str(sequence_id)]["sequence_status"] != "Not Started":
                return sequence_id, total_stage

        return total_stage, total_stage

    def get_stage_template(self, campaigns_name: str, campaign_id: str, stage: int) -> Dict:
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

    def update_stage_start_time(self, campaigns_name: str, campaign_id: str, stage: int, new_time: datetime) -> bool:
        """Update the start time for the stage."""
        sequence = self.get_stage(campaigns_name, campaign_id, stage)

        if not sequence:
            return False

        sequence["start_time"] = new_time.isoformat(timespec='seconds')
        self.save_state()
        logger.log_logic_event(f"Updated start time for stage {stage} in {campaigns_name} - {campaign_id}.", "INFO")
        return True

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
            logger.log_event(f"Campaign {campaign_id} in {campaigns_name} has already started.", "WARNING")

        current_stage, total_stage = self.get_current_stage(campaigns_name, campaign_id)
        sequence = self.get_stage(campaigns_name, campaign_id, current_stage)

        if not sequence:
            logger.log_logic_event(f"Fail to start {campaigns_name} - {campaign_id} - {current_stage}.", "ERROR")
            return False

        for contact_email, contact in sequence["contacts"].items():
            if contact["progress"] != "Not Started":
                logger.log_event(f"Contact {contact} has already started located at sequence {current_stage}, campaign {campaign_id}, folder {campaigns_name}", "WARNING")
            self.update_contact_status(campaigns_name, campaign_id, current_stage, contact_email, "Pending")

        self.update_stage_status(campaigns_name, campaign_id, current_stage, "In Progress")
        self.update_campaign_status(campaigns_name, campaign_id, "In Progress")
        logger.log_event(f"Campaign {campaign_id} started.", "INFO")
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
                logger.log_event(f"Contact {contact} has already started located at sequence {current_stage}, campaign {campaign_id}, folder {campaigns_name}", "WARNING")
            self.update_contact_status(campaigns_name, campaign_id, next_stage, contact_email, "Pending")

        self.update_stage_status(campaigns_name, campaign_id, next_stage, "In Progress")
        logger.log_event(f"Started to next sequence {next_stage}, campaign {campaign_id}, folder {campaigns_name}.", "INFO")
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
        logger.log_event(f"Sequence {stage} completed, in campaign {campaign_id} folder {campaigns_name}.", "INFO")
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
        logger.log_event(f"Campaign {campaign_id} completed, in folder {campaigns_name} .", "INFO")
        return True

    def completed_all_campaigns(self, campaigns_name: str) -> bool:
        """Get all campaigns completed."""
        campaigns = self.get_campaigns(campaigns_name)

        if not campaigns:
            return False

        for campaign_id, _ in campaigns.items():
            campaign = self.get_campaign(campaigns_name, campaign_id)
            if campaign["campaign_status"] != "Completed":
                return False

        logger.log_event(f"All campaigns completed in folder {campaigns_name} .", "INFO")
        return True

    def save_state(self):
        """Save the current campaign state to the state file."""
        if self.load_file:
            Utils.save_json_file(self.store_file, self.campaigns_workflow)
            logger.log_logic_event("Saved campaign state to file.", "INFO")

    @staticmethod
    def delete_state(store_file: Union[str, Path]):
        """Delete the state file."""
        store_file = Path(store_file)
        if store_file.exists():
            store_file.unlink()
            logger.log_logic_event("Deleted campaign state file.", "INFO")
        else:
            logger.log_logic_event("Campaign state file not found.", "WARNING")

