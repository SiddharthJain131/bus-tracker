import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import bcrypt
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def seed_data():
    print("Seeding database...")
    
    # Clear existing data
    await db.users.delete_many({})
    await db.students.delete_many({})
    await db.attendance.delete_many({})
    await db.events.delete_many({})
    await db.bus_locations.delete_many({})
    await db.notifications.delete_many({})
    await db.holidays.delete_many({})
    
    # Create users
    parent_id = str(uuid.uuid4())
    teacher_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())
    
    student1_id = str(uuid.uuid4())
    student2_id = str(uuid.uuid4())
    student3_id = str(uuid.uuid4())
    
    users = [
        {
            "user_id": parent_id,
            "email": "parent@school.com",
            "password_hash": bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "parent",
            "name": "John Parent",
            "student_ids": [student1_id]
        },
        {
            "user_id": teacher_id,
            "email": "teacher@school.com",
            "password_hash": bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "teacher",
            "name": "Mary Teacher",
            "student_ids": [student1_id, student2_id, student3_id]
        },
        {
            "user_id": admin_id,
            "email": "admin@school.com",
            "password_hash": bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "admin",
            "name": "Admin User",
            "student_ids": []
        }
    ]
    
    await db.users.insert_many(users)
    print(f"Created {len(users)} users")
    
    # Create students
    students = [
        {
            "student_id": student1_id,
            "name": "Emma Johnson",
            "parent_id": parent_id,
            "bus_id": "BUS-001",
            "photo_ref": None
        },
        {
            "student_id": student2_id,
            "name": "Liam Smith",
            "parent_id": str(uuid.uuid4()),
            "bus_id": "BUS-001",
            "photo_ref": None
        },
        {
            "student_id": student3_id,
            "name": "Olivia Brown",
            "parent_id": str(uuid.uuid4()),
            "bus_id": "BUS-002",
            "photo_ref": None
        }
    ]
    
    await db.students.insert_many(students)
    print(f"Created {len(students)} students")
    
    # Create some sample attendance records
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    attendance_records = [
        {
            "attendance_id": str(uuid.uuid4()),
            "student_id": student1_id,
            "date": today,
            "trip": "AM",
            "status": "green",
            "confidence": 0.95,
            "last_update": datetime.now(timezone.utc).isoformat()
        },
        {
            "attendance_id": str(uuid.uuid4()),
            "student_id": student2_id,
            "date": today,
            "trip": "AM",
            "status": "yellow",
            "confidence": 0.92,
            "last_update": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.attendance.insert_many(attendance_records)
    print(f"Created {len(attendance_records)} attendance records")
    
    # Create initial bus location
    bus_location = {
        "bus_id": "BUS-001",
        "lat": 37.7749,
        "lon": -122.4194,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bus_locations.insert_one(bus_location)
    print("Created initial bus location")
    
    # Create sample holidays
    holidays = [
        {
            "holiday_id": str(uuid.uuid4()),
            "date": "2025-01-01",
            "name": "New Year's Day"
        },
        {
            "holiday_id": str(uuid.uuid4()),
            "date": "2025-12-25",
            "name": "Christmas Day"
        }
    ]
    
    await db.holidays.insert_many(holidays)
    print(f"Created {len(holidays)} holidays")
    
    print("Database seeding completed!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_data())
