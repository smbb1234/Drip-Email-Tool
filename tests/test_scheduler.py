import unittest, mock
from datetime import datetime, timedelta
from src.modules import CampaignManager, log_event
from src.modules import Scheduler

class TestScheduler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        contacts = [
            {"name": "John Doe", "email": "john.doe@example.com", "company": "Example Corp"},
            {"name": "Jane Smith", "email": "jane.smith@example.com", "company": "Tech Innovators"}
        ]
        templates = [
            {"sequence": 1, "subject": "Hello {name}", "content": "Hi {name}, let's connect!"},
            {"sequence": 2, "subject": "Follow-up", "content": "Hi {name}, just checking in!"},
            {"sequence": 3, "subject": "Final follow-up", "content": "Hi {name}, last chance to connect!"}
        ]
        schedule = [
            {
                "campaign_id": "campaign_1",
                "sequences": [
                    {"sequence": 1, "start_time": (datetime.now() + timedelta(seconds=5)).isoformat(), "interval": 2},
                    {"sequence": 2, "start_time": (datetime.now() + timedelta(seconds=10)).isoformat(), "interval": 3},
                    {"sequence": 3, "start_time": (datetime.now() + timedelta(seconds=15)).isoformat(), "interval": 5}
                ]
            }
        ]
        campaign_data = CampaignManager.build_campaign_data(contacts, templates, schedule)
        cls.campaign_manager = CampaignManager(campaign_data)
        cls.scheduler = Scheduler(cls.campaign_manager)

    def test_schedule_campaign(self):
        """Test scheduling a campaign."""
        result = self.scheduler.schedule_campaign(
            campaign_id="campaign_1",
            campaign_start_time=(datetime.now() + timedelta(seconds=5)).isoformat(),
            action=lambda campaign_id, email, status: log_event(f"Action executed for {campaign_id}, {email}.", "INFO")
        )
        self.assertTrue(result)

    def test_schedule_next_email(self):
        """Test scheduling the next email for a contact."""
        result = self.scheduler.schedule_next_email(
            campaign_id="campaign_1",
            contact_email="john.doe@example.com",
            action=lambda campaign_id, email, status: log_event(f"Next email sent for {campaign_id}, {email}.", "INFO"),
            delay=1
        )
        self.assertTrue(result)

    def test_remove_nonexistent_job(self):
        """Test attempting to remove a nonexistent job."""
        log_event_mock = mock.Mock()
        log_event_mock.side_effect = log_event
        with mock.patch('src.modules', log_event_mock):
            result = self.scheduler.schedule_next_email(
                campaign_id="campaign_1",
                contact_email="nonexistent@example.com",
                action=lambda campaign_id, email, status: log_event(f"Next email sent for {campaign_id}, {email}.", "INFO"),
                delay=1
            )
            self.assertFalse(result)
            log_event_mock.assert_called_with(
                mock.ANY, "WARNING"
            )

    def test_scheduler_shutdown(self):
        """Test shutting down the scheduler."""
        self.scheduler.run_scheduler()
        self.scheduler.shutdown_scheduler()
        self.assertFalse(self.scheduler.scheduler.running)

if __name__ == "__main__":
    unittest.main()
