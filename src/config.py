import logging
import os

from dotenv import load_dotenv


class _Config:
    ALEPH_AGENTS_OWNER: str
    ALEPH_AGENT_CHANNEL: str
    LIBERTAI_INSTANCES_ADDRESS: str
    LIBERTAI_X402_ADDRESS: str
    LIBERCLAW_INSTANCES_ADDRESS: str

    LOG_LEVEL: int
    LOG_FILE: str | None

    def __init__(self):
        load_dotenv()

        self.ALEPH_AGENTS_OWNER = os.getenv("ALEPH_AGENTS_OWNER")
        self.ALEPH_AGENT_CHANNEL = os.getenv("ALEPH_AGENT_CHANNEL")
        self.LIBERTAI_INSTANCES_ADDRESS = os.getenv("LIBERTAI_INSTANCES_ADDRESS")
        self.LIBERTAI_X402_ADDRESS = os.getenv("LIBERTAI_X402_ADDRESS")
        self.LIBERCLAW_INSTANCES_ADDRESS = os.getenv("LIBERCLAW_INSTANCES_ADDRESS")

        # Configure logging
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        self.LOG_LEVEL = getattr(logging, log_level_str, logging.INFO)
        self.LOG_FILE = os.getenv("LOG_FILE", None)


config = _Config()
