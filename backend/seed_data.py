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
    await db.buses.delete_many({})
    await db.routes.delete_many({})
    await db.stops.delete_many({})
    await db.email_logs.delete_many({})
    
    # Create stops first
    stop1_id = str(uuid.uuid4())
    stop2_id = str(uuid.uuid4())
    stop3_id = str(uuid.uuid4())
    stop4_id = str(uuid.uuid4())
    
    stops = [
        {
            "stop_id": stop1_id,
            "stop_name": "Main Gate",
            "lat": 37.7749,
            "lon": -122.4194,
            "order_index": 0
        },
        {
            "stop_id": stop2_id,
            "stop_name": "Park Avenue",
            "lat": 37.7849,
            "lon": -122.4094,
            "order_index": 1
        },
        {
            "stop_id": stop3_id,
            "stop_name": "Market Street",
            "lat": 37.7949,
            "lon": -122.3994,
            "order_index": 2
        },
        {
            "stop_id": stop4_id,
            "stop_name": "School Entrance",
            "lat": 37.8049,
            "lon": -122.3894,
            "order_index": 3
        }
    ]
    
    await db.stops.insert_many(stops)
    print(f"Created {len(stops)} stops")
    
    # Create routes
    route1_id = str(uuid.uuid4())
    route2_id = str(uuid.uuid4())
    
    routes = [
        {
            "route_id": route1_id,
            "route_name": "Route A - North",
            "stop_ids": [stop1_id, stop2_id, stop3_id, stop4_id],
            "map_path": [
                {"lat": 37.7749, "lon": -122.4194},
                {"lat": 37.7849, "lon": -122.4094},
                {"lat": 37.7949, "lon": -122.3994},
                {"lat": 37.8049, "lon": -122.3894}
            ],
            "remarks": "Morning route covering north side"
        },
        {
            "route_id": route2_id,
            "route_name": "Route B - South",
            "stop_ids": [],
            "map_path": [
                {"lat": 37.7649, "lon": -122.4294},
                {"lat": 37.7749, "lon": -122.4194}
            ],
            "remarks": "Afternoon route covering south side"
        }
    ]
    
    await db.routes.insert_many(routes)
    print(f"Created {len(routes)} routes")
    
    # Create buses
    bus1_id = str(uuid.uuid4())
    bus2_id = str(uuid.uuid4())
    
    buses = [
        {
            "bus_id": bus1_id,
            "bus_number": "BUS-001",
            "driver_name": "Robert Driver",
            "driver_phone": "+1-555-0101",
            "route_id": route1_id,
            "capacity": 40,
            "remarks": "New bus with AC"
        },
        {
            "bus_id": bus2_id,
            "bus_number": "BUS-002",
            "driver_name": "Sarah Wheeler",
            "driver_phone": "+1-555-0102",
            "route_id": route2_id,
            "capacity": 35,
            "remarks": "Regular maintenance scheduled"
        }
    ]
    
    await db.buses.insert_many(buses)
    print(f"Created {len(buses)} buses")
    
    # Create users
    parent_id = str(uuid.uuid4())
    parent2_id = str(uuid.uuid4())
    parent3_id = str(uuid.uuid4())
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
            "phone": "+1-555-1001",
            "photo": None,
            "address": "123 Main St, San Francisco, CA",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student1_id]
        },
        {
            "user_id": parent2_id,
            "email": "parent2@school.com",
            "password_hash": bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "parent",
            "name": "Sarah Smith",
            "phone": "+1-555-1002",
            "photo": None,
            "address": "456 Oak Ave, San Francisco, CA",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student2_id]
        },
        {
            "user_id": parent3_id,
            "email": "parent3@school.com",
            "password_hash": bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "parent",
            "name": "Michael Brown",
            "phone": "+1-555-1003",
            "photo": None,
            "address": "789 Pine Rd, San Francisco, CA",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student3_id]
        },
        {
            "user_id": teacher_id,
            "email": "teacher@school.com",
            "password_hash": bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "teacher",
            "name": "Mary Teacher",
            "phone": "+1-555-2001",
            "photo": None,
            "address": "321 School Lane, San Francisco, CA",
            "assigned_class": "Grade 5",
            "assigned_section": "A",
            "student_ids": [student1_id, student2_id, student3_id]
        },
        {
            "user_id": admin_id,
            "email": "admin@school.com",
            "password_hash": bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "admin",
            "name": "Admin User",
            "phone": "+1-555-9999",
            "photo": None,
            "address": "School Office",
            "assigned_class": None,
            "assigned_section": None,
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
            "phone": "+1-555-3001",
            "photo": None,
            "class_name": "Grade 5",
            "section": "A",
            "parent_id": parent_id,
            "teacher_id": teacher_id,
            "bus_id": bus1_id,
            "stop_id": stop2_id,
            "emergency_contact": "+1-555-9001",
            "remarks": "Allergic to peanuts"
        },
        {
            "student_id": student2_id,
            "name": "Liam Smith",
            "phone": "+1-555-3002",
            "photo": None,
            "class_name": "Grade 5",
            "section": "A",
            "parent_id": parent2_id,
            "teacher_id": teacher_id,
            "bus_id": bus1_id,
            "stop_id": stop1_id,
            "emergency_contact": "+1-555-9002",
            "remarks": None
        },
        {
            "student_id": student3_id,
            "name": "Olivia Brown",
            "phone": "+1-555-3003",
            "photo": None,
            "class_name": "Grade 4",
            "section": "B",
            "parent_id": parent3_id,
            "teacher_id": teacher_id,
            "bus_id": bus2_id,
            "stop_id": None,
            "emergency_contact": "+1-555-9003",
            "remarks": None
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
    
    # Create initial bus locations
    bus_locations = [
        {
            "bus_id": bus1_id,
            "lat": 37.7749,
            "lon": -122.4194,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "bus_id": bus2_id,
            "lat": 37.7649,
            "lon": -122.4294,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    for loc in bus_locations:
        await db.bus_locations.insert_one(loc)
    print("Created initial bus locations")
    
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
