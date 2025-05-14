"""
MongoDB client functionality for PyMondantic.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar
from pymongo import MongoClient as PyMongoClient
from pymongo.database import Database
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from .models import MongoModel

T = TypeVar("T", bound=MongoModel)

class MongoClient:
    """
    Client class for managing MongoDB connections and operations.
    """
    
    def __init__(
        self,
        uri: str,
        database: str,
        **kwargs: Any
    ) -> None:
        """
        Initialize the MongoDB client.
        
        Args:
            uri: MongoDB connection URI
            database: Database name
            **kwargs: Additional arguments passed to PyMongo client
        """
        self._sync_client = PyMongoClient(uri, **kwargs)
        self._async_client = AsyncIOMotorClient(uri, **kwargs)
        self._database = database
    
    def get_database(self) -> Database:
        """Get the synchronous database instance."""
        return self._sync_client[self._database]
    
    def get_async_database(self) -> AsyncIOMotorDatabase:
        """Get the asynchronous database instance."""
        return self._async_client[self._database]
    
    def ensure_indexes(self, models: List[Type[MongoModel]]) -> None:
        """
        Create indexes for all specified models.
        
        Args:
            models: List of model classes to create indexes for
        """
        db = self.get_database()
        for model in models:
            model.ensure_indexes(db)
    
    def close(self) -> None:
        """Close all client connections."""
        self._sync_client.close()
        self._async_client.close()
    
    async def close_async(self) -> None:
        """Close async client connection."""
        self._async_client.close() 