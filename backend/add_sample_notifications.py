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
    
    # Get users by role
    admin_user = await db.users.find_one({"role": "admin"})
    parent_user = await db.users.find_one({"email": "parent@school.com"})
    teacher_user = await db.users.find_one({"email": "teacher@school.com"})
    
    if not admin_user or not parent_user or not teacher_user:
        print("❌ Required users not found")
        return
    
    admin_id = admin_user['user_id']
    parent_id = parent_user['user_id']
    teacher_id = teacher_user['user_id']
    
    # Sample notifications
    now = datetime.utcnow()
    sample_notifications = [
        # Admin notifications
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
        
        # Parent notifications
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": parent_id,
            "title": "Bus Approaching",
            "message": "BUS-001 is approaching your child's stop. Estimated arrival in 5 minutes.",
            "timestamp": (now - timedelta(minutes=15)).isoformat(),
            "read": False,
            "type": "update"
        },
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": parent_id,
            "title": "Student Boarded",
            "message": "Emma Johnson has successfully boarded BUS-001 at 7:45 AM",
            "timestamp": (now - timedelta(hours=3)).isoformat(),
            "read": False,
            "type": "update"
        },
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": parent_id,
            "title": "Reached School",
            "message": "Emma Johnson reached school safely at 8:15 AM",
            "timestamp": (now - timedelta(hours=4)).isoformat(),
            "read": True,
            "type": "update"
        },
        
        # Teacher notifications
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": teacher_id,
            "title": "Class Schedule Update",
            "message": "Grade 5-A morning assembly rescheduled to 8:30 AM tomorrow",
            "timestamp": (now - timedelta(hours=1)).isoformat(),
            "read": False,
            "type": "update"
        },
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": teacher_id,
            "title": "Parent Meeting Reminder",
            "message": "Parent-teacher meeting scheduled for Friday at 3:00 PM in Room 205",
            "timestamp": (now - timedelta(hours=6)).isoformat(),
            "read": False,
            "type": "update"
        },
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": teacher_id,
            "title": "Attendance Alert",
            "message": "2 students absent in Grade 5-A today. Please update records.",
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "read": True,
            "type": "update"
        }
    ]
    
    # Insert notifications
    result = await db.notifications.insert_many(sample_notifications)
    print(f"✅ Added {len(result.inserted_ids)} sample notifications")
    print(f"   Admin: {admin_user['name']} - 3 notifications")
    print(f"   Parent: {parent_user['name']} - 3 notifications")
    print(f"   Teacher: {teacher_user['name']} - 3 notifications")

if __name__ == "__main__":
    asyncio.run(add_sample_notifications())
