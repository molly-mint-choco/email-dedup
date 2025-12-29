from pathlib import Path
from src.config import config
from src.app.services.aioproducer import AIOProducer
from src.app.services.kafka_payload import KafkaPayload
from loguru import logger
import os

class PublishEmailService:
    def __init__(self) -> None:
        self.ENV = os.getenv("APP_ENV", "development")
        
        self.read_dir = Path(config.data['email']['read_dir'])
        self.kafka_configs = {
            'bootstrap.servers': config.data['kafka']['bootstrap_servers'],
            'client.id': config.data['kafka']['producer']['client_id']
        }

        if self.ENV == "production":
            self.kafka_configs["bootstrap.servers"] = os.getenv("KAFKA_SERVERS")
            self.kafka_configs["security.protocol"] = os.getenv("KAFKA_SECURITY_PROTOCOL")
            self.kafka_configs["sasl.mechanism"] = os.getenv("KAFKA_SASL_MECHANISM")
            self.kafka_configs["sasl.username"] = os.getenv("KAFKA_SASL_USERNAME")
            self.kafka_configs["sasl.password"] = os.getenv("KAFKA_SASL_PASSWORD")

        logger.info(f'publish kafka configs: {self.kafka_configs}')

        self.topic = config.data['kafka']['topic']
        self.producer = AIOProducer(producer_configs=self.kafka_configs)
        logger.info(f"Service init: {self.__class__.__name__}")
    
    async def ingest_emails_async(self):
        logger.info(f"Starting ingestion from: {self.read_dir}")
        count = 0
        files = [entry for entry in self.read_dir.iterdir() if entry.is_file()] # TODO: replace with async lib: anyio
        files.sort(key=lambda file: file.stat().st_ctime, reverse=False)
        for file in files:
            payload = KafkaPayload(file_name=file.name)
            logger.debug(f"Preparing to send: {payload.file_name} from source node {payload.source_node}")
            await self.producer.produce_async(
                topic=self.topic,
                key=None,
                value=payload.to_json()
            )
            logger.success(f"Sent successfully: {payload.file_name} from source node {payload.source_node}")
            count += 1
        logger.info(f"Ingestion finished. Total files read and sent: {count}")
    
    async def close_async(self):
        self.producer.close()
        logger.info(f"Service shut down: {self.__class__.__name__}")
    