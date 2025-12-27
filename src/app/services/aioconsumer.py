import asyncio
from confluent_kafka import Consumer, Message
from loguru import logger
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any, Optional
from functools import partial

class AIOConsumer:
    def __init__(self, consumer_configs, topics, max_workers=2, loop=None) -> None:
        self._loop = loop or asyncio.get_event_loop()
        self.topics = topics
        self._consumer = Consumer(consumer_configs)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def _call(self, blocking_task: Callable, *args: Any) -> Any:
        return await self._loop.run_in_executor(self.executor, blocking_task, *args)
    
    async def subscribe(self):
        await self._call(self._consumer.subscribe, self.topics)
        logger.info(f"subscribed to topics: {self.topics}")
    
    async def poll(self, timeout=1.0) -> Optional[Message]:
        return await self._call(self._consumer.poll, timeout)
    
    async def commit(self):
        task = partial(self._consumer.commit, asynchronous=True)
        await self._call(task)
    
    async def close(self):
        await self._call(self._consumer.close)
        self.executor.shutdown(wait=True)
        logger.info("kafka consumer is closed")