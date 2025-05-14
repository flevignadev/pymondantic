"""
Embedded document and query builder functionality for PyMondantic.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel, ConfigDict, Field
from .models import MongoModel

T = TypeVar("T", bound=BaseModel)

class EmbeddedDocument(BaseModel, Generic[T]):
    """
    Base class for embedded documents with automatic nesting/unpacking.
    """
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmbeddedDocument":
        """Create an embedded document from a dictionary."""
        return cls.model_validate(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the embedded document to a dictionary."""
        return self.model_dump(by_alias=True, exclude_none=True)

class QueryBuilder:
    """
    Query builder for MongoDB operations with Pydantic models.
    """
    
    def __init__(self, model: Type[MongoModel]):
        self.model = model
        self._filter: Dict[str, Any] = {}
        self._sort: List[tuple] = []
        self._skip: int = 0
        self._limit: int = 0
        self._projection: Optional[Dict[str, Any]] = None
    
    def filter(self, **kwargs: Any) -> "QueryBuilder":
        """Add filter conditions."""
        for key, value in kwargs.items():
            if isinstance(value, (list, tuple)):
                self._filter[key] = {"$in": value}
            else:
                self._filter[key] = value
        return self
    
    def sort(self, *fields: str, **kwargs: Any) -> "QueryBuilder":
        """Add sort conditions."""
        for field in fields:
            self._sort.append((field, 1))
        for field, direction in kwargs.items():
            self._sort.append((field, direction))
        return self
    
    def skip(self, n: int) -> "QueryBuilder":
        """Set skip value."""
        self._skip = n
        return self
    
    def limit(self, n: int) -> "QueryBuilder":
        """Set limit value."""
        self._limit = n
        return self
    
    def project(self, **fields: Any) -> "QueryBuilder":
        """Set projection fields."""
        self._projection = fields
        return self
    
    def find(self, db: Any) -> List[MongoModel]:
        """Execute the query synchronously."""
        return self.model.find(
            db,
            self._filter,
            skip=self._skip,
            limit=self._limit,
            sort=self._sort if self._sort else None,
            projection=self._projection
        )
    
    async def find_async(self, db: Any) -> List[MongoModel]:
        """Execute the query asynchronously."""
        return await self.model.find_async(
            db,
            self._filter,
            skip=self._skip,
            limit=self._limit,
            sort=self._sort if self._sort else None,
            projection=self._projection
        )
    
    def find_one(self, db: Any) -> Optional[MongoModel]:
        """Execute the query for one document synchronously."""
        return self.model.find_one(
            db,
            self._filter,
            projection=self._projection
        )
    
    async def find_one_async(self, db: Any) -> Optional[MongoModel]:
        """Execute the query for one document asynchronously."""
        return await self.model.find_one_async(
            db,
            self._filter,
            projection=self._projection
        ) 