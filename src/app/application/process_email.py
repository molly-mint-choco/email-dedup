import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
from typing import List, Optional
import uuid
from simhash import Simhash
from src.config import config
from pathlib import Path
import re
from src.app.infrastructure.database import Database
from src.app.infrastructure.repo import EmailRepository
from src.app.domain.data_model import CanonicalThread, Document

class EmailHandler:
    def __init__(self) -> None:
        self.read_dir = config.data['email']['read_dir']
        self.bit_distance_threshold = config.data['email']['threshold']
        self.max_workers = config.data['email']['max_workers']
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.divider = "-----Original Message-----"
        self.db = Database()

    async def process_async(self, file_name):
        raw_content = await self.read_document_content_async(file_name)
        normalized_content = self.normalize(raw_content)
        email_parts = self.split_emails(normalized_content)
        thread_length = len(email_parts)
        self_hash = await self.generate_hash_async(normalized_content) # simhash of the whole content
        new_doc = Document(
            id = uuid.uuid4(),
            file_name = file_name,
            email_metadata = raw_content,
        )
        async for session in self.db.get_session_async():
            repo = EmailRepository(session)
            same_len_cano_threads = await repo.get_canonical_threads_by_length(thread_length)
            is_duplicate = False
            if same_len_cano_threads: # check if equal by simhash
                for cano_thread in same_len_cano_threads:
                    is_duplicate = await self.check_near_duplicate_async(self_hash, Simhash(value=cano_thread.hash))
                    if is_duplicate:
                        logger.info(f"Found duplicate canonical thread in db: {cano_thread.id}")
                        new_doc.cano_id = cano_thread.id
                        break
            if not same_len_cano_threads or not is_duplicate:
                new_cano = CanonicalThread(
                    id = uuid.uuid4(),
                    hash = self_hash.value,
                    thread_length = thread_length
                )
                new_doc.cano_id = new_cano.id
                if thread_length > 1: # for every new insertion, calculate the parent hash
                    parent_hash = await self.generate_hash_async(self.divider.join(email_parts[:-1])) # simhash of the parent content
                    new_cano.parent_hash = parent_hash.value

    def normalize(self, text: str) -> str:
        t = text.lower().strip()
        # standardize returns
        t = t.replace("\r\n", "\n").replace("\r", "\n")
        # remove html tags
        t = re.sub(r'<[^>]+>', '', t)
        # shrink extra whitespaces
        t = re.sub(r'\s+', ' ', t)
        return t

    def split_emails(self, text: str) -> List[str]:
        # assume that replies are splited by '-----Original Message-----'
        return text.split(self.divider)    

    async def read_document_content_async(self,file_name) -> str:
        file_path = Path(self.read_dir) / file_name
        try:
            async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                return await f.read()
        except FileNotFoundError:
            logger.error(f"File {file_name} not found at {file_path}")
            raise
    
    def _generate_hash(self, text: str) -> Simhash:
        return Simhash(text)

    async def generate_hash_async(self, text: str) -> Simhash:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._generate_hash, text)
    
    async def check_near_duplicate_async(self, hash1: Simhash, hash2: Simhash) -> bool:
        loop = asyncio.get_running_loop()
        distance = await loop.run_in_executor(self.executor, lambda: hash1.distance(hash2))
        return distance <= self.bit_distance_threshold
    
    def shutdown(self):
        self.executor.shutdown(wait=True)
