"""
Example demonstrating async usage of PyMondantic.
"""

import asyncio
from datetime import datetime
from typing import List
from pymondantic import MongoModel, MongoClient, ObjectIdField

class Post(MongoModel):
    """Example blog post model."""
    
    collection_name = "posts"
    
    indexes = [
        {"keys": [("slug", 1)], "unique": True},
        {"keys": [("author_id", 1)]},
        {"keys": [("created_at", -1)]}
    ]
    
    title: str
    slug: str
    content: str
    author_id: ObjectIdField
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

async def main():
    # Initialize client
    client = MongoClient("mongodb://localhost:27017", "mydb")
    db = client.get_async_database()
    
    try:
        # Create a post
        post = Post(
            title="Async MongoDB with PyMondantic",
            slug="async-mongodb-pymondantic",
            content="This is a test post about async operations...",
            author_id=ObjectIdField("507f1f77bcf86cd799439011")
        )
        
        # Save post
        await post.save_async(db)
        print(f"Created post: {post.title}")
        
        # Find posts by author
        posts = await Post.find_async(
            db,
            {"author_id": post.author_id}
        )
        print(f"Found {len(posts)} posts by author")
        
        # Update post
        post.tags = ["mongodb", "async", "python"]
        post.updated_at = datetime.utcnow()
        await post.save_async(db)
        
        # Find one post
        found_post = await Post.find_one_async(
            db,
            {"slug": post.slug}
        )
        if found_post:
            print(f"Found post: {found_post.title}")
            print(f"Tags: {found_post.tags}")
        
    finally:
        # Clean up
        await client.close_async()

if __name__ == "__main__":
    asyncio.run(main()) 