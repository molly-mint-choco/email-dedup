# src/main_api.py
import uvicorn
from fastapi import FastAPI
from app.api.routers.email_query_router import router as email_router
from app.infrastructure.database import Database
from loguru import logger
import asyncio
from app.services.publish_email_service import PublishEmailService
from app.services.subscribe_email_service import SubscribeEmailService

app = FastAPI(title="Email Deduplication API")

app.include_router(email_router)

@app.on_event("startup")
async def startup_event():
    logger.info("API Layer started and database verified.")

@app.on_event("shutdown")
def shutdown_event():
    # await db.dispose_async()
    logger.info("Application shutdown")


async def run_pub():
    service = PublishEmailService()
    logger.debug("Starting email ingesting")
    await service.ingest_emails_async()
    logger.debug("Email ingestion completed")
    await service.close_async()

async def run_sub():
    service = SubscribeEmailService()
    logger.debug("Starting email consumer")
    try:
        await service.start_consumer_loop_async()
    except KeyboardInterrupt:
        logger.debug("Manually stopped consumer")
    finally:
        await service.close_async()
        logger.debug("Consumer execution finished.")

def set_up_logger():
    logger.add(
    "logs/log_{time:YYYY-MM-DD_HH-mm-ss}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)


config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop="asyncio")
server = uvicorn.Server(config)

async def main():
    set_up_logger()

    # set up db first
    try:
        db = Database()
        db.setup_database() 
        logger.info("Database setup completed successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return
    
    # run producer, consumer and web app in parallel
    await asyncio.gather(
        server.serve(),
        run_pub(),
        run_sub()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application manually stopped.")


# http://127.0.0.1:8000/docs