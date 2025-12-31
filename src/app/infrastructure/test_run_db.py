import sys
import os

# Adds the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import asyncio
from app.infrastructure.database import Database
from sqlalchemy import text
from loguru import logger


async def test_run_db():
    db = Database()
    logger.debug("start databse set up")
    db.setup_database()
    logger.debug("db set up completed")

    logger.debug("test async connection")
    async for session in db.get_session_async():
        result = await session.execute(text("SELECT 1"))
        if result.scalar() == 1:
            logger.debug("test async connection completed")
        
        result = await session.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]
        logger.debug(f"tables: {tables}")
    await db.engine.dispose()

if __name__ == '__main__':
    asyncio.run(test_run_db())