from src.modules.logger import Logger

# Initialize logger
logger = Logger()

from src.modules.input_parser import InputParser
from src.modules.campaign_manager import CampaignManager
from src.modules.scheduler import Scheduler
from src.modules.email_sender import EmailSender
from src.modules.folder_watchdog import DataFolderHandler

__all__ = [ logger, Logger, InputParser, CampaignManager, Scheduler, EmailSender, DataFolderHandler  ]