# Data settings
DATA_DIR = "data"
SCHEDULE_FILE_NAME = "schedule.json"
TEMPLATES_FILE_NAME = "templates.yaml"
CONTACTS_FILE_NAME = "contacts.csv"

# Log settings
LOG_DIR = "logs"
LOG_FILE_NAME = "app.log"
LOG_LEVEL = "DEBUG"

# Campaign settings
FILE_PERSISTENCE = False
CAMPAIGN_PATH = "src/campaigns.json"

# Schedule settings
RETRY_INTERVAL = 5

# Email settings
AWS_REGION = "eu-west-2"
CHARSET = "UTF-8"
SENDER_EMAIL = "ramya@DiagonalMatrix.com"
CUSTOM_VAR = {
    "topic": "Future"
}