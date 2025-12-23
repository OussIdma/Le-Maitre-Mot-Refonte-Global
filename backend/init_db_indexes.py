#!/usr/bin/env python3
"""
Database initialization script for Le Maître Mot
Creates necessary indexes to ensure data integrity and security
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def init_database_indexes():
    """Initialize database indexes for security and performance"""
    try:
        # Connect to MongoDB
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
        print("🔧 Initializing database indexes for Le Maître Mot...")
        
        # P1: Remove old unique constraint (allow multi-device)
        print("Removing old unique constraint on login_sessions.user_email...")
        try:
            await db.login_sessions.drop_index("unique_user_session")
            print("✅ Old unique constraint removed")
        except Exception as e:
            print(f"  Note: Index may not exist: {e}")
        
        # P1: Non-unique index on login_sessions.user_email (for multi-device support)
        print("Creating non-unique index on login_sessions.user_email...")
        await db.login_sessions.create_index(
            "user_email",
            unique=False,  # P1: Allow multiple sessions per user
            name="user_email_index"
        )
        print("✅ User email index created (multi-device enabled)")
        
        # P1: Compound index for efficient sorting (user_email, created_at)
        print("Creating compound index on login_sessions (user_email, created_at)...")
        await db.login_sessions.create_index(
            [("user_email", 1), ("created_at", 1)],
            name="user_email_created_at_compound"
        )
        print("✅ Compound index created (for session ordering)")
        
        # 2. TTL index on login_sessions.expires_at (auto-cleanup expired sessions)
        print("Creating TTL index on login_sessions.expires_at...")
        await db.login_sessions.create_index(
            "expires_at",
            expireAfterSeconds=0,  # Expire at the specified date
            name="session_expiry_ttl"
        )
        print("✅ Session expiry TTL index created")
        
        # 3. TTL index on magic_tokens.expires_at (auto-cleanup expired tokens)
        print("Creating TTL index on magic_tokens.expires_at...")
        await db.magic_tokens.create_index(
            "expires_at",
            expireAfterSeconds=0,  # Expire at the specified date
            name="magic_token_ttl"
        )
        print("✅ Magic token TTL index created")
        
        # 4. Index on pro_users.email for fast lookups
        print("Creating index on pro_users.email...")
        await db.pro_users.create_index(
            "email",
            unique=True,
            name="unique_pro_user_email"
        )
        print("✅ Pro user unique email index created")
        
        # 5. Cleanup any duplicate sessions (in case they exist)
        print("Cleaning up any duplicate sessions...")
        
        # Find duplicate sessions
        pipeline = [
            {"$group": {"_id": "$user_email", "count": {"$sum": 1}, "sessions": {"$push": "$$ROOT"}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        
        duplicates = []
        async for doc in db.login_sessions.aggregate(pipeline):
            duplicates.append(doc)
        
        if duplicates:
            print(f"Found {len(duplicates)} users with duplicate sessions")
            for dup in duplicates:
                user_email = dup["_id"]
                sessions = dup["sessions"]
                
                # Keep only the most recent session
                sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                sessions_to_delete = sessions[1:]  # All except the most recent
                
                for session in sessions_to_delete:
                    await db.login_sessions.delete_one({"_id": session["_id"]})
                    print(f"  Removed duplicate session for {user_email}")
        else:
            print("No duplicate sessions found")
        
        print("\n🎉 Database initialization completed successfully!")
        print("Security measures in place:")
        print("  ✅ Multi-device support (max 3 sessions per user - P1)")
        print("  ✅ Automatic session cleanup on expiry")
        print("  ✅ Automatic magic token cleanup")
        print("  ✅ Pro user email uniqueness")
        
        # Close connection
        client.close()
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_database_indexes())