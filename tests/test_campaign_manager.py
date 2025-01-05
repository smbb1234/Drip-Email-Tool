import unittest
import os
from src.modules import CampaignManager

class TestCampaignManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.contacts = [
            {"name": "John Doe", "email": "john.doe@example.com", "company": "Example Corp"},
            {"name": "Jane Smith", "email": "jane.smith@example.com", "company": "Tech Innovators"}
        ]

        cls.templates = [
            {"sequence": 1, "subject": "Hello {name}", "content": "Hi {name}, let's connect!"},
            {"sequence": 2, "subject": "Follow-up", "content": "Hi {name}, just checking in!"}
        ]

        cls.schedule = [
            {
                "campaign_id": "campaign_1",
                "sequences": [
                    {"sequence": 1, "start_time": "2025-01-01T10:00:00", "interval": 1},
                    {"sequence": 2, "start_time": "2025-01-02T10:00:00", "interval": 2}
                ]
            }
        ]

        cls.store_file = "test_campaigns.json"

    def setUp(self):
        if os.path.exists(self.store_file):
            os.remove(self.store_file)

        self.manager = CampaignManager(
            contacts=self.contacts,
            templates=self.templates,
            schedule=self.schedule,
            store_file=self.store_file
        )

    def tearDown(self):
        if os.path.exists(self.store_file):
            os.remove(self.store_file)

    def test_initialize_campaign(self):
        """Test initializing a campaign with valid data."""
        self.assertIn("campaign_1", self.manager.campaigns)
        campaign = self.manager.campaigns["campaign_1"]
        self.assertEqual(campaign["status"], "Not Started")
        self.assertEqual(len(campaign["contacts"]), 2)

    def test_start_campaign(self):
        """Test starting a campaign."""
        result = self.manager.start_campaign("campaign_1")
        self.assertTrue(result)
        self.assertEqual(self.manager.campaigns["campaign_1"]["status"], "In Progress")

    def test_start_nonexistent_campaign(self):
        """Test starting a nonexistent campaign."""
        result = self.manager.start_campaign("nonexistent")
        self.assertFalse(result)

    def test_update_campaign_status(self):
        """Test updating the status of a contact in a campaign."""
        self.manager.start_campaign("campaign_1")
        result = self.manager.update_campaign_status(
            "campaign_1", "john.doe@example.com", "Email Sent"
        )
        self.assertTrue(result)
        self.assertEqual(
            self.manager.campaigns["campaign_1"]["contacts"]["john.doe@example.com"]["progress"],
            "Email Sent"
        )

    def test_update_invalid_status(self):
        """Test updating a contact's status to an invalid value."""
        result = self.manager.update_campaign_status(
            "campaign_1", "john.doe@example.com", "Invalid Status"
        )
        self.assertFalse(result)

    def test_update_campaign_status_nonexistent_contact(self):
        """Test updating a status for a contact that doesn't exist."""
        result = self.manager.update_campaign_status("campaign_1", "nonexistent@example.com", "Completed")
        self.assertFalse(result)

    def test_get_campaign(self):
        """Test retrieving the status of a campaign."""
        status = self.manager.get_campaign_status("campaign_1")
        self.assertIn("contacts", status)
        self.assertIn("templates", status)
        self.assertEqual(status["status"], "Not Started")

    def test_get_nonexistent_campaign(self):
        """Test retrieving the status of a nonexistent campaign."""
        status = self.manager.get_campaign_status("nonexistent_campaign")
        self.assertEqual(status, {})

    def test_save_and_load_state(self):
        """Test saving and loading campaign state from file."""
        self.manager.start_campaign("campaign_1")
        self.manager.save_state()

        new_manager = CampaignManager(store_file=self.store_file)
        self.assertIn("campaign_1", new_manager.campaigns)
        self.assertEqual(new_manager.campaigns["campaign_1"]["status"], "In Progress")

    def test_delete_state(self):
        """Test deleting the state file."""
        self.manager.save_state()
        CampaignManager.delete_state(self.store_file)
        self.assertFalse(os.path.exists(self.store_file))

if __name__ == "__main__":
    unittest.main()
