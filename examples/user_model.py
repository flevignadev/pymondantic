"""
Example user model demonstrating PyMondantic features.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import Field, EmailStr
from pymondantic import MongoModel, ObjectIdField

class User(MongoModel):
    """
    Example user model with various field types and MongoDB features.
    """
    
    # Collection name for MongoDB
    collection_name = "users"
    
    # Define indexes
    indexes = [
        {"keys": [("email", 1)], "unique": True},
        {"keys": [("username", 1)], "unique": True},
        {"keys": [("created_at", -1)]}
    ]
    
    # Model fields
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password_hash: str
    full_name: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    is_active: bool = True
    roles: List[str] = ["user"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    # Reference to another document
    manager_id: Optional[ObjectIdField] = None
    
    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

# Example usage:
if __name__ == "__main__":
    from pymondantic import MongoClient
    
    # Initialize client
    client = MongoClient("mongodb://localhost:27017", "mydb")
    db = client.get_database()
    
    # Create indexes
    User.ensure_indexes(db)
    
    # Create a user
    user = User(
        username="johndoe",
        email="john@example.com",
        password_hash="hashed_password_here"
    )
    
    # Save to database
    user.save(db)
    
    # Find user
    found_user = User.find_one(db, {"username": "johndoe"})
    if found_user:
        print(f"Found user: {found_user.username}")
        
        # Update user
        found_user.full_name = "John Doe"
        found_user.update_timestamp()
        found_user.save(db) 