"""
PyMondantic - A library combining Pydantic and PyMongo for type-safe MongoDB operations.
"""

from .models import MongoModel
from .client import MongoClient
from .fields import ObjectIdField

__version__ = "0.1.0"
__all__ = ["MongoModel", "MongoClient", "ObjectIdField"] 