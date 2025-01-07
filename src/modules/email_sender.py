import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from src.modules import log_event
from src.utils import Validator

class EmailSender:
    """Class to handle sending emails using SendGrid."""

    def __init__(self, sender_email: str):
        """Initialize the EmailSender with sender's email address."""
        self.client = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        self.sender_email = sender_email

    def send_email(self, recipient: str, subject: str, content: str, sender: str = None) -> bool:
        """Send an email using SendGrid.

        Args:
            recipient (str): The recipient's email address.
            subject (str): The subject of the email.
            content (str): The content/body of the email.
            sender (str, optional): The sender's email address. Defaults to a configured sender.

        Returns:
            bool: True if the email is sent successfully, False otherwise.
        """
        try:
            sender = sender or self.sender_email
            if not sender:
                log_event("Sender email is not configured.", "ERROR")
                return False

            if not Validator.validate_email_format(sender):
                log_event("Invalid sender email format.", "ERROR")
                return False

            if not Validator.validate_email_format(recipient):
                log_event("Invalid recipient email format.", "ERROR")
                return False

            message = Mail(
                from_email=sender,
                to_emails=recipient,
                subject=subject,
                html_content=content
            )
            response = self.client.send(message)

            if 200 <= response.status_code < 300:
                log_event(f"Email successfully sent to {recipient}.", "INFO")
                return True
            else:
                log_event(f"Failed to send email to {recipient}. Status code: {response.status_code}", "ERROR")
                return False

        except Exception as e:
            log_event(f"An error occurred while sending email to {recipient}: {e}", "ERROR")
            return False

    @staticmethod
    def build_email_content(campaign_template: dict, contact: dict, custom_vars: dict = None) -> (str, str):
        """Generate email content using a template and contact details.

        Args:
            campaign_template (dict): The template containing placeholders.
            contact (dict): The contact details to fill in the placeholders.
            custom_vars (dict, optional): Additional custom variables for placeholder replacement. Defaults to None.

        Returns:
            str: The generated email subject and content.
        """
        try:
            _subject = campaign_template.get("subject", "")
            _content = campaign_template.get("content", "")
            custom_vars = custom_vars or {}

            if not _subject or not _content:
                log_event("Subject or content not found in template.", "ERROR")
                return "", ""

            # Replace placeholders with contact details
            for key, value in {**contact["info"], **custom_vars}.items():
                placeholder = f"{{{key}}}"
                _subject = _subject.replace(placeholder, str(value))
                _content = _content.replace(placeholder, str(value))

            return _subject, _content
        except Exception as e:
            log_event(f"An error occurred while building email content: {e}", "ERROR")
            return "", ""

if __name__ == "__main__":
    from src.modules import CampaignManager
    from src.modules import InputParser

    templates_file = "../../config/sample_templates.yaml"
    schedule_file = "../../config/sample_schedule.json"

    try:
        templates = InputParser.load_templates(templates_file)
        schedule = InputParser.load_schedule(schedule_file)
        contacts = [
            {"name": "Steve Jia", "email": "jbl1990926@gmail.com"}
        ]

        campaign_data = CampaignManager.build_campaign_data(
            contacts,
            templates,
            schedule
        )
        manager = CampaignManager(campaign_data)

        target_user = manager.get_contact_campaign_status("campaign_1", contacts[0]["email"])
        subject, content = EmailSender.build_email_content(
            manager.get_current_stage_template("campaign_1",
                                               target_user["current_stage"]),
            target_user,
            {"topic": "Future"}
        )

        print(f"Subject: {subject}\nContent: {content}")

        if not os.getenv("SENDGRID_API_KEY"):
            log_event("SendGrid API key is not configured.", "ERROR")
            exit(1)

        email_sender = EmailSender("peter_926@live.cn")

        # Example email details
        # recipient_email = "jbl1990926@gmail.com"
        # subject = "Welcome to Our Service"
        # content = "<h1>Hello!</h1><p>Thank you for signing up.</p>"

        success = email_sender.send_email(
            recipient=contacts[0]["email"],
            subject=subject,
            content=content
        )

        if success:
            log_event("Email was sent successfully.", "INFO")
        else:
            log_event("Email failed to send.", "ERROR")

    except Exception as e:
        log_event(f"Failed to load input data: {e}", "ERROR")
        exit(1)
