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

    def schedule_campaign(self, campaign_id: str, campaign_start_time: str, action: Callable) -> bool:
        """Schedule a campaign to start at the specified time."""
        try:
            start_datetime = datetime.fromisoformat(campaign_start_time)
            if start_datetime <= datetime.now():
                log_event(f"Start time for campaign {campaign_id} has already passed.", "WARNING")
                return False

            log_event(f"Scheduling campaign {campaign_id} to start at {campaign_start_time}.", "INFO")

            _contacts = self.campaign_manager.get_all_contacts(campaign_id)
            for contact_email, _ in _contacts.items():
                current_stage = self.campaign_manager.get_current_stage(campaign_id, contact_email)
                if datetime.fromisoformat(current_stage["start_time"]) <= start_datetime:
                    current_stage["start_time"] = start_datetime.isoformat()

                self.scheduler.add_job(
                    action,
                    trigger=IntervalTrigger(
                        days=current_stage["interval"],
                        start_date=datetime.fromisoformat(current_stage["start_time"])
                    ),
                    args=[
                        campaign_id,
                        contact_email,
                        self.campaign_manager.get_campaign_status(campaign_id)
                    ],
                    id=f"{campaign_id}_{contact_email}"
                )
                self.campaign_manager.update_contact_campaign_status(campaign_id, contact_email, "Pending")

            self.campaign_manager.start_campaign(campaign_id)
            return True
        except Exception as e:
            log_event(f"Failed to schedule campaign {campaign_id}: {e}", "ERROR")
            return False

    def schedule_next_email(self, campaign_id: str, contact_email: str, action: Callable, delay: int = 0) -> bool:
        """Schedule the next email of stage for a contact in a campaign."""
        try:
            current_campaign_contact = self.campaign_manager.get_contact_campaign_status(campaign_id, contact_email)

            if not self.campaign_manager.move_to_next_stage(campaign_id, contact_email):
                if not self.scheduler.get_job(f"{campaign_id}_{contact_email}"):
                    log_event(f"Job for contact {contact_email} in campaign {campaign_id} not found during removal.", "WARNING")
                    return False
                self.scheduler.remove_job(f"{campaign_id}_{contact_email}")
                self.campaign_manager.update_contact_campaign_status(campaign_id, contact_email, "Closed")
                return False

            current_campaign_stage = self.campaign_manager.get_current_stage(campaign_id, contact_email)
            start_datetime = datetime.fromisoformat(
                current_campaign_stage["start_time"]
            )

            if start_datetime <= datetime.now() + timedelta(days=delay):
                current_campaign_stage["start_time"] = (datetime.now() + timedelta(days=delay)).isoformat()

            log_event(f"Scheduling next email for {contact_email} in campaign {campaign_id} in {delay} days. Current/Total: {current_campaign_contact["current_stage"]}/{current_campaign_contact["total_stage"]}. Start Time: {current_campaign_stage['start_time']}", "INFO")

            if not self.scheduler.get_job(f"{campaign_id}_{contact_email}"):
                log_event(f"Job for contact {contact_email} in campaign {campaign_id} not found during removal.", "WARNING")
                return False
            self.scheduler.remove_job(f"{campaign_id}_{contact_email}")
            self.scheduler.add_job(
                action,
                trigger=IntervalTrigger(
                    days=current_campaign_stage["interval"],
                    start_date=datetime.fromisoformat(current_campaign_stage["start_time"])
                ),
                args=[
                    campaign_id,
                    contact_email,
                    self.campaign_manager.get_campaign_status(campaign_id)
                ],
                id=f"{campaign_id}_{contact_email}"
            )
            self.campaign_manager.update_contact_campaign_status(campaign_id, contact_email, "Pending")
            return True

        except Exception as e:
            log_event(f"Failed to schedule next email for {contact_email} in campaign {campaign_id}: {e}", "ERROR")
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
    from time import sleep
    # from src.modules import initialize_logger

    # initialize_logger()

    contacts_file = "../../config/sample_contacts.csv"
    templates_file = "../../config/sample_templates.yaml"
    schedule_file = "../../config/sample_schedule.json"

    def start_action(*args):
        print(f"Start action, {args[0]}, stage: {args[2]["contacts"][args[1]]["current_stage"]},{args[1]}, {args[2]["contacts"][args[1]]["progress"]}, {datetime.now()}")

    def email_action(*args):
        print(f"Email action, {args[0]}, stage: {args[2]["contacts"][args[1]]["current_stage"]}, {args[1]}, {args[2]["contacts"][args[1]]["progress"]}, {datetime.now()}")

    try:
        contacts = InputParser.load_contacts(contacts_file)
        templates = InputParser.load_templates(templates_file)
        schedule = [
          {
            "campaign_id": "campaign_1",
            "sequences": [
              {
                "sequence": 1,
                "start_time": (datetime.now() + timedelta(seconds=1)).isoformat(),
                "interval": 2
              },
              {
                "sequence": 2,
                "start_time": (datetime.now() + timedelta(seconds=2)).isoformat(),
                "interval": 3
              },
                {
                    "sequence": 3,
                    "start_time": (datetime.now() + timedelta(seconds=3)).isoformat(),
                    "interval": 4
                }
            ]
          },
            {
                "campaign_id": "campaign_2",
                "sequences": [
                {
                    "sequence": 1,
                    "start_time": (datetime.now() + timedelta(seconds=1)).isoformat(),
                    "interval": 2
                },
                {
                    "sequence": 2,
                    "start_time": (datetime.now() + timedelta(seconds=2)).isoformat(),
                    "interval": 3
                },
                    {
                        "sequence": 3,
                        "start_time": (datetime.now() + timedelta(seconds=3)).isoformat(),
                        "interval": 4
                    }
                ]
            }
        ]

        if os.path.exists("campaigns.json"):
            CampaignManager.delete_state("campaigns.json")

        campaign_data = CampaignManager.build_campaign_data(contacts, templates, schedule)
        manager = CampaignManager(campaign_data)
        scheduler = Scheduler(manager)

        # Schedule campaign starts
        for campaign in schedule:
            scheduler.schedule_campaign(campaign["campaign_id"],
                                        (datetime.now()+timedelta(seconds=1)).isoformat(),
                                        start_action)

        print(datetime.now())
        scheduler.run_scheduler()

        for campaign in schedule:
            sleep(5)
            for contact_email, _ in manager.get_all_contacts(campaign["campaign_id"]).items():
                scheduler.schedule_next_email(campaign["campaign_id"],
                                              contact_email,
                                              email_action)
                sleep(1)

        log_event("Scheduler running. Press Ctrl+C to exit.", "INFO")
        try:
            while True:
                for campaign in schedule:
                    sleep(7)
                    for contact_email, _ in manager.get_all_contacts(campaign["campaign_id"]).items():
                        scheduler.schedule_next_email(campaign["campaign_id"],
                                                      contact_email,
                                                      email_action)
                        sleep(1)

                if manager.completed_all_campaigns():
                    raise 'All campaigns completed.'
        except (KeyboardInterrupt, SystemExit):
            raise KeyboardInterrupt
        finally:
            scheduler.shutdown_scheduler()
            exit(1)

    except Exception as e:
        log_event(f"Failed to initialize scheduler: {e}", "ERROR")
        raise