import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
from typing import List, Optional
import uuid
from simhash import Simhash
from config import config
from pathlib import Path
import re
from app.infrastructure.database import Database
from app.infrastructure.repo import EmailRepository
from app.domain.data_model import CanonicalThread, Document
import time


class EmailProcessor:
    def __init__(self) -> None:
        self.read_dir = config.data['email']['read_dir']
        self.bit_distance_threshold = config.data['email']['threshold']
        self.max_workers = config.data['email']['max_workers']
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.divider_re = r'(?=From: .+\nTo: .+\n(?:CC: .+\n)?Subject: )'
        self.db = Database()

    async def process_async(self, file_name: str):
        start_time = time.perf_counter()
        logger.info(f"Starting processing for file: {file_name}")

        try:
            # 1. Content Extraction & Whole Email Hashing
            raw_content = await self.read_document_content_async(file_name)
            email_parts = self.split_emails(raw_content)
            thread_length = len(email_parts)
            
            # Generate hash for the full content
            self_hash = await self.generate_hash_async(raw_content)
            logger.debug(f"File: {file_name} | Parts: {thread_length} | Hash: {str(self_hash.value)}")

            new_doc = Document(
                id=uuid.uuid4(),
                file_name=file_name,
                email_metadata=raw_content,
            )

            async for session in self.db.get_session_async():
                repo = EmailRepository(session)
                
                # 2. Deduplication Check
                # Filter by thread length to minimize distance calculations
                candidates = await repo.get_canonical_threads_by_length_async(thread_length)
                logger.debug(f"Length-match candidates found: {len(candidates)}")

                existing_cano_id = None
                for cano_thread in candidates:
                    if cano_thread.hash is not None:
                        is_duplicate = await self.check_near_duplicate_async(
                            self_hash, Simhash(int(cano_thread.hash)) # type: ignore
                        )
                        if is_duplicate:
                            logger.success(f"Duplicate detected. File {file_name} matches Canonical Thread {str(cano_thread.id)}")
                            existing_cano_id = cano_thread.id
                            break
                
                # 3. Canonical Thread Creation or Linking
                if existing_cano_id is not None:
                    new_doc.cano_id = existing_cano_id
                else:
                    logger.info("No duplicates found. Creating new Canonical Thread record.")
                    new_cano = CanonicalThread(
                        id=uuid.uuid4(),
                        hash=str(self_hash.value),
                        thread_length=thread_length
                    )
                    
                    # 4. Identify Its Parent Thread
                    if thread_length > 1:
                        # Reconstruct parent content by removing the most recent part
                        parent_content = "".join(email_parts[1:])
                        parent_hash = await self.generate_hash_async(parent_content)
                        new_cano.parent_hash = str(parent_hash.value) # type: ignore
                        
                        # Search for parent hash candidates by its thread length
                        parent_thread_candidates = await repo.get_canonical_threads_by_length_async(thread_length-1)
                        logger.info(f"Length-Match parent thread candidates found: {len(parent_thread_candidates)}")

                        for parent_thread_candidate in parent_thread_candidates:
                            if parent_thread_candidate.hash is not None:
                                is_duplicate = await self.check_near_duplicate_async(parent_hash, Simhash(int(parent_thread_candidate.hash))) # type: ignore
                                if is_duplicate:
                                    logger.success(f"Parent thread {str(parent_thread_candidate.id)} found for Canonical Thread {str(new_cano.id)}")
                                    new_cano.parent_id = parent_thread_candidate.id
                                    break
                        if new_cano.parent_id is None:
                            logger.info(f"Currently parent thread not found in DB for Canonical Thread {str(new_cano.id)}")

                    repo.insert_canonical_thread(new_cano)
                    new_doc.cano_id = new_cano.id

                    # 5. Check If Itself Is Parent Of Others
                    child_thread_candidates = await repo.get_orphan_child_threads_by_length_async(thread_length+1)
                    logger.info(f"Length-Match child thread candidates found: {len(child_thread_candidates)}")

                    for child_thread_candidate in child_thread_candidates:
                        is_duplicate = await self.check_near_duplicate_async(self_hash, Simhash(int(child_thread_candidate.parent_hash))) # type: ignore
                        if is_duplicate:
                                logger.success(f"Child thread {str(child_thread_candidate.id)} linked to current thread {str(new_cano.id)}")
                                child_thread_candidate.parent_id = new_cano.id

                # 6. Insert Document
                repo.insert_document(new_doc)
            
            duration = time.perf_counter() - start_time
            logger.success(f"Finished processing {file_name} in {duration:.3f}s")

        except Exception as e:
            logger.error(f"Failed to process file {file_name}: {str(e)}")
            # raise

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
        return [splitted for splitted in re.split(self.divider_re, text) if splitted.strip()] # remove empty parts

    async def read_document_content_async(self,file_name) -> str:
        file_path = Path(self.read_dir) / file_name
        try:
            async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                return await f.read()
        except FileNotFoundError:
            logger.error(f"File {file_name} not found at {file_path}")
            raise
    
    def _generate_hash(self, text: str) -> Simhash:
        text = self.normalize(text)
        return Simhash(text)

    async def generate_hash_async(self, text: str) -> Simhash:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._generate_hash, text)
    
    async def check_near_duplicate_async(self, hash1: Simhash, hash2: Simhash) -> bool:
        loop = asyncio.get_running_loop()
        distance = await loop.run_in_executor(self.executor, lambda: hash1.distance(hash2))
        return distance <= self.bit_distance_threshold
    
    def close(self):
        self.executor.shutdown(wait=True)
        logger.info("Email processor executor is shutdown.")
