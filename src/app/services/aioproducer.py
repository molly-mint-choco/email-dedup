import asyncio
from threading import Thread
from confluent_kafka import Producer, KafkaException
from loguru import logger

class AIOProducer:
    def __init__(self, producer_configs, loop=None) -> None:
        self._loop = loop or asyncio.get_event_loop()
        self._producer = Producer(producer_configs)
        self._cancelled = False
        self._poll_thread = Thread(target=self._poll_loop)
        self._poll_thread.daemon = True
        self._poll_thread.start()

    def _poll_loop(self):
        logger.debug("background poll loop started.")
        while not self._cancelled:
            self._producer.poll(0.1)
        logger.debug("background poll loop stopped.")
    
    def close(self):
        self._cancelled = True
        self._poll_thread.join()
        self._producer.flush()
        logger.debug("kafka producer is closed, all messages are flushed to queue")
    
    async def produce_async(self, topic, key, value):
        result = self._loop.create_future()
        def delivery_callback(err, msg):
            if err:
                self._loop.call_soon_threadsafe(result.set_exception, KafkaException(err))
            else:
                self._loop.call_soon_threadsafe(result.set_result, msg)
        self._producer.produce(topic, key=key, value=value, on_delivery=delivery_callback)
        return await result
