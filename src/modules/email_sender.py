from typing import List

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

from config import config
from src.modules import logger
from src.utils import Validator


class EmailSender:
    """Class to handle sending emails using SendGrid."""

    def __init__(self):
        """Initialize the EmailSender with sender's email address."""
        self.client = boto3.client('ses', region_name=config.AWS_REGION)

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
            sender = sender or config.SENDER_EMAIL
            if not sender:
                logger.log_logic_event("Sender email is not configured.", "ERROR")
                return False
            if not Validator.validate_email_format(sender):
                logger.log_logic_event("Invalid sender email format.", "ERROR")
                return False
            for recipient in recipients:
                if not Validator.validate_email_format(recipient):
                    logger.log_logic_event("Invalid recipient email format.", "ERROR")
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
                            'Charset': config.CHARSET,
                            'Data': content,
                        },
                        'Text': {
                            'Charset': config.CHARSET,
                            'Data': content,
                        },
                    },
                    'Subject': {
                        'Charset': config.CHARSET,
                        'Data': subject,
                    },
                },
                Source=sender
            )

            if 200 <= response['ResponseMetadata']['HTTPStatusCode'] < 300:
                logger.log_logic_event(f"Email successfully sent to {recipients}.", "INFO")
                return True
            else:
                logger.log_logic_event(f"Failed to send email. Status code: {response['ResponseMetadata']['HTTPStatusCode']}", "ERROR")
                return False
        except NoCredentialsError:
            logger.log_logic_event("AWS credentials not found.", "ERROR")
            return False
        except PartialCredentialsError:
            logger.log_logic_event("AWS credentials are incomplete.", "ERROR")
            return False
        except ClientError as e:
            logger.log_logic_event(f"An error occurred while sending email to {recipients}: {e.response['Error']['Message']}", "ERROR")
            return False
        except Exception as e:
            logger.log_logic_event(f"An error occurred: {e}", "ERROR")
            return False

    @staticmethod
    def build_email_content(campaign_template: dict, contact_info: dict) -> (str, str):
        """Generate email content using a template and contact details.

        Args:
            campaign_template (dict): The template containing placeholders.
            contact_info (dict): The contact details to fill in the placeholders.

        Returns:
            str: The generated email subject and content.
        """
        try:
            _subject = campaign_template["subject"]
            _content = campaign_template["content"]

            if not _subject or not _content:
                logger.log_logic_event("Subject or content not found in template.", "ERROR")
                return "", ""

            replaceable_vars = contact_info["info"]

            # Check if all placeholders are existed
            if not Validator.check_placeholders_all_exist(set(campaign_template["placeholders"]["subject"]), set(replaceable_vars.keys())):
                logger.log_logic_event(f"Subject missing placeholders", "ERROR")
                return "", ""
            if not Validator.check_placeholders_all_exist(set(campaign_template["placeholders"]["content"]), set(replaceable_vars.keys())):
                logger.log_logic_event(f"Content missing placeholders", "ERROR")
                return "", ""

            # Replace placeholders with contact details
            _subject = _subject.format(**replaceable_vars)
            _content = _content.format(**replaceable_vars)
            return _subject, _content

        except Exception as e:
            logger.log_logic_event(f"An error occurred while building email content: {e}", "ERROR")
            return "", ""
