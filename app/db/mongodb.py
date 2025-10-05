from __future__ import annotations

from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket

from app.core.config import get_settings

settings = get_settings()


class MongoDB:
    """Container for MongoDB connections."""

    client: Optional[AsyncIOMotorClient] = None
    database: Optional[Any] = None
    grid_fs: Optional[AsyncIOMotorGridFSBucket] = None


def get_database() -> Any:
    if MongoDB.database is None:
        raise RuntimeError("MongoDB connection has not been initialised")
    return MongoDB.database


def get_grid_fs() -> AsyncIOMotorGridFSBucket:
    if MongoDB.grid_fs is None:
        raise RuntimeError("MongoDB GridFS bucket not initialised")
    return MongoDB.grid_fs


async def connect_to_mongo() -> None:
    """Initialise a MongoDB connection pool."""

    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_url)
    MongoDB.client = client
    MongoDB.database = client[settings.mongodb_db_name]
    if MongoDB.database is None:  # pragma: no cover - safety guard for type checkers
        raise RuntimeError("MongoDB database initialisation failed")
    MongoDB.grid_fs = AsyncIOMotorGridFSBucket(MongoDB.database)


async def close_mongo_connection() -> None:
    """Gracefully close MongoDB connection."""

    if MongoDB.client is not None:
        MongoDB.client.close()
        MongoDB.client = None
        MongoDB.database = None
        MongoDB.grid_fs = None
