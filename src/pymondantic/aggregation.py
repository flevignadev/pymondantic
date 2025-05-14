"""
Aggregation pipeline builder for MongoDB operations.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from .models import MongoModel

T = TypeVar("T", bound=MongoModel)

class AggregationPipeline:
    """
    Builder for MongoDB aggregation pipelines.
    """
    
    def __init__(self, model: Type[T]):
        self.model = model
        self._pipeline: List[Dict[str, Any]] = []
    
    def match(self, **conditions: Any) -> "AggregationPipeline":
        """Add $match stage."""
        self._pipeline.append({"$match": conditions})
        return self
    
    def project(self, **fields: Any) -> "AggregationPipeline":
        """Add $project stage."""
        self._pipeline.append({"$project": fields})
        return self
    
    def group(
        self,
        _id: Any,
        **accumulators: Any
    ) -> "AggregationPipeline":
        """Add $group stage."""
        self._pipeline.append({
            "$group": {
                "_id": _id,
                **accumulators
            }
        })
        return self
    
    def sort(self, **fields: Any) -> "AggregationPipeline":
        """Add $sort stage."""
        self._pipeline.append({"$sort": fields})
        return self
    
    def limit(self, n: int) -> "AggregationPipeline":
        """Add $limit stage."""
        self._pipeline.append({"$limit": n})
        return self
    
    def skip(self, n: int) -> "AggregationPipeline":
        """Add $skip stage."""
        self._pipeline.append({"$skip": n})
        return self
    
    def lookup(
        self,
        from_: str,
        local_field: str,
        foreign_field: str,
        as_: str
    ) -> "AggregationPipeline":
        """Add $lookup stage."""
        self._pipeline.append({
            "$lookup": {
                "from": from_,
                "localField": local_field,
                "foreignField": foreign_field,
                "as": as_
            }
        })
        return self
    
    def unwind(
        self,
        path: str,
        preserve_null_and_empty_arrays: bool = False
    ) -> "AggregationPipeline":
        """Add $unwind stage."""
        self._pipeline.append({
            "$unwind": {
                "path": path,
                "preserveNullAndEmptyArrays": preserve_null_and_empty_arrays
            }
        })
        return self
    
    def facet(self, **facets: Any) -> "AggregationPipeline":
        """Add $facet stage."""
        self._pipeline.append({"$facet": facets})
        return self
    
    def add_fields(self, **fields: Any) -> "AggregationPipeline":
        """Add $addFields stage."""
        self._pipeline.append({"$addFields": fields})
        return self
    
    def set(self, **fields: Any) -> "AggregationPipeline":
        """Add $set stage."""
        self._pipeline.append({"$set": fields})
        return self
    
    def unset(self, *fields: str) -> "AggregationPipeline":
        """Add $unset stage."""
        self._pipeline.append({"$unset": fields})
        return self
    
    def replace_root(self, new_root: str) -> "AggregationPipeline":
        """Add $replaceRoot stage."""
        self._pipeline.append({"$replaceRoot": {"newRoot": new_root}})
        return self
    
    def count(self, field: str) -> "AggregationPipeline":
        """Add $count stage."""
        self._pipeline.append({"$count": field})
        return self
    
    def execute(self, db: Any) -> List[Dict[str, Any]]:
        """Execute the pipeline synchronously."""
        collection = self.model.get_collection(db)
        return list(collection.aggregate(self._pipeline))
    
    async def execute_async(self, db: Any) -> List[Dict[str, Any]]:
        """Execute the pipeline asynchronously."""
        collection = self.model.get_collection(db)
        cursor = collection.aggregate(self._pipeline)
        return [doc async for doc in cursor] 