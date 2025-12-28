import asyncio
import uuid
from typing import List, Dict, Any, Optional
from src.app.infrastructure.database import Database
from src.app.infrastructure.repo import EmailRepository

class EmailQueryHandler:
    def __init__(self):
        self.db = Database()

    async def get_canonical_id_by_document_async(self, file_name: str) -> Optional[uuid.UUID]:
        async for session in self.db.get_session_async():
            repo = EmailRepository(session)
            return await repo.get_cano_id_by_filename_async(file_name)

    async def get_documents_by_thread_async(self, cano_id: uuid.UUID) -> List[str]:
        documents = []

        async for session in self.db.get_session_async():
            repo = EmailRepository(session)
            results = await repo.get_filenames_by_cano_id(cano_id)

            if results:
                documents = results
                
        return documents

    async def get_child_threads_async(self, cano_id: uuid.UUID) -> List[uuid.UUID]:
        children = []
        async for session in self.db.get_session_async():
            repo = EmailRepository(session)
            results = await repo.get_cano_ids_by_parent_id_async(cano_id)

            if results:
                children = results
        
        return children


    async def get_parent_thread_async(self, cano_id: uuid.UUID) -> Optional[uuid.UUID]:
        async for session in self.db.get_session_async():
            repo = EmailRepository(session)
            return await repo.get_parent_cano_id_by_cano_id_async(cano_id)

    async def get_hierarchy_async(self, cano_id: uuid.UUID) -> str:
        hierarchy_chain = str(cano_id)
        async for session in self.db.get_session_async():
            repo = EmailRepository(session)
            parent_id = await repo.get_parent_cano_id_by_cano_id_async(cano_id)
            while parent_id is not None:
                hierarchy_chain = f"{parent_id} -> {hierarchy_chain}"
                parent_id = await repo.get_parent_cano_id_by_cano_id_async(parent_id)
        return hierarchy_chain
                
            
            
    async def shutdown(self):
        await self.db.dispose_async()