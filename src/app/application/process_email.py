import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
from typing import List, Optional
import uuid
from simhash import Simhash
from src.config import config
from pathlib import Path

class EmailHandler:
    def __init__(self) -> None:
        self.read_dir = config.data['email']['read_dir']
        self.bit_distance_threshold = config.data['email']['threshold']
        self.max_workers = config.data['email']['max_workers']
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

    async def process_async(self, file_name):
        raw_content = await self.read_document_content_async(file_name)
        email_parts = self.split_emails(raw_content)
        hash_chain = await self.generate_hash_chain_async(email_parts)

        # check if hash_chain exist in canonical thread table
        

    def split_emails(self, raw_content: str) -> List[str]:
        return []        

    async def read_document_content_async(self,file_name) -> str:
        file_path = Path(self.read_dir) / file_name
        try:
            async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                return await f.read()
        except FileNotFoundError:
            logger.error(f"File {file_name} not found at {file_path}")
            raise
    
    def _generate_hash_chain(self, email_parts: List[str]) -> List[Simhash]:
        return [Simhash(part) for part in email_parts]

    async def generate_hash_chain_async(self, email_parts: List[str]) -> List[Simhash]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._generate_hash_chain, email_parts)
    
    async def check_near_duplicate_async(self, hash1: Simhash, hash2: Simhash) -> bool:
        loop = asyncio.get_running_loop()
        distance = await loop.run_in_executor(self.executor, lambda: hash1.distance(hash2))
        return distance <= self.bit_distance_threshold
    
    def shutdown(self):
        self.executor.shutdown(wait=True)
