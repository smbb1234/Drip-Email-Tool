import os
from src.modules import InputParser, CampaignManager, Scheduler, EmailSender, initialize_logger, log_event

def main():
    # Load environment variables
    EMAIL_API_KEY = os.getenv("SENDGRID_API_KEY")
    DEFAULT_SENDER = os.getenv("DEFAULT_SENDER_EMAIL")
    CONTACTS_FILE = "config/contacts.csv"
    TEMPLATES_FILE = "config/templates.yaml"
    SCHEDULE_FILE = "config/schedule.json"

    # Define email sending action
    def send_email_action(
            campaign_id,
            contact_email,
            campaign_status,
            campaign_manager : CampaignManager = None,
            email_sender : EmailSender = None
    ):
        if not email_sender or not campaign_manager:
            log_event(f"{campaign_id} - {contact_email}, Email sender or Campaign manager is not configured.", "ERROR")
            return False

        subject, content = EmailSender.build_email_content(
            campaign_template=campaign_manager.get_current_stage_template(campaign_id,
                                           campaign_status["contacts"][contact_email]["current_stage"]),
            contact=campaign_manager.get_contact_campaign_status(campaign_id, contact_email),
            custom_vars={}
        )
        log_event(f"Email has been generated and ready to be sent...", "INFO")

        success = email_sender.send_email(
            recipient=contact_email,
            subject=subject,
            content=content,
            sender=DEFAULT_SENDER
        )

        if success:
            log_event(f"Email sent to {contact_email} for campaign {campaign_id}, stage {campaign_status["contacts"][contact_email]["current_stage"]}.",
                      "INFO")
            campaign_manager.update_contact_campaign_status(campaign_id, contact_email, "Email Sent")
        else:
            log_event(f"Failed to send email to {contact_email} for campaign {campaign_id}, stage {campaign_status["contacts"][contact_email]["current_stage"]}.",
                      "ERROR")

    initialize_logger(os.getcwd()+"/logs")
    log_event("Starting the application...", "INFO")

    if not EMAIL_API_KEY:
        log_event("SendGrid API key is not configured.", "ERROR")
        return

    if not DEFAULT_SENDER:
        log_event("Default sender email is not configured.", "ERROR")
        return

    # Initialize EmailSender
    email_sender = EmailSender(DEFAULT_SENDER)

    # Load campaign data
    try:
        contacts = InputParser.load_contacts(CONTACTS_FILE)
        templates = InputParser.load_templates(TEMPLATES_FILE)
        schedule = InputParser.load_schedule(SCHEDULE_FILE)

        campaign_data = CampaignManager.build_campaign_data(
            contacts,
            templates,
            schedule
        )
        campaign_manager = CampaignManager(campaign_data)
        scheduler = Scheduler(campaign_manager)

        # Schedule campaigns
        for campaign_id, campaign in campaign_manager.campaigns.items():
            scheduler.schedule_campaign(
                campaign_id=campaign_id,
                campaign_start_time=campaign["schedule"][0]["start_time"],
                action=lambda cid, email, status: send_email_action(cid, email, status, campaign_manager, email_sender)
            )

        log_event("Scheduler running. Press Ctrl+C to exit.", "INFO")
        try:
            scheduler.run_scheduler()
            while True:
                for campaign_id, campaign in campaign_manager.campaigns.items():
                    for contact_email, contact in campaign["contacts"].items():
                        if contact["progress"] not in {
                            "Email Sent",
                            "Reply Received"
                        }:
                            continue
                        scheduler.schedule_next_email(
                            campaign_id=campaign_id,
                            contact_email=contact_email,
                            action=lambda cid, email, status: send_email_action(cid, email, status, campaign_manager, email_sender)
                        )

                if campaign_manager.completed_all_campaigns():
                    raise 'All campaigns completed.'
        except (KeyboardInterrupt, SystemExit):
            raise KeyboardInterrupt
        finally:
            scheduler.shutdown_scheduler()
            exit(1)
    except Exception as e:
        log_event(f"Error loading campaign data: {e}", "ERROR")
        return

if __name__ == "__main__":
    main()