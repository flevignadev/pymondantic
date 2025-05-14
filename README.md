# PyMondantic

A powerful Python library that seamlessly integrates Pydantic for data modeling and validation with PyMongo for MongoDB interaction. PyMondantic provides a modern, type-safe, and developer-friendly way to work with MongoDB in Python applications.

## Features

### Core Features
- 🎯 Automatic schema inference from Pydantic models
- 🔄 Native support for ObjectId fields
- 🛠️ Built-in CRUD operations
- 🔌 Easy MongoDB client setup
- 📝 Configurable collection names
- 🏷️ Full type hinting support

### Advanced Features
- 🔄 Lifecycle hooks for model operations
- 📄 Embedded document support
- 🔍 Fluent query builder interface
- 🗑️ Soft delete functionality
- 📊 Data versioning
- 🔔 Change streams support
- 💾 Redis caching integration
- 📊 OpenTelemetry logging

### Polymorphic Support
- 🎭 Polymorphic document support
- 🔄 Schema migration utilities
- 📦 Bulk operations
- 🔄 Aggregation pipeline builder

## Installation

```bash
pip install pymondantic
```

## Quick Start

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from pymondantic import MongoModel, ObjectId

# Define your model
class User(MongoModel):
    name: str
    email: EmailStr
    age: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Initialize MongoDB client
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client["mydatabase"]

# Create and save a user
user = User(name="John Doe", email="john@example.com", age=30)
user.save(db)

# Find users
users = User.find(db, {"age": {"$gt": 25}})
```

## Advanced Usage

### Embedded Documents

```python
from pymondantic import EmbeddedDocument

class Address(EmbeddedDocument):
    street: str
    city: str
    country: str

class User(MongoModel):
    name: str
    address: Address
```

### Query Builder

```python
from pymondantic import QueryBuilder

# Build complex queries
query = QueryBuilder(User)
results = query.filter(age__gt=25).sort(name=1).limit(10).find(db)
```

### Lifecycle Hooks

```python
class User(MongoModel):
    def before_save(self):
        self.updated_at = datetime.utcnow()

    def after_save(self):
        print(f"User {self.name} was saved")
```

### Caching

```python
from pymondantic import with_cache

@with_cache(ttl=3600)
def get_user_by_email(email: str):
    return User.find_one(db, {"email": email})
```

### Aggregation Pipeline

```python
from pymondantic import AggregationPipeline

# Build and execute aggregation pipeline
pipeline = AggregationPipeline(User)
results = pipeline.match(age__gt=25).group(
    _id="$city",
    count={"$sum": 1},
    avg_age={"$avg": "$age"}
).execute(db)
```

### Polymorphic Documents

```python
from pymondantic import PolymorphicModel

class Animal(PolymorphicModel):
    name: str
    type: str = Field(discriminator=True)

class Dog(Animal):
    type: str = "dog"
    breed: str

class Cat(Animal):
    type: str = "cat"
    color: str
```

### Bulk Operations

```python
from pymondantic import BulkOperations

# Perform bulk operations
bulk = BulkOperations(User)
bulk.insert_many([user1, user2, user3])
bulk.update_many({"age": {"$lt": 18}}, {"$set": {"status": "minor"}})
bulk.execute(db)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 