import sys
import os

# Adds the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import asyncio
from loguru import logger
from app.services.subscribe_email_service import SubscribeEmailService

async def test_run_sub():
    service = SubscribeEmailService()
    logger.debug("Starting consumer test")
    try:
        await service.start_consumer_loop_async()
    except KeyboardInterrupt:
        logger.debug("Manually stopped consumer test")
    finally:
        await service.close_async()
        logger.debug("Consumer test execution finished.")

if __name__ == '__main__':
    asyncio.run(test_run_sub())