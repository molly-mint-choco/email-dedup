import sys
import os

# Adds the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import asyncio
from loguru import logger
from src.app.services.publish_email_service import PublishEmailService

async def test_run_pub():
    service = PublishEmailService()
    logger.debug("Starting producer test")
    await service.ingest_emails()
    logger.debug("Producer test execution finished.")
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_run_pub())