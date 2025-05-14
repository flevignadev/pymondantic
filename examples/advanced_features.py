"""
Example demonstrating advanced PyMondantic features.
"""

import asyncio
from datetime import datetime
from typing import List, Optional
from pydantic import Field, EmailStr
from pymondantic import (
    MongoModel, MongoClient, ObjectIdField,
    EmbeddedDocument, QueryBuilder, CacheManager,
    MongoLogger, with_cache
)

# Example embedded document
class Address(EmbeddedDocument):
    street: str
    city: str
    country: str
    postal_code: str

# Example model with advanced features
class User(MongoModel):
    """Example user model with advanced features."""
    
    collection_name = "users"
    soft_delete = True
    versioning = True
    
    indexes = [
        {"keys": [("email", 1)], "unique": True},
        {"keys": [("username", 1)], "unique": True},
        {"keys": [("created_at", -1)]}
    ]
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password_hash: str
    full_name: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    is_active: bool = True
    roles: List[str] = ["user"]
    address: Optional[Address] = None
    manager_id: Optional[ObjectIdField] = None
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

# Example lifecycle hooks
def before_save_hook(user: User) -> None:
    """Hook to run before saving a user."""
    print(f"About to save user: {user.username}")

def after_save_hook(user: User) -> None:
    """Hook to run after saving a user."""
    print(f"Saved user: {user.username}")

# Register hooks
User.register_hook("before_save", before_save_hook)
User.register_hook("after_save", after_save_hook)

async def main():
    # Initialize clients
    mongo_client = MongoClient("mongodb://localhost:27017", "mydb")
    cache_manager = CacheManager("redis://localhost:6379")
    logger = MongoLogger()
    
    try:
        db = mongo_client.get_async_database()
        
        # Create a user with embedded address
        user = User(
            username="johndoe",
            email="john@example.com",
            password_hash="hashed_password_here",
            address=Address(
                street="123 Main St",
                city="New York",
                country="USA",
                postal_code="10001"
            )
        )
        
        # Save user (with hooks)
        await user.save_async(db)
        
        # Use query builder
        query = QueryBuilder(User)
        users = await query.filter(
            age={"$gt": 18},
            is_active=True
        ).sort(
            "created_at", -1
        ).limit(10).find_async(db)
        
        # Use caching
        @with_cache(cache_manager)
        async def get_user_by_email(email: str) -> Optional[User]:
            return await User.find_one_async(db, {"email": email})
        
        cached_user = await get_user_by_email("john@example.com")
        
        # Watch for changes
        async with User.watch_async(db) as stream:
            async for change in stream:
                print(f"Change detected: {change}")
        
        # Soft delete
        await user.delete_async(db)  # Sets is_deleted=True
        
        # Hard delete
        await user.delete_async(db, hard=True)  # Actually deletes the document
        
    finally:
        await mongo_client.close_async()

if __name__ == "__main__":
    asyncio.run(main()) 