"""Database connection management with a real MongoDB-first approach and a safe local fallback."""

import logging
from typing import Any

from mongomock_motor import AsyncMongoMockClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseClient:
    """A wrapper class to hold the database client instance."""

    client: Any = None


db_client = DatabaseClient()


async def connect_to_mongo():
    """Establish a connection to MongoDB when available, otherwise fall back to a mock database."""
    try:
        if settings.mongodb_url and settings.mongodb_url != "mongodb://localhost:27017":
            db_client.client = AsyncIOMotorClient(settings.mongodb_url)
            await db_client.client.admin.command("ping")
            logger.info("Successfully connected to MongoDB at %s", settings.mongodb_url)
        else:
            db_client.client = AsyncMongoMockClient()
            logger.info("Using an embedded mock MongoDB instance for local development.")
    except Exception as exc:
        logger.warning("MongoDB connection unavailable: %s. Falling back to mock database.", exc)
        db_client.client = AsyncMongoMockClient()


async def close_mongo_connection():
    """Close the MongoDB connection if it exists."""
    if db_client.client:
        if hasattr(db_client.client, "close"):
            db_client.client.close()
        db_client.client = None
        logger.info("Database connection closed.")


async def get_database():
    """Dependency function to get the database instance, initializing it lazily if needed."""
    if db_client.client is None:
        await connect_to_mongo()
    return db_client.client[settings.database_name]
