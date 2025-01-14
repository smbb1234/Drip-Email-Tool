import logging
import os
import sys
from pathlib import Path
from time import sleep
from typing import Dict


# Add the project root directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, os.pardir)
sys.path.append(project_root)

# Switch working directory to "drip_email_tool"
os.chdir(project_root)

from src.modules import InputParser, CampaignManager, Scheduler, EmailSender, initialize_logger, log_event

# Define email sending action
def send_email_action(
        contacts: Dict,
        template: Dict,
        campaign_info: list[str],
        custom_vars: Dict = None,
        campaign_manager: CampaignManager = None,
        email_sender : EmailSender = None
):
    if not campaign_manager:
        log_event(f"Campaign manager is not configured.", "ERROR")
        return False
    if not email_sender:
        log_event(f"Email sender is not configured.", "ERROR")
        return False

    campaigns_name, campaign_id, current_stage = campaign_info

    for contact_email, info in contacts.items():
        subject, content = EmailSender.build_email_content(
            campaign_template=template,
            contact_info=info,
            custom_vars=custom_vars
        )
        log_event(f"Email has been generated and ready to be sent...", "INFO")

        # success = email_sender.send_email(
        #     recipients=[contact_email],
        #     subject=subject,
        #     content=content
        # )
        print([[contact_email],subject,content])
        success = True

        if success:
            log_event(
                f"Sent email to {contact_email} for {campaigns_name} - {campaign_id}, stage {current_stage}.",
                "INFO")
            campaign_manager.update_contact_status(
                campaigns_name,
                campaign_id,
                int(current_stage),
                contact_email,
                "Email Sent"
            )
        else:
            log_event(
                f"Failed to send email to {contact_email} for {campaigns_name} - {campaign_id}, stage {current_stage}.",
                "ERROR")

def main():

    data_directory = Path("data/")
    load_file = False
    store_file = "src/campaigns.json"

    default_sender = "ramya@DiagonalMatrix.com"

    # Get all schedules directory
    schedules_directory = []
    items = os.listdir(data_directory)
    for item in items:
        item_path = data_directory / item
        if os.path.isdir(item_path):
            schedules_directory.append(str(item_path))

    initialize_logger(log_path=os.getcwd()+"/logs", log_level=logging.WARNING)
    log_event("Starting the application...", "INFO")

    # Initialize EmailSender
    email_sender = EmailSender(default_sender)
    scheduler = None

    # Load campaign data
    try:
        if not load_file and os.path.exists("src/campaigns.json"):
            CampaignManager.delete_state("src/campaigns.json")

        campaigns_path, campaigns_name = os.path.split(schedules_directory[0])

        campaign_data = InputParser.build_campaign_data(Path(schedules_directory[0]))
        campaign_manager = CampaignManager(campaign_data, campaigns_name, load_file, store_file)
        scheduler = Scheduler(campaign_manager)

        # Schedule campaigns
        for campaign_id, campaign in campaign_manager.get_campaigns(campaigns_name).items():
            scheduler.schedule_campaign(
                campaigns_name=campaigns_name,
                campaign_id=campaign_id,
                action=lambda contacts, template, campaign_info: send_email_action(
                    contacts,
                    template,
                    campaign_info,
                    custom_vars={"topic": "Future"},
                    campaign_manager=campaign_manager,
                    email_sender=email_sender
                )
            )

        log_event("Scheduler running. Press Ctrl+C to exit.", "INFO")
        print("Scheduler running. Press Ctrl+C to exit.")

        scheduler.run_scheduler()

        while True:
            sleep(10)
            for campaign_id, campaign in campaign_manager.get_campaigns(campaigns_name).items():
                current_stage, _ = campaign_manager.get_current_stage(campaigns_name, campaign_id)
                if campaign_manager.completed_stage(campaigns_name, campaign_id, current_stage):
                    if not campaign_manager.completed_campaign(campaigns_name, campaign_id):
                        scheduler.schedule_next_stage(
                            campaigns_name=campaigns_name,
                            campaign_id=campaign_id,
                            action=lambda contacts, template, campaign_info: send_email_action(
                                contacts,
                                template,
                                campaign_info,
                                custom_vars={"topic": "Future"},
                                campaign_manager=campaign_manager,
                                email_sender=email_sender
                            )
                        )
                        continue
                    continue

            if campaign_manager.completed_all_campaigns(campaigns_name):
                raise Exception("All campaigns have been completed.")

    except (KeyboardInterrupt, SystemExit):
        raise KeyboardInterrupt
    except Exception as e:
        log_event(f"An error occurred: {e}", "ERROR")
    finally:
        if scheduler:
            scheduler.shutdown_scheduler()
        exit(1)

if __name__ == "__main__":
    main()