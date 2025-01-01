import unittest
import os
import json
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
from src.modules.input_parser import load_contacts, load_templates, load_schedule

class TestInputParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up temporary test files."""
        cls.sample_contacts_path = "test_contacts.csv"
        cls.sample_templates_path = "test_templates.yaml"
        cls.sample_schedule_path = "test_schedule.json"

        # Sample contacts CSV
        if not os.path.exists(cls.sample_contacts_path) or os.path.getsize(cls.sample_contacts_path) == 0:
            with open(cls.sample_contacts_path, "w") as f:
                sample_contacts = """name,email,company,role
                John Doe,john.doe@example.com,Example Corp,Manager
                Invalid User,invalid-email,Example Corp,Staff
                Jane Smith,jane.smith@example.com,Tech Innovators,Engineer"""
                f.write(sample_contacts.replace('  ', ''))

        # Sample templates YAML
        if not os.path.exists(cls.sample_templates_path) or os.path.getsize(cls.sample_templates_path) == 0:
            yaml = YAML()
            yaml.width = 240
            sample_templates = [
                {
                    "sequence": 1,
                    "subject": DoubleQuotedScalarString("Hello {name}, let's connect!"),
                    "content": DoubleQuotedScalarString("Hi {name},\n\nWe noticed you're interested in {topic}. Let us know how we can help!\n\nBest,\nThe Team")
                },
                {
                    "sequence": 2,
                    "subject": DoubleQuotedScalarString("Following up, {name}"),
                    "content": DoubleQuotedScalarString("Hi {name},\n\nJust wanted to follow up on my previous email. Let me know if you're available to chat.\n\nThanks,\nThe Team")
                }
            ]
            with open(cls.sample_templates_path, "w") as f:
                yaml.dump(sample_templates, f)

        # Sample schedule JSON
        if not os.path.exists(cls.sample_schedule_path) or os.path.getsize(cls.sample_schedule_path) == 0:
            sample_schedule = [
                {
                    "campaign_id": "campaign_1",
                    "start_time": "2025-01-02T09:00:00",
                    "interval": 2
                },
                {
                    "campaign_id": "campaign_2",
                    "start_time": "2025-01-03T10:00:00",
                    "interval": 3
                }
            ]
            # noinspection PyTypeChecker
            with open(cls.sample_schedule_path, "w") as f:
                json.dump(sample_schedule, f, indent=2)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary test files."""
        os.remove(cls.sample_contacts_path)
        os.remove(cls.sample_templates_path)
        os.remove(cls.sample_schedule_path)

    def test_load_contacts(self):
        """Test loading and validation of contacts."""
        contacts = load_contacts(self.sample_contacts_path)
        self.assertEqual(len(contacts), 2)  # Invalid email should be skipped
        self.assertEqual(contacts[0]["name"], "John Doe")
        self.assertEqual(contacts[0]["email"], "john.doe@example.com")
        self.assertEqual(contacts[1]["email"], "jane.smith@example.com")

    def test_load_templates(self):
        """Test loading and validation of templates."""
        templates = load_templates(self.sample_templates_path)
        self.assertEqual(len(templates), 2)
        self.assertEqual(templates[0]["sequence"], 1)
        self.assertIn("{name}", templates[0]["subject"])
        self.assertIn("{topic}", templates[0]["content"])

    def test_load_schedule(self):
        """Test loading and validation of schedule."""
        schedule = load_schedule(self.sample_schedule_path)
        self.assertEqual(len(schedule), 2)
        self.assertEqual(schedule[0]["campaign_id"], "campaign_1")
        self.assertEqual(schedule[0]["start_time"], "2025-01-02T09:00:00")
        self.assertEqual(schedule[0]["interval"], 2)

    def test_invalid_file_paths(self):
        """Test handling of non-existent files."""
        with self.assertRaises(FileNotFoundError):
            load_contacts("nonexistent.csv")
        with self.assertRaises(FileNotFoundError):
            load_templates("nonexistent.yaml")
        with self.assertRaises(FileNotFoundError):
            load_schedule("nonexistent.json")

    def test_invalid_file_content(self):
        """Test handling of invalid file content."""
        invalid_file_path = "invalid.json"
        with open(invalid_file_path, "w") as f:
            f.write("Not a valid JSON")

        with self.assertRaises(ValueError):
            load_schedule(invalid_file_path)

        os.remove(invalid_file_path)

if __name__ == "__main__":
    unittest.main()
