"""
Custom field types for PyMondantic.
"""

from typing import Any, Optional
from bson import ObjectId
from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema
from pydantic_core.core_schema import ValidationInfo

class ObjectIdField:
    """
    Custom field type for MongoDB ObjectId with validation.
    """
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v: Any, info: ValidationInfo) -> ObjectId:
        """Validate and convert input to ObjectId."""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            try:
                return ObjectId(v)
            except Exception as e:
                raise ValueError(f"Invalid ObjectId string: {e}")
        raise ValueError("ObjectId must be a string or ObjectId instance")
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetJsonSchemaHandler,
    ) -> CoreSchema:
        """Get the core schema for the field."""
        return core_schema.json_or_python_schema(
            json_schema=core_schema.string_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.string_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate)
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x) if isinstance(x, ObjectId) else x
            )
        )
    
    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _core_schema: CoreSchema,
        _handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        """Get the JSON schema for the field."""
        return {
            "type": "string",
            "description": "MongoDB ObjectId",
            "examples": ["507f1f77bcf86cd799439011"]
        } 