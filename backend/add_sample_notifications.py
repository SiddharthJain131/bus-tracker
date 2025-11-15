#!/usr/bin/env python3
"""
Add Sample Notification Data
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid
from datetime import datetime, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def add_sample_notifications():
    print("\n📬 Adding sample notification entries...")
    
    # Get first admin user
    admin_user = await db.users.find_one({"role": "admin"})
    if not admin_user:
        print("❌ No admin user found")
        return
    
    admin_id = admin_user['user_id']
    
    # Sample notifications
    now = datetime.utcnow()
    sample_notifications = [
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": admin_id,
            "title": "System Update",
            "message": "Bus tracking system has been updated with new features",
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "read": False,
            "type": "update"
        },
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": admin_id,
            "title": "New Device Registered",
            "message": "A new Raspberry Pi device was registered for BUS-001",
            "timestamp": (now - timedelta(hours=5)).isoformat(),
            "read": False,
            "type": "update"
        },
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": admin_id,
            "title": "Attendance Summary",
            "message": "Daily attendance report: 18/20 students marked present",
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "read": True,
            "type": "update"
        },
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": admin_id,
            "title": "Holiday Reminder",
            "message": "Upcoming holiday: Christmas Day on December 25, 2025",
            "timestamp": (now - timedelta(days=2)).isoformat(),
            "read": True,
            "type": "update"
        },
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": admin_id,
            "title": "Backup Completed",
            "message": "Database backup completed successfully",
            "timestamp": (now - timedelta(days=3)).isoformat(),
            "read": True,
            "type": "update"
        }
    ]
    
    # Insert notifications
    result = await db.notifications.insert_many(sample_notifications)
    print(f"✅ Added {len(result.inserted_ids)} sample notifications")
    print(f"   User: {admin_user['name']} ({admin_user['email']})")

if __name__ == "__main__":
    asyncio.run(add_sample_notifications())
