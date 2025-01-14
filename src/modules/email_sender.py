import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from typing import List
from src.modules import log_event
from src.utils import Validator

class EmailSender:
    """Class to handle sending emails using SendGrid."""

    def __init__(self, sender_email: str):
        """Initialize the EmailSender with sender's email address."""
        self.AWS_REGION = "eu-west-2"
        self.client = boto3.client('ses', region_name=self.AWS_REGION)
        self.sender_email = sender_email
        self.CHARSET = "UTF-8"

    def send_email(self, recipients: List[str], subject: str, content: str, sender: str = None) -> bool:
        """Send an email using SendGrid.

        Args:
            recipients (str): The recipient's email addresses.
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
            for recipient in recipients:
                if not Validator.validate_email_format(recipient):
                    log_event("Invalid recipient email format.", "ERROR")
                    return False

            response = self.client.send_email(
                Destination={
                    'ToAddresses': [
                        *recipients,
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': self.CHARSET,
                            'Data': content,
                        },
                        'Text': {
                            'Charset': self.CHARSET,
                            'Data': content,
                        },
                    },
                    'Subject': {
                        'Charset': self.CHARSET,
                        'Data': subject,
                    },
                },
                Source=sender
            )

            if 200 <= response['ResponseMetadata']['HTTPStatusCode'] < 300:
                log_event(f"Email successfully sent to {recipients}.", "INFO")
                return True
            else:
                log_event(f"Failed to send email. Status code: {response['ResponseMetadata']['HTTPStatusCode']}", "ERROR")
                return False
        except NoCredentialsError:
            log_event("AWS credentials not found.", "ERROR")
            return False
        except PartialCredentialsError:
            log_event("AWS credentials are incomplete.", "ERROR")
            return False
        except ClientError as e:
            log_event(f"An error occurred while sending email to {recipients}: {e.response['Error']['Message']}", "ERROR")
            return False
        except Exception as e:
            log_event(f"An error occurred: {e}", "ERROR")
            return False

    # def get_email_states(self, params: dict):
    #
    #     try:
    #         response = self.client.client.stats.get(query_params=params)
    #         if response.status_code == 200:
    #             return response.to_dict
    #         else:
    #             log_event(f"Failed to fetch metrics: {response.status_code}, {response.text}", "ERROR")
    #     except Exception as e:
    #         log_event(f"An error occurred while fetching email metrics: {e}", "ERROR")

    @staticmethod
    def build_email_content(campaign_template: dict, contact_info: dict, custom_vars: dict = None) -> (str, str):
        """Generate email content using a template and contact details.

        Args:
            campaign_template (dict): The template containing placeholders.
            contact_info (dict): The contact details to fill in the placeholders.
            custom_vars (dict, optional): Additional custom variables for placeholder replacement. Defaults to None.

        Returns:
            str: The generated email subject and content.
        """
        try:
            _subject = campaign_template["subject"]
            _content = campaign_template["content"]
            custom_vars = custom_vars or {}

            if not _subject or not _content:
                log_event("Subject or content not found in template.", "ERROR")
                return "", ""

            replaceable_vars = {**contact_info["info"], **custom_vars}

            # Check if all placeholders are existed
            if not Validator.check_placeholders_all_exist(set(campaign_template["placeholders"]["subject"]), set(replaceable_vars.keys())):
                log_event(f"Subject missing placeholders", "ERROR")
                return "", ""
            if not Validator.check_placeholders_all_exist(set(campaign_template["placeholders"]["content"]), set(replaceable_vars.keys())):
                log_event(f"Content missing placeholders", "ERROR")
                return "", ""

            # Replace placeholders with contact details
            _subject = _subject.format(**replaceable_vars)
            _content = _content.format(**replaceable_vars)
            return _subject, _content

        except Exception as e:
            log_event(f"An error occurred while building email content: {e}", "ERROR")
            return "", ""

if __name__ == "__main__":
    from src.modules import CampaignManager
    from src.modules import InputParser
    from pathlib import Path

    try:
        example_data = InputParser.build_campaign_data(Path("../../data/12-01-2025"))
        manager = CampaignManager(example_data, "12-01-2025", "campaigns.json")

        target_user = manager.get_contact("12-01-2025", "campaign_1", 1,"john.doe@example.com")
        target_template = manager.get_stage_template("12-01-2025", "campaign_1", 1)

        subject, content = EmailSender.build_email_content(
            target_template,
            target_user,
            {"topic": "Future"}
        )

        print(f"Subject: {subject}\nContent: {content}")

        email_sender = EmailSender("ramya@DiagonalMatrix.com")

        # Example email details
        # recipient_email = "jbl1990926@gmail.com"
        # subject = "Welcome to Our Service"
        # content = "<h1>Hello!</h1><p>Thank you for signing up.</p>"

        recipients = [
            "john.doe@example.com"
        ]
        success = email_sender.send_email(recipients, subject, content)

        # params = {
        #     "start_date": "2025-01-07"
        # }
        # # Fetch email metrics
        # email_metrics = email_sender.get_email_states(params)
        # for metric in email_metrics:
        #     print(metric)

    except Exception as e:
        log_event(f"Failed to load input data: {e}", "ERROR")
        exit(1)