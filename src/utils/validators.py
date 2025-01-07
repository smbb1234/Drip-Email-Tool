from src.modules import log_event
from typing import Dict

class Validator:

    @staticmethod
    def validate_email_format(email: str) -> bool:
        """Validate the format of an email address using a simple regex."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_campaign_data(campaign_data: Dict) -> bool:
        """Validate campaign data for required fields."""
        required_keys = {"contacts", "templates", "schedule"}
        for key in required_keys:
            if key not in campaign_data:
                log_event(f"Missing required field: {key}", "ERROR")
                return False

        for contact in campaign_data["contacts"]:
            if "name" not in contact or "email" not in contact:
                log_event("Each contact must have 'name' and 'email' fields.", "ERROR")
                return False

        for template in campaign_data["templates"]:
            if "sequence" not in template or "subject" not in template or "content" not in template:
                log_event("Each template must have 'sequence', 'subject', and 'content' fields.", "ERROR")
                return False

        for schedule in campaign_data["schedule"]:
            if "campaign_id" not in schedule or "sequences" not in schedule:
                log_event("Each schedule entry must have 'campaign_id' and 'sequences' fields.", "ERROR")
                return False

            if not schedule["sequences"]:
                log_event("The current campaign does not contain any stages.", "ERROR")
                return False
            else:
                for sequence in schedule["sequences"]:
                    if "sequence" not in sequence or "start_time" not in sequence or "interval" not in sequence:
                        log_event("Each sequence must have 'sequence', 'start_time' and 'interval' fields.", "ERROR")
                        return False
        return True
