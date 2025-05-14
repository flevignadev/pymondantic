"""
Core model functionality for PyMondantic.
"""

from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar, Union, Callable
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field
from pymongo import MongoClient as PyMongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

T = TypeVar("T", bound="MongoModel")

class MongoModel(BaseModel):
    """
    Base model class that combines Pydantic validation with MongoDB operations.
    """
    
    # MongoDB specific configuration
    collection_name: ClassVar[str]
    indexes: ClassVar[List[Dict[str, Any]]] = []
    soft_delete: ClassVar[bool] = False
    versioning: ClassVar[bool] = False
    
    # Common fields
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_deleted: bool = Field(default=False)
    _v: Optional[int] = Field(default=1, alias="__v")
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_encoders={ObjectId: str}
    )
    
    # Lifecycle hooks
    _before_save: ClassVar[List[Callable[["MongoModel"], None]]] = []
    _after_save: ClassVar[List[Callable[["MongoModel"], None]]] = []
    _before_delete: ClassVar[List[Callable[["MongoModel"], None]]] = []
    _after_delete: ClassVar[List[Callable[["MongoModel"], None]]] = []
    
    @classmethod
    def get_collection(cls, db: Union[Database, AsyncIOMotorDatabase]) -> Union[Collection, Any]:
        """Get the MongoDB collection for this model."""
        return db[cls.collection_name]
    
    @classmethod
    def ensure_indexes(cls, db: Database) -> None:
        """Create indexes defined in the model."""
        collection = cls.get_collection(db)
        for index in cls.indexes:
            collection.create_index(**index)
    
    def _prepare_save(self) -> Dict[str, Any]:
        """Prepare document for saving."""
        self.updated_at = datetime.utcnow()
        if self.versioning:
            self._v = (self._v or 0) + 1
        return self.model_dump(by_alias=True, exclude_none=True)
    
    def _run_hooks(self, hooks: List[Callable[["MongoModel"], None]]) -> None:
        """Run lifecycle hooks."""
        for hook in hooks:
            hook(self)
    
    def save(self, db: Database) -> None:
        """Save the model to MongoDB synchronously."""
        self._run_hooks(self._before_save)
        
        collection = self.get_collection(db)
        data = self._prepare_save()
        
        if self.id is None:
            result = collection.insert_one(data)
            self.id = result.inserted_id
        else:
            collection.update_one(
                {"_id": self.id},
                {"$set": data}
            )
        
        self._run_hooks(self._after_save)
    
    async def save_async(self, db: AsyncIOMotorDatabase) -> None:
        """Save the model to MongoDB asynchronously."""
        self._run_hooks(self._before_save)
        
        collection = self.get_collection(db)
        data = self._prepare_save()
        
        if self.id is None:
            result = await collection.insert_one(data)
            self.id = result.inserted_id
        else:
            await collection.update_one(
                {"_id": self.id},
                {"$set": data}
            )
        
        self._run_hooks(self._after_save)
    
    def _prepare_query(self, filter_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare query with soft delete filter if enabled."""
        if self.soft_delete:
            return {"$and": [filter_dict, {"is_deleted": False}]}
        return filter_dict
    
    @classmethod
    def find(
        cls: Type[T],
        db: Database,
        filter_dict: Dict[str, Any],
        skip: int = 0,
        limit: int = 0,
        sort: Optional[List[tuple]] = None,
        **kwargs: Any
    ) -> List[T]:
        """Find documents synchronously with pagination."""
        collection = cls.get_collection(db)
        query = cls._prepare_query(filter_dict)
        
        cursor = collection.find(query, **kwargs)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
            
        return [cls.model_validate(doc) for doc in cursor]
    
    @classmethod
    async def find_async(
        cls: Type[T],
        db: AsyncIOMotorDatabase,
        filter_dict: Dict[str, Any],
        skip: int = 0,
        limit: int = 0,
        sort: Optional[List[tuple]] = None,
        **kwargs: Any
    ) -> List[T]:
        """Find documents asynchronously with pagination."""
        collection = cls.get_collection(db)
        query = cls._prepare_query(filter_dict)
        
        cursor = collection.find(query, **kwargs)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
            
        return [cls.model_validate(doc) async for doc in cursor]
    
    @classmethod
    def find_one(
        cls: Type[T],
        db: Database,
        filter_dict: Dict[str, Any],
        **kwargs: Any
    ) -> Optional[T]:
        """Find one document synchronously."""
        collection = cls.get_collection(db)
        query = cls._prepare_query(filter_dict)
        doc = collection.find_one(query, **kwargs)
        return cls.model_validate(doc) if doc else None
    
    @classmethod
    async def find_one_async(
        cls: Type[T],
        db: AsyncIOMotorDatabase,
        filter_dict: Dict[str, Any],
        **kwargs: Any
    ) -> Optional[T]:
        """Find one document asynchronously."""
        collection = cls.get_collection(db)
        query = cls._prepare_query(filter_dict)
        doc = await collection.find_one(query, **kwargs)
        return cls.model_validate(doc) if doc else None
    
    def delete(self, db: Database, hard: bool = False) -> None:
        """Delete the document synchronously."""
        if self.id is not None:
            self._run_hooks(self._before_delete)
            collection = self.get_collection(db)
            
            if self.soft_delete and not hard:
                collection.update_one(
                    {"_id": self.id},
                    {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
                )
            else:
                collection.delete_one({"_id": self.id})
            
            self._run_hooks(self._after_delete)
    
    async def delete_async(self, db: AsyncIOMotorDatabase, hard: bool = False) -> None:
        """Delete the document asynchronously."""
        if self.id is not None:
            self._run_hooks(self._before_delete)
            collection = self.get_collection(db)
            
            if self.soft_delete and not hard:
                await collection.update_one(
                    {"_id": self.id},
                    {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
                )
            else:
                await collection.delete_one({"_id": self.id})
            
            self._run_hooks(self._after_delete)
    
    @classmethod
    def watch(
        cls,
        db: Database,
        pipeline: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any
    ) -> Any:
        """Watch for changes in the collection synchronously."""
        collection = cls.get_collection(db)
        return collection.watch(pipeline, **kwargs)
    
    @classmethod
    async def watch_async(
        cls,
        db: AsyncIOMotorDatabase,
        pipeline: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any
    ) -> Any:
        """Watch for changes in the collection asynchronously."""
        collection = cls.get_collection(db)
        return collection.watch(pipeline, **kwargs)
    
    @classmethod
    def register_hook(
        cls,
        hook_type: str,
        hook_func: Callable[["MongoModel"], None]
    ) -> None:
        """Register a lifecycle hook."""
        hook_map = {
            "before_save": cls._before_save,
            "after_save": cls._after_save,
            "before_delete": cls._before_delete,
            "after_delete": cls._after_delete
        }
        if hook_type in hook_map:
            hook_map[hook_type].append(hook_func)
        else:
            raise ValueError(f"Invalid hook type: {hook_type}") 