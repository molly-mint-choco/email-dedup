import sys
import os

# Adds the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))


import asyncio
import uuid
from loguru import logger
from app.infrastructure.database import Database
from app.infrastructure.repo import EmailRepository
from app.domain.data_model import Document, CanonicalThread

async def test_repo():
    db = Database()
    test_file = "test_doc_001.txt"
    test_content = "This is a test email body."
    new_cano_thread = CanonicalThread(id=uuid.uuid4())
    new_doc = Document(
            id = uuid.uuid4(),
            file_name = test_file,
            cano_id = new_cano_thread.id,
            email_metadata = test_content,
            thread_length = 3,
            hash = '0-1-2',
            parent_hash = '0-1'
        )
    
    logger.debug("starting a new session from db")
    async for session in db.get_session_async():
        repo = EmailRepository(session)
        
        logger.debug(f"insert new canonical thread with id: {new_cano_thread.id}")
        await repo.insert_canonical_thread_async(new_cano_thread)
        logger.debug(f"successully inserted new canonical thread with id: {new_cano_thread.id}")
        
        logger.debug(f"insert new document with id: {new_doc.id}")
        await repo.insert_document_async(new_doc)
        logger.debug(f"successully inserted new document with id: {new_doc.id}")


    logger.debug("end session and commit changes")
    
    # start a new session because we need to commit the insertions first
    
    logger.debug("starting a new session from db")
    async for session in db.get_session_async():
        repo = EmailRepository(session)
        retrieved_cano_id = await repo.get_cano_id_by_filename_async(test_file)
        logger.debug(f"retrived canonical thread id: {retrieved_cano_id}")
        if retrieved_cano_id == new_cano_thread.id:
            logger.debug(f"retrieved correct canonical thread id: {new_cano_thread.id}")
        else:
            logger.error(f"expected {new_cano_thread.id}, got {retrieved_cano_id}")

    await db.engine.dispose() #
    logger.debug("Database engine disposed successfully.")
    
if __name__ == '__main__':
        asyncio.run(test_repo())
