from src.modules import log_event

class Validator:

    @staticmethod
    def validate_email_format(email: str) -> bool:
        """Validate the format of an email address using a simple regex."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def check_placeholders_all_exist(placeholders: set, replacement: set) -> bool:
        """Check if all placeholders in a template exist in a dictionary."""
        missing_fields = placeholders - replacement
        if missing_fields:
            log_event(f"Missing fields: {missing_fields}", "ERROR")
            return False
        return True
