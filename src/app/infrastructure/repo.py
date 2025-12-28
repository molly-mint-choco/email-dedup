from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.domain.data_model import CanonicalThread, Document, AuditLog
from loguru import logger
from typing import List, Optional
import uuid

class EmailRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_document_by_filename_async(self, file_name) -> Optional[Document]:
        result = await self.session.execute(
            select(Document).where(Document.file_name == file_name)
        )
        return result.scalars().first()
    
    async def insert_document_async(self, new_doc) -> Document:
        self.session.add(new_doc)
        # await self.session.flush()
        # await self.session.refresh()
        return new_doc
    
    async def get_canonical_thread_by_id_async(self, cano_id: uuid.UUID) -> Optional[CanonicalThread]:
        result = await self.session.execute(
            select(CanonicalThread).where(CanonicalThread.id == cano_id)
        )
        return result.scalars().first()

    async def get_cano_id_by_filename_async(self, file_name) -> Optional[uuid.UUID]:
        result = await self.session.execute(
            select(Document.cano_id).where(Document.file_name == file_name)
        )
        return result.scalars().first()
    
    async def get_filenames_by_cano_id(self, cano_id: uuid.UUID) -> List[str]:
        result = await self.session.execute(
            select(Document.file_name).where(Document.cano_id == cano_id)
        )
        return list(result.scalars().all())
    
    async def get_parent_cano_id_by_cano_id_async(self, cano_id: uuid.UUID) -> Optional[uuid.UUID]:
        # a child only has one parent
        result = await self.session.execute(
            select(CanonicalThread.parent_id).where(CanonicalThread.id == cano_id)
        )
        return result.scalars().first()
    
    async def get_cano_ids_by_parent_id_async(self, parent_cano_id: uuid.UUID) -> List[uuid.UUID]:
        # a parent can have multiple children, e,g, 0-1(P), 0-1-2(C1), 0-1-3(C2)
        result = await self.session.execute(
            select(CanonicalThread.id).where(CanonicalThread.parent_id == parent_cano_id)
        )
        return list(result.scalars().all())

    async def insert_canonical_thread_async(self, new_cano_thread) -> CanonicalThread:
        self.session.add(new_cano_thread)
        return new_cano_thread
    
    async def get_canonical_thread_by_hash_chain_async(self, hash_chain: List[int]) -> Optional[CanonicalThread]
        result = await self.session.execute(
            select(CanonicalThread).where(CanonicalThread.hash_chain == hash_chain)
        )
        return result.scalars().first()
    # TODO: audit log