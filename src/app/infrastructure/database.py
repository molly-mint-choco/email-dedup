from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy_utils import create_database, database_exists
from sqlalchemy import create_engine
from src.config import config
from loguru import logger
from src.app.domain.data_model import Base


class Database:
    def __init__(self) -> None:
        # DB set up
        self.sync_database_url = f"mysql+pymysql://{config.data['database']['username']}:{config.data['database']['password']}@{config.data['database']['host']}:{config.data['database']['port']}/{config.data['database']['database_name']}"
        self.async_database_url = f"mysql+aiomysql://{config.data['database']['username']}:{config.data['database']['password']}@{config.data['database']['host']}:{config.data['database']['port']}/{config.data['database']['database_name']}"
        self.engine = create_async_engine(self.async_database_url)
        self.session_maker = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

    def setup_database(self):
        if not database_exists(self.sync_database_url):
            create_database(self.sync_database_url)
            logger.info(f"Database {config.data['database']['database_name']} created.")
        else:
            logger.info(f"Database {config.data['database']['database_name']} exists.")

        sync_engine = create_engine(self.sync_database_url)
        Base.metadata.create_all(sync_engine)
        logger.info("Database {config.data['database']['database_name']} tables creation or verification completed.")
        sync_engine.dispose()


    async def get_session_async(self):
        async with self.session_maker() as session:
            try:
                yield session
                await session.commit() # commit changes for the last database operations
            except Exception as e:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def dispose_async(self):
        await self.engine.dispose()
        logger.info("Database engine disposed successfully.")




