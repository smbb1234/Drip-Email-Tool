import unittest
from unittest.mock import patch, MagicMock
from src.modules import EmailSender

class TestEmailSender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.email_sender = EmailSender("sender@example.com")

    @patch("sendgrid.SendGridAPIClient.send")
    def test_send_email_success(self, mock_send):
        """Test sending an email successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_send.return_value = mock_response

        result = self.email_sender.send_email(
            recipient="test@example.com",
            subject="Test Subject",
            content="<p>This is a test email.</p>"
        )

        self.assertTrue(result)

    @patch("sendgrid.SendGridAPIClient.send")
    def test_send_email_failure(self, mock_send):
        """Test failing to send an email."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_send.return_value = mock_response

        result = self.email_sender.send_email(
            recipient="test@example.com",
            subject="Test Subject",
            content="<p>This is a test email.</p>"
        )

        self.assertFalse(result)

    def test_build_email_content_success(self):
        """Test building email content with successful placeholder replacement."""
        template = {
            "sequence": 1,
            "subject": "Hello {name}, let's connect!",
            "content": "<h1>Hello {name}!</h1><p>Welcome to {company} in {year}.</p>"
        }
        contact = {
            "info": {
                "name": "John Doe",
                "company": "Example Corp"
            }
        }
        custom_vars = {"year": "2025"}

        subject, content = self.email_sender.build_email_content(template, contact, custom_vars)

        self.assertNotIn("{", content)
        self.assertIn("John Doe", content)
        self.assertIn("Example Corp", content)
        self.assertIn("2025", content)

    def test_send_email_without_sender(self):
        """Test sending an email without a sender specified."""
        with patch("sendgrid.SendGridAPIClient.send") as mock_send:
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_send.return_value = mock_response

            result = self.email_sender.send_email(
                recipient="test@example.com",
                subject="Test Subject",
                content="<p>This is a test email.</p>"
            )

            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
