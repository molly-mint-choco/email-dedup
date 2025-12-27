from pathlib import Path
from src.config import config
from src.app.services.aioproducer import AIOProducer
from src.app.services.kafka_payload import KafkaPayload
from loguru import logger

class PublishEmailService:
    def __init__(self) -> None:
        self.read_dir = Path(config.data['email']['read_dir'])
        self.kafka_configs = {
            'bootstrap.servers': config.data['kafka']['bootstrap_servers'],
            'client.id': config.data['kafka']['producer']['client_id']
        }
        self.topic = config.data['kafka']['topic']
        self.producer = AIOProducer(kafka_configs=self.kafka_configs)
        logger.info("Service init: PublishEmailService")
    
    async def ingest_emails(self):
        logger.info(f"Starting ingestion from: {self.read_dir}")
        count = 0
        for file in self.read_dir.iterdir():
            if file.is_file():
                payload = KafkaPayload(file_name=file.name)
                logger.debug(f"Preparing to send: {payload.file_name} from source node {payload.source_node}")
                await self.producer.produce(
                    topic=self.topic,
                    key=None,
                    value=payload.to_json()
                )
                logger.success(f"Sent successfully: {payload.file_name} from source node {payload.source_node}")
                count += 1
        logger.info(f"Ingestion finished. Total files read and sent: {count}")
    
    async def close(self):
        self.producer.close()
        logger.info("Service shut down: PublishEmailService")
    