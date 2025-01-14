from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from src.modules import log_event
from src.modules import CampaignManager
from typing import Callable

class Scheduler:
    def __init__(self, campaign_manager: CampaignManager):
        """Initialize the scheduler with a CampaignManager instance."""
        self.campaign_manager = campaign_manager
        self.scheduler = BackgroundScheduler()

    def schedule_campaign(self, campaigns_name: str, campaign_id: str, action: Callable) -> bool:
        """Schedule a campaign to start."""
        try:
            if not self.campaign_manager.get_campaign(campaigns_name, campaign_id):
                return False
            if not self.campaign_manager.start_campaign(campaigns_name, campaign_id):
                return False

            current_stage, total_stage = self.campaign_manager.get_current_stage(campaigns_name, campaign_id)
            sequence = self.campaign_manager.get_stage(campaigns_name, campaign_id, current_stage)

            start_time = self.campaign_manager.get_campaign_start_time(campaigns_name, campaign_id)
            if self.schedule_time_exceeded(start_time):
                log_event(
                    f"Start time {datetime.isoformat(start_time)} for {campaigns_name} - {campaign_id} - {current_stage} has already passed. Update to current time",
                    "WARNING")
                start_time = datetime.now() + timedelta(seconds=5)
                self.campaign_manager.update_stage_start_time(campaigns_name, campaign_id, current_stage, start_time)

            log_event(f"Scheduling {campaigns_name} - {campaign_id} to start at {datetime.isoformat(start_time)}.",
                      "INFO")

            self.scheduler.add_job(
                action,
                trigger=IntervalTrigger(
                    days=sequence["interval"],
                    start_date=datetime.fromisoformat(sequence["start_time"])
                ),
                args=[
                    sequence["contacts"],
                    sequence["template"],
                    [campaigns_name, campaign_id, current_stage]
                ],
                id=f"{campaigns_name}_{campaign_id}_{current_stage}"
            )

            self.campaign_manager.update_stage_status(campaigns_name, campaign_id, current_stage, "In Progress")
            return True
        except Exception as e:
            log_event(f"Failed to schedule {campaigns_name} - {campaign_id}: {e}", "ERROR")
            return False

    def schedule_next_stage(self, campaigns_name: str, campaign_id: str, action: Callable, delay: int = 0) -> bool:
        """Schedule the next email of stage in a campaign."""
        try:
            if not self.campaign_manager.get_campaign(campaigns_name, campaign_id):
                return False

            current_stage, total_stage = self.campaign_manager.get_current_stage(campaigns_name, campaign_id)

            if self.scheduler.get_job(f"{campaigns_name}_{campaign_id}_{current_stage}"):
                self.scheduler.remove_job(f"{campaigns_name}_{campaign_id}_{current_stage}")

            if not self.campaign_manager.move_to_next_stage(campaigns_name, campaign_id):
                self.campaign_manager.update_stage_status(campaigns_name, campaign_id, current_stage, "Completed")
                return False

            current_stage, _ = self.campaign_manager.get_current_stage(campaigns_name, campaign_id)
            start_time = self.campaign_manager.get_stage_start_time(campaigns_name, campaign_id, current_stage)
            if self.schedule_time_exceeded(start_time):
                log_event(f"Start time {datetime.isoformat(start_time)} for {campaigns_name} - {campaign_id} - {current_stage} has already passed. Update to current time", "WARNING")
                start_time = datetime.now() + timedelta(seconds=5)
                self.campaign_manager.update_stage_start_time(campaigns_name, campaign_id, current_stage, start_time)

            log_event(f"Scheduling {campaigns_name} - {campaign_id} - {current_stage} to start at {datetime.isoformat(start_time)}. Total stage: {total_stage}.",
                      "INFO")

            sequence = self.campaign_manager.get_stage(campaigns_name, campaign_id, current_stage)

            self.scheduler.add_job(
                action,
                trigger=IntervalTrigger(
                    days=sequence["interval"],
                    start_date=datetime.fromisoformat(sequence["start_time"])
                ),
                args=[
                    sequence["contacts"],
                    sequence["template"],
                    [campaigns_name, campaign_id, current_stage]
                ],
                id=f"{campaigns_name}_{campaign_id}_{current_stage}"
            )
            self.campaign_manager.update_stage_status(campaigns_name, campaign_id, current_stage, "In Progress")
            return True

        except Exception as e:
            log_event(f"Failed to schedule next stage for {campaigns_name} - {campaign_id}: {e}", "ERROR")
            return False

    def schedule_email(self, campaigns_name: str, campaign_id: str, stage: int, contact_email: str, action: Callable, delay: int = 0) -> bool:
        """Schedule an email for a contact At a stage of a campaign."""
        try:
            designated_stage = self.campaign_manager.get_stage(campaigns_name, campaign_id, stage)
            designated_contact = self.campaign_manager.get_contact(campaigns_name, campaign_id, stage, contact_email)

            if not designated_stage:
                return False
            if not designated_contact:
                return False

            delay_timedelta = timedelta(days=delay)
            start_datetime = delay_timedelta + datetime.fromisoformat(designated_stage["start_time"])

            if self.schedule_time_exceeded(start_datetime):
                log_event(f"Start time {datetime.isoformat(start_datetime)} for {contact_email} in {campaigns_name} - {campaign_id} - {stage} has already passed.", "WARNING")
                return False

            self.scheduler.add_job(
                action,
                trigger=IntervalTrigger(
                    days=designated_stage["interval"],
                    start_date=start_datetime
                ),
                args=[
                    [{contact_email: designated_contact["info"]}],
                    self.campaign_manager.get_stage_template(campaigns_name, campaign_id, stage)
                ],
                id=f"{campaigns_name}_{campaign_id}_{stage}_{contact_email}"
            )

            self.campaign_manager.update_contact_status(campaigns_name, campaign_id, stage, contact_email, "Pending")
            return True

        except Exception as e:
            log_event(f"Failed to schedule email for {contact_email} in {campaigns_name} - {campaign_id} - {stage}: {e}", "ERROR")
            return False

    @staticmethod
    def schedule_time_exceeded(input_time: datetime) -> bool:
        """Check if the input time has already passed."""
        if input_time <= datetime.now():
            return True
        return False


    def run_scheduler(self):
        """Run the scheduler."""
        self.scheduler.start()
        log_event("Scheduler started.", "INFO")

    def shutdown_scheduler(self):
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        log_event("Scheduler shutdown.", "INFO")

if __name__ == "__main__":
    from src.modules import InputParser
    import os
    from pathlib import Path
    from time import sleep
    from src.modules import initialize_logger

    initialize_logger("../../logs/", "scheduler.log")

    def test_action(*args):
        print(f"{datetime.now()}: {args}, ")

    def test_datetime(delay: int):
        return datetime.now() + timedelta(seconds=delay)

    try:
        if os.path.exists("campaigns.json"):
            CampaignManager.delete_state("campaigns.json")

        example_data = InputParser.build_campaign_data(Path("../../data/12-01-2025"))
        manager = CampaignManager(example_data, "12-01-2025", "campaigns.json")
        scheduler = Scheduler(manager)

        manager.campaigns_workflow["12-01-2025"]["campaign_1"][1]["start_time"] = test_datetime(5).isoformat()
        manager.campaigns_workflow["12-01-2025"]["campaign_1"][2]["start_time"] = test_datetime(10).isoformat()
        manager.campaigns_workflow["12-01-2025"]["campaign_3"][1]["start_time"] = test_datetime(2).isoformat()

        # Schedule campaign starts
        scheduler.schedule_campaign("12-01-2025", "campaign_1", test_action)
        scheduler.schedule_campaign("12-01-2025", "campaign_3", test_action)

        print(f"Scheduler start at {datetime.now()}")
        scheduler.run_scheduler()
        log_event("Scheduler running. Press Ctrl+C to exit.", "INFO")
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
        log_event(f"Failed to initialize scheduler: {e}", "ERROR")
        raise