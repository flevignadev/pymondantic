"""
Polymorphic document support and schema migration utilities.
"""

from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar, Union
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from .models import MongoModel

T = TypeVar("T", bound="PolymorphicModel")

class PolymorphicModel(MongoModel):
    """
    Base class for polymorphic documents with discriminator field.
    """
    
    # Configuration
    discriminator_field: ClassVar[str] = "_type"
    discriminator_mapping: ClassVar[Dict[str, Type["PolymorphicModel"]]] = {}
    
    # Common fields
    _type: str = Field(..., alias=discriminator_field)
    
    @classmethod
    def register_type(cls, type_name: str, model_class: Type["PolymorphicModel"]) -> None:
        """Register a model class for a specific type."""
        cls.discriminator_mapping[type_name] = model_class
    
    @classmethod
    def model_validate(cls: Type[T], obj: Any) -> T:
        """Override model validation to handle polymorphic types."""
        if isinstance(obj, dict):
            type_name = obj.get(cls.discriminator_field)
            if type_name and type_name in cls.discriminator_mapping:
                return cls.discriminator_mapping[type_name].model_validate(obj)
        return super().model_validate(obj)

class SchemaMigration:
    """
    Utility for handling schema migrations.
    """
    
    def __init__(self, model: Type[MongoModel]):
        self.model = model
        self._migrations: List[Dict[str, Any]] = []
    
    def add_migration(
        self,
        version: int,
        up: Dict[str, Any],
        down: Dict[str, Any]
    ) -> None:
        """Add a migration step."""
        self._migrations.append({
            "version": version,
            "up": up,
            "down": down,
            "applied_at": None
        })
    
    async def migrate_up(
        self,
        db: Any,
        target_version: Optional[int] = None
    ) -> None:
        """Apply migrations up to target version."""
        collection = self.model.get_collection(db)
        current_version = await self._get_current_version(collection)
        
        for migration in sorted(
            [m for m in self._migrations if m["version"] > current_version],
            key=lambda x: x["version"]
        ):
            if target_version and migration["version"] > target_version:
                break
                
            await collection.update_many(
                {},
                migration["up"]
            )
            migration["applied_at"] = datetime.utcnow()
    
    async def migrate_down(
        self,
        db: Any,
        target_version: Optional[int] = None
    ) -> None:
        """Rollback migrations down to target version."""
        collection = self.model.get_collection(db)
        current_version = await self._get_current_version(collection)
        
        for migration in sorted(
            [m for m in self._migrations if m["version"] <= current_version],
            key=lambda x: x["version"],
            reverse=True
        ):
            if target_version and migration["version"] <= target_version:
                break
                
            await collection.update_many(
                {},
                migration["down"]
            )
            migration["applied_at"] = None
    
    async def _get_current_version(self, collection: Any) -> int:
        """Get current schema version."""
        result = await collection.find_one(
            {},
            projection={"_schema_version": 1}
        )
        return result.get("_schema_version", 0) if result else 0

class BulkOperations:
    """
    Utility for bulk database operations.
    """
    
    def __init__(self, model: Type[MongoModel]):
        self.model = model
        self._operations: List[Dict[str, Any]] = []
    
    def insert(self, documents: List[MongoModel]) -> None:
        """Add insert operations."""
        self._operations.extend([
            {
                "insertOne": {
                    "document": doc.model_dump(by_alias=True, exclude_none=True)
                }
            }
            for doc in documents
        ])
    
    def update(
        self,
        filter_dict: Dict[str, Any],
        update_dict: Dict[str, Any],
        upsert: bool = False
    ) -> None:
        """Add update operation."""
        self._operations.append({
            "updateMany": {
                "filter": filter_dict,
                "update": update_dict,
                "upsert": upsert
            }
        })
    
    def delete(self, filter_dict: Dict[str, Any]) -> None:
        """Add delete operation."""
        self._operations.append({
            "deleteMany": {
                "filter": filter_dict
            }
        })
    
    async def execute(self, db: Any) -> Dict[str, Any]:
        """Execute bulk operations."""
        collection = self.model.get_collection(db)
        return await collection.bulk_write(self._operations) 