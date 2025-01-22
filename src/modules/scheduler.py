from datetime import datetime, timedelta
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import config
from src.modules import logger, CampaignManager


class Scheduler:
    def __init__(self, campaign_manager: CampaignManager):
        """Initialize the scheduler with a CampaignManager instance."""
        self.campaign_manager = campaign_manager
        self.scheduler = BackgroundScheduler()

    def schedule_campaign(self, campaigns_name: str, campaign_id: str, action: Callable) -> bool:
        """Schedule a campaign to start."""
        try:
            if not self.campaign_manager.start_campaign(campaigns_name, campaign_id):
                return False

            current_stage, total_stage = self.campaign_manager.get_current_stage(campaigns_name, campaign_id)

            if not self.add_task(campaigns_name, campaign_id, current_stage, action):
               logger.log_logic_event(f"Failed to schedule {campaigns_name} - {campaign_id} - {current_stage}.", "ERROR")
               return False

            start_time = self.campaign_manager.get_stage_start_time(campaigns_name, campaign_id, current_stage)

            logger.log_logic_event(f"Scheduling {campaigns_name} - {campaign_id} - {current_stage} to start at {datetime.isoformat(start_time)}. Total stage: {total_stage}.",
                      "INFO")

            self.campaign_manager.update_stage_status(campaigns_name, campaign_id, current_stage, "In Progress")
            return True
        except Exception as e:
            logger.log_logic_event(f"Failed to schedule {campaigns_name} - {campaign_id}: {e}", "ERROR")
            return False

    def schedule_next_stage(self, campaigns_name: str, campaign_id: str, action: Callable) -> bool:
        """Schedule the next email of stage in a campaign."""
        try:
            if not self.campaign_manager.get_campaign(campaigns_name, campaign_id):
                return False

            current_stage, total_stage = self.campaign_manager.get_current_stage(campaigns_name, campaign_id)

            self.remove_task(campaigns_name, campaign_id, current_stage)

            if not self.campaign_manager.move_to_next_stage(campaigns_name, campaign_id):
                self.campaign_manager.update_stage_status(campaigns_name, campaign_id, current_stage, "Completed")
                return False

            current_stage, _ = self.campaign_manager.get_current_stage(campaigns_name, campaign_id)

            if not self.add_task(campaigns_name, campaign_id, current_stage, action):
               logger.log_logic_event(f"Failed to schedule {campaigns_name} - {campaign_id} - {current_stage}.", "ERROR")
               return False

            start_time = self.campaign_manager.get_stage_start_time(campaigns_name, campaign_id, current_stage)

            logger.log_logic_event(f"Scheduling {campaigns_name} - {campaign_id} - {current_stage} to start at {datetime.isoformat(start_time)}. Total stage: {total_stage}.",
                      "INFO")

            self.campaign_manager.update_stage_status(campaigns_name, campaign_id, current_stage, "In Progress")
            return True

        except Exception as e:
            logger.log_logic_event(f"Failed to schedule next stage for {campaigns_name} - {campaign_id}: {e}", "ERROR")
            return False

    def add_task(self, campaigns_name: str, campaign_id: str, stage: int, action: Callable) -> bool:
        """Add a task to the scheduler."""
        try:
            if not self.campaign_manager.get_campaign(campaigns_name, campaign_id):
                logger.log_logic_event(f"Failed to add task for {campaigns_name} - {campaign_id} - {stage}: Campaign not found.", "ERROR")
                return False

            _, total_stage = self.campaign_manager.get_current_stage(campaigns_name, campaign_id)
            if stage == 0 or total_stage == 0 or stage > total_stage:
                logger.log_logic_event(f"Failed to add task for {campaigns_name} - {campaign_id} - {stage}: Invalid stage.", "ERROR")
                return False
            sequence = self.campaign_manager.get_stage(campaigns_name, campaign_id, stage)

            start_time = self.campaign_manager.get_stage_start_time(campaigns_name, campaign_id, stage)
            if start_time == "":
                logger.log_logic_event(
                    f"Failed to add task for {campaigns_name} - {campaign_id} - {stage}: Start time not found.",
                    "ERROR")

            self.scheduler.add_job(
                action,
                trigger=IntervalTrigger(
                    start_date=start_time,
                    minutes=config.RETRY_INTERVAL
                ),
                args=[
                    sequence["contacts"],
                    sequence["template"],
                    [campaigns_name, campaign_id, stage]
                ],
                id=f"{campaigns_name}_{campaign_id}_{stage}",
                name=f"Task: {campaigns_name}_{campaign_id}_{stage}"
            )
            logger.log_event(f"The task is scheduled to start on {start_time.isoformat(timespec='seconds')}, in sequence {stage} campaign {campaign_id} folder {campaigns_name}.", "INFO")
            return True
        except Exception as e:
            logger.log_logic_event(f"Failed to add task for {campaigns_name} - {campaign_id} - {stage}: {e}", "ERROR")
            return False

    def remove_task(self, campaigns_name: str, campaign_id: str, stage: int) -> bool:
        """Remove a task from the scheduler."""
        try:
            if not self.campaign_manager.get_campaign(campaigns_name, campaign_id):
                logger.log_logic_event(f"Failed to remove task for {campaigns_name} - {campaign_id} - {stage}: Campaign not found.", "ERROR")
                return False

            if self.scheduler.get_job(f"{campaigns_name}_{campaign_id}_{stage}"):
                self.scheduler.remove_job(f"{campaigns_name}_{campaign_id}_{stage}")
                logger.log_logic_event(f"Task removed for {campaigns_name} - {campaign_id} - {stage}.", "INFO")
                return True
            logger.log_logic_event(f"Failed to remove task for {campaigns_name} - {campaign_id} - {stage}: Task not found.", "ERROR")
            return False
        except Exception as e:
            logger.log_logic_event(f"Failed to remove task for {campaigns_name} - {campaign_id} - {stage}: {e}", "ERROR")
            return False

    def run_scheduler(self):
        """Run the scheduler."""
        self.scheduler.start()
        logger.log_logic_event("Scheduler started.", "INFO")

    def shutdown_scheduler(self):
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.log_logic_event("Scheduler shutdown.", "INFO")

if __name__ == "__main__":
    from src.modules import InputParser
    import os
    from pathlib import Path
    from time import sleep
    from src.modules import Logger

    logger = Logger("../../logs/")

    def test_action(*args):
        print(f"{datetime.now()}: {args}, ")

    def test_datetime(delay: int):
        return datetime.now() + timedelta(seconds=delay)

    try:
        if os.path.exists("campaigns.json"):
            CampaignManager.delete_state("campaigns.json")

        example_data = InputParser.build_campaign_data(Path("../../data/12-01-2025"))
        manager = CampaignManager(example_data, "12-01-2025", True, "campaigns.json")
        scheduler = Scheduler(manager)

        manager.campaigns_workflow["12-01-2025"]["campaign_1"]["1"]["start_time"] = test_datetime(5).isoformat(timespec='seconds')
        manager.campaigns_workflow["12-01-2025"]["campaign_1"]["2"]["start_time"] = test_datetime(10).isoformat(timespec='seconds')
        manager.campaigns_workflow["12-01-2025"]["campaign_3"]["1"]["start_time"] = test_datetime(2).isoformat(timespec='seconds')

        # Schedule campaign starts
        scheduler.schedule_campaign("12-01-2025", "campaign_1", test_action)
        scheduler.schedule_campaign("12-01-2025", "campaign_3", test_action)

        print(f"Scheduler start at {datetime.now()}")
        scheduler.run_scheduler()
        logger.log_logic_event("Scheduler running. Press Ctrl+C to exit.", "INFO")
        try:
            while True:
                sleep(7)
                scheduler.schedule_next_stage("12-01-2025", "campaign_3", test_action)
                if not scheduler.schedule_next_stage("12-01-2025", "campaign_1", test_action):
                    break

        except (KeyboardInterrupt, SystemExit):
            raise KeyboardInterrupt
        finally:
            scheduler.shutdown_scheduler()
            exit(1)

    except Exception as e:
        logger.log_logic_event(f"Failed to initialize scheduler: {e}", "ERROR")
        raise