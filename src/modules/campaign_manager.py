from datetime import datetime
from pathlib import Path
from typing import Dict, Union

from config import config
from src.modules import logger
from src.utils import Utils


class CampaignManager:
    """Manage email campaigns and track their progress."""
    CONTACT_ALLOWED_STATUSES = {"Not Started", "Skip", "Pending", "Email Sent", "Reply Received", "Closed"}
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

        if campaigns_data is None or campaigns_data == {}:
            logger.log_event("No campaign data provided.", "ERROR")
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

        for sequence_id in range(1, total_stage + 1):
            if campaign[str(sequence_id)]["sequence_status"] != "Completed":
                return sequence_id, total_stage
            continue

        return total_stage, total_stage

    def get_stage_template(self, campaigns_name: str, campaign_id: str, stage: int) -> Dict:
        """Get the template for the current stage of a campaign."""
        sequence = self.get_stage(campaigns_name, campaign_id, stage)

        if not sequence:
            return {}

        return sequence["template"]

    def get_stage_start_time(self, campaigns_name: str, campaign_id: str, stage: int):
        """Get the start time for the stage."""
        sequence = self.get_stage(campaigns_name, campaign_id, stage)

        if not sequence:
            return None

        return datetime.fromisoformat(sequence["start_time"])

    def is_end_of_stage(self, campaigns_name: str, campaign_id: str) -> bool:
        """Check if the stage is the last stage in the campaign."""
        current_stage, total_stage = self.get_current_stage(campaigns_name, campaign_id)

        if current_stage == 0 or total_stage == 0:
            return False

        return current_stage >= total_stage

    def start_campaign(self, campaigns_name: str, campaign_id: str) -> bool:
        """Start the campaign by updating its status."""
        campaign = self.get_campaign(campaigns_name, campaign_id)

        if not campaign:
            return False

        if campaign["campaign_status"] != "Not Started":
            logger.log_event(f"Campaign {campaign_id} in {campaigns_name} has already started.", "WARNING")
        else:
            self.update_campaign_status(campaigns_name, campaign_id, "In Progress")

        current_stage, total_stage = self.get_current_stage(campaigns_name, campaign_id)
        sequence = self.get_stage(campaigns_name, campaign_id, current_stage)

        if not sequence:
            logger.log_logic_event(f"Fail to start {campaigns_name} - {campaign_id} - {current_stage}.", "ERROR")
            return False

        for contact_email, contact in sequence["contacts"].items():
            if contact["progress"] != "Not Started":
                logger.log_event(
                    f"Contact {contact['info']['name']} has already started located at sequence {current_stage}, campaign {campaign_id}, folder {campaigns_name}",
                    "WARNING")
                continue
            self.update_contact_status(campaigns_name, campaign_id, current_stage, contact_email, "Pending")

        self.update_stage_status(campaigns_name, campaign_id, current_stage, "In Progress")

        logger.log_event(f"Campaign {campaign_id} started.", "INFO")
        return True

    def completed_stage(self, campaigns_name: str, campaign_id: str, stage: int) -> bool:
        """Get all stages completed."""
        sequence = self.get_stage(campaigns_name, campaign_id, stage)

        if not sequence:
            return False

        for _, contact in sequence["contacts"].items():
            if contact["progress"] not in {
                "Skip",
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
        logger.log_event(f"Campaign {campaign_id} completed, in folder {campaigns_name}.", "INFO")
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


if __name__ == "__main__":
    load_file = False

    from src.modules import InputParser

    data_directory = Path("../../data/2025/Jan/12Sun")

    campaigns_name = "12-01-2025"
    example_campaigns1 = InputParser.build_campaign_data(data_directory)
    manager = CampaignManager(example_campaigns1, campaigns_name, load_file, "campaigns.json")

    example_campaigns2 = InputParser.build_campaign_data(data_directory)
    print(manager.add_campaigns(example_campaigns2, "12-02-2025"))

    print(f"get_campaigns: {manager.get_campaigns(campaigns_name)}")
    print(manager.get_campaign(campaigns_name, "20Mon2025_AIML"))
    print(manager.get_stage(campaigns_name, "20Mon2025_AIML", 1))
    print(manager.get_contact(campaigns_name, "20Mon2025_AIML", 1, "john.doe@example.com"))

    print(manager.get_current_stage(campaigns_name, "20Mon2025_AIML"))
    print(manager.start_campaign(campaigns_name, "20Mon2025_AIML"))
    print(manager.get_campaign(campaigns_name, "20Mon2025_AIML"))

    print(manager.start_campaign(campaigns_name, "21Mon2025_AIML"))
    print(manager.get_campaign(campaigns_name, "21Mon2025_AIML"))

    print(manager.get_current_stage(campaigns_name, "20Mon2025_AIML"))
    print(manager.get_stage_template(campaigns_name, "20Mon2025_AIML", 2))
    print(manager.get_stage_start_time(campaigns_name, "20Mon2025_AIML", 2))
    print(manager.is_end_of_stage(campaigns_name, "20Mon2025_AIML"))
    print(manager.get_current_stage(campaigns_name, "21Mon2025_AIML"))

    print(manager.update_stage_status(campaigns_name, "20Mon2025_AIML", 1, "Completed"))
    print(manager.update_stage_status(campaigns_name, "20Mon2025_AIML", 2, "Completed"))
    print(manager.completed_campaign(campaigns_name, "20Mon2025_AIML"))
