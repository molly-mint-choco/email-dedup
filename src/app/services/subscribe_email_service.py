import asyncio
from src.config import config
from src.app.services.aioconsumer import AIOConsumer
from loguru import logger
from confluent_kafka import Message, KafkaError
import orjson
from src.app.services.kafka_payload import KafkaPayload

class SubscribeEmailService:
    def __init__(self) -> None:
        self.kafka_configs = {
            'bootstrap.servers': config.data['kafka']['bootstrap_servers'],
            'group.id': config.data['kafka']['consumer']['group_id'],
            'client.id': config.data['kafka']['consumer']['client_id'],
            'auto.offset.reset': 'earliest'
        }
        self.topics = [config.data['kafka']['topic']]
        self.max_workers = config.data['kafka']['consumer']['max_workers']
        self.poll_interval = config.data['kafka']['consumer']['poll_interval']
        self.min_commit_count = config.data['kafka']['consumer']['min_commit_count']
        self.consumer = AIOConsumer(consumer_configs=self.kafka_configs, topics=self.topics, max_workers=self.max_workers)
        self.is_running = False
        logger.info(f"Service init: {self.__class__.__name__}")
    
    async def start_consumer_loop_async(self):
        await self.consumer.subscribe_async()
        self.is_running = True
        logger.info(f"Starting listening to topic: {self.topics}")
        count = 0

        while self.is_running:
            msg = await self.consumer.poll_async(timeout=self.poll_interval)
            if not msg: # no emails in queue
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.info(f"topic {msg.topic()} reached end of partition {msg.partition()} at offset {msg.offset()}")
                    continue
                else:
                    logger.error(f"consumer error: {msg.error()}") # TODO: push failed messages to dead letter queue by calling producer
                    continue
            
            else:
                logger.debug(f"Received message from Kafka: {msg.value().decode('utf-8')}")
                payload = KafkaPayload.from_json(msg.value())
                count += 1
                if count % self.min_commit_count == 0:
                    await self.consumer.commit_async()
        
        # consumer.close

    async def close_async(self):
        self.is_running = False
        if self.consumer:
            await self.consumer.close_async()
        logger.info(f"Service shut down: {self.__class__.__name__}")


