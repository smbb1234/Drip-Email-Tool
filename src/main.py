import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Dict, Union

from watchdog.observers import Observer

# Add the project root directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, os.pardir)
sys.path.append(project_root)

# Switch working directory to "drip_email_tool"
os.chdir(project_root)

from config import config
from src.modules import logger
from src.modules import InputParser, CampaignManager, Scheduler, EmailSender, DataFolderHandler
from src.utils import Validator

# Wake-up event
event = threading.Event()

# Load added campaign data
def process_directory(path: Union[str, Path], **kwargs):
    try:
        new_schedule = Path(path)
        campaigns_name = datetime.strptime(
            f"{new_schedule.name}/{new_schedule.parents[0].name}/{new_schedule.parents[1].name}",
            "%d%a/%b/%Y"
        ).strftime("%d-%m-%Y")
        if not Validator.is_valid_structure(new_schedule):
            return
        campaigns_data = InputParser.build_campaign_data(new_schedule)

        scheduler = kwargs.get("scheduler")
        email_sender = kwargs.get("email_sender")

        if scheduler is None:
            logger.log_logic_event("Scheduler is not configured.", "ERROR")
            return

        if email_sender is None:
            logger.log_logic_event("Email sender is not configured.", "ERROR")
            return

        # Schedule campaigns
        if not scheduler.campaign_manager.add_campaigns(campaigns_data, campaigns_name):
            return

        if start_campaigns(
                scheduler=scheduler,
                campaigns_name=campaigns_name,
                action=lambda contacts, template, campaign_info: send_email_action(
                    contacts=contacts,
                    template=template,
                    campaign_info=campaign_info,
                    campaign_manager=scheduler.campaign_manager,
                    email_sender=email_sender
                )
        ):
            event.set()

    except Exception as e:
        logger.log_logic_event(f"{e}", "ERROR")

# Start the campaigns_name
def start_campaigns(scheduler: Scheduler = None, campaigns_name: str = None, action: callable = None) -> bool:
    if scheduler is None or campaigns_name is None or action is None:
        logger.log_logic_event("Scheduler, campaigns_name, or action is not configured.", "ERROR")
        return False

    for campaign_id, campaign in scheduler.campaign_manager.get_campaigns(campaigns_name).items():

        if not scheduler.schedule_campaign(campaigns_name=campaigns_name, campaign_id=campaign_id, action=action):
            logger.log_logic_event(f"Failed to schedule campaign {campaign_id} for {campaigns_name}.", "ERROR")
            return False


# Define email sending action
def send_email_action(
        contacts: Dict,
        template: Dict,
        campaign_info: list[str],
        campaign_manager: CampaignManager = None,
        email_sender : EmailSender = None
):
    if not campaign_manager:
        logger.log_logic_event(f"Campaign manager is not configured.", "ERROR")
        return False
    if not email_sender:
        logger.log_logic_event(f"Email sender is not configured.", "ERROR")
        return False

    campaigns_name, campaign_id, current_stage = campaign_info

    for contact_email, info in contacts.items():
        subject, content = EmailSender.build_email_content(
            campaign_template=template,
            contact_info=info
        )
        if not subject or not content:
            logger.log_event(f"Failed to build email content for {contact_email}, some fields may be missing.", "ERROR")
            continue
        logger.log_logic_event(f"Email has been generated and ready to be sent...", "INFO")

        # success = email_sender.send_email(
        #     recipients=[contact_email],
        #     subject=subject,
        #     content=content
        # )
        print([[contact_email],subject,content])
        success = True

        if success:
            logger.log_event(
                f"Sent email to {contact_email} for {info['info']['name']} on Campaign Name: {campaign_id} from folder: {campaigns_name}, during sequence {current_stage}.")
            campaign_manager.update_contact_status(
                campaigns_name,
                campaign_id,
                int(current_stage),
                contact_email,
                "Email Sent"
            )
            event.set()

        else:
            logger.log_logic_event(
                f"Failed to send email to {contact_email} for {campaigns_name} - {campaign_id}, stage {current_stage}.",
                "ERROR")

def main():
    # Directories to monitor
    data_directory = Path(config.DATA_DIR)

    logger.log_event("Application initialization")

    scheduler: Union[Scheduler, None] = None
    observer: Union[Observer, None] = None

    # Load campaign data
    try:

        # Get all exist schedules in data directory
        schedules_directory: list[Path] = list(data_directory.rglob(config.SCHEDULE_FILE_NAME))

        # Initialize EmailSender
        email_sender = EmailSender()

        campaign_manager = CampaignManager()
        scheduler = Scheduler(campaign_manager)

        # Creating a file monitoring
        observer = Observer()
        observer.schedule(
            DataFolderHandler(
                process_directory,
                scheduler=scheduler,
                email_sender=email_sender
            ),
            path=str(data_directory),
            recursive=True
        )

        # Start file monitoring
        observer.start()

        if scheduler is None:
            logger.log_logic_event("Scheduler is not configured.", "ERROR")
            raise Exception("Scheduler is not configured.")

        for schedule in schedules_directory:
            campaigns_name = datetime.strptime(
                f"{schedule.parents[0].name}/{schedule.parents[1].name}/{schedule.parents[2].name}",
                "%d%a/%b/%Y"
            ).strftime("%d-%m-%Y")
            if not Validator.is_valid_structure(schedule.parent):
                continue
            campaigns_data = InputParser.build_campaign_data(schedule.parent)

            # Schedule campaigns
            if not campaign_manager.add_campaigns(campaigns_data, campaigns_name):
                logger.log_business_event(f"Failed to add campaigns from {schedule.parent.resolve()}.")
                continue

            if start_campaigns(
                scheduler=scheduler,
                campaigns_name=campaigns_name,
                action=lambda contacts, template, campaign_info: send_email_action(
                    contacts=contacts,
                    template=template,
                    campaign_info=campaign_info,
                    campaign_manager=campaign_manager,
                    email_sender=email_sender
                )
            ):
                continue

        if scheduler.campaign_manager.campaigns_workflow == {}:
            logger.log_business_event("Please adding campaigns.")
        logger.log_event("Application running. Press Ctrl+C to exit.")

        # Run scheduler
        scheduler.run_scheduler()

        while True:
            event.wait()
            sleep(2)

            for campaigns_name, _ in scheduler.campaign_manager.campaigns_workflow.copy().items():

                for campaign_id, campaign in scheduler.campaign_manager.get_campaigns(campaigns_name).items():
                    current_stage, _ = scheduler.campaign_manager.get_current_stage(campaigns_name, campaign_id)

                    if not scheduler.campaign_manager.completed_stage(campaigns_name, campaign_id, current_stage):
                        continue

                    if not scheduler.campaign_manager.completed_campaign(campaigns_name, campaign_id):

                        if not scheduler.schedule_next_stage(
                                campaigns_name=campaigns_name,
                                campaign_id=campaign_id,
                                action=lambda contacts, template, campaign_info: send_email_action(
                                    contacts=contacts,
                                    template=template,
                                    campaign_info=campaign_info,
                                    campaign_manager=scheduler.campaign_manager,
                                    email_sender=email_sender
                                )
                        ):
                            logger.log_logic_event(
                                f"Failed to schedule next stage for {campaign_id} in {campaigns_name}.", "ERROR")

                        continue

                    scheduler.remove_task(campaigns_name, campaign_id, current_stage)

                if scheduler.campaign_manager.completed_all_campaigns(campaigns_name):
                    scheduler.campaign_manager.del_campaigns(campaigns_name)

            if scheduler.campaign_manager.campaigns_workflow == {}:
                logger.log_business_event("Please adding campaigns.")

            event.clear()

    except (KeyboardInterrupt, SystemExit):
        raise KeyboardInterrupt
    except Exception as e:
        logger.log_logic_event(f"An error occurred: {e}", "ERROR")
    finally:
        if scheduler:
            scheduler.shutdown_scheduler()

        if observer:
            observer.stop()
            observer.join()

        exit(1)

if __name__ == "__main__":
    main()