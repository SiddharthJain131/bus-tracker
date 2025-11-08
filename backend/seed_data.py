"""
Comprehensive Seed Data Generator for Bus Tracker System
Creates realistic demo data for all roles and entities with proper linking
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import bcrypt
import uuid
from datetime import datetime, timezone, timedelta
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Test credentials for easy login
TEST_CREDENTIALS = """
===========================================
📝 DEMO LOGIN CREDENTIALS
===========================================

🔐 ADMIN ACCOUNTS:
  Email: admin@school.com
  Password: password
  Role: Primary Administrator (⭐ Elevated Admin - Can manage other admins)
  ---
  Email: admin2@school.com
  Password: password
  Role: Secondary Administrator (Regular Admin)

👨‍🏫 TEACHER ACCOUNTS:
  Email: teacher@school.com
  Password: password
  Name: Mary Johnson
  Class: Grade 5 - Section A
  ---
  Email: teacher2@school.com
  Password: password
  Name: Robert Smith
  Class: Grade 6 - Section B
  ---
  Email: teacher3@school.com
  Password: password
  Name: Sarah Wilson
  Class: Grade 4 - Section A

👪 PARENT ACCOUNTS:
  Email: parent@school.com
  Password: password
  Children: Emma Johnson (Grade 5-A)
  ---
  Email: parent2@school.com
  Password: password
  Children: Liam Smith (Grade 5-A)
  ---
  Email: parent3@school.com
  Password: password
  Children: Olivia Brown (Grade 4-A)
  ---
  Email: parent4@school.com
  Password: password
  Children: Noah Davis (Grade 6-B)
  ---
  Email: parent5@school.com
  Password: password
  Children: Ava Martinez (Grade 6-B)
  ---
  [... and more parents linked to students]

===========================================
"""

async def seed_data():
    print("=" * 60)
    print("🌱 STARTING COMPREHENSIVE DATABASE SEEDING")
    print("=" * 60)
    
    # Clear existing data
    collections = ['users', 'students', 'attendance', 'events', 'bus_locations', 
                  'notifications', 'holidays', 'buses', 'routes', 'stops', 'email_logs']
    
    for collection in collections:
        count = await db[collection].count_documents({})
        await db[collection].delete_many({})
        print(f"✅ Cleared {count} records from {collection}")
    
    print("\n" + "=" * 60)
    print("📍 CREATING STOPS AND ROUTES")
    print("=" * 60)
    
    # Create stops for Route 1 (North Route)
    route1_stops_data = [
        {"name": "Main Gate North", "lat": 37.7749, "lon": -122.4194},
        {"name": "Park Avenue", "lat": 37.7849, "lon": -122.4094},
        {"name": "Market Street", "lat": 37.7949, "lon": -122.3994},
        {"name": "Oak Boulevard", "lat": 37.8019, "lon": -122.3944},
        {"name": "School North Entrance", "lat": 37.8049, "lon": -122.3894}
    ]
    
    # Create stops for Route 2 (South Route)
    route2_stops_data = [
        {"name": "South Gate", "lat": 37.7649, "lon": -122.4294},
        {"name": "Elm Street", "lat": 37.7699, "lon": -122.4244},
        {"name": "Maple Avenue", "lat": 37.7749, "lon": -122.4194},
        {"name": "Pine Road", "lat": 37.7799, "lon": -122.4144}
    ]
    
    # Create stops for Route 3 (East Route)
    route3_stops_data = [
        {"name": "East Gate", "lat": 37.7849, "lon": -122.3794},
        {"name": "Cedar Lane", "lat": 37.7899, "lon": -122.3844},
        {"name": "Birch Street", "lat": 37.7949, "lon": -122.3894},
        {"name": "Walnut Drive", "lat": 37.7999, "lon": -122.3944},
        {"name": "School East Entrance", "lat": 37.8049, "lon": -122.3894}
    ]
    
    # Create stops for Route 4 (West Route)
    route4_stops_data = [
        {"name": "West Gate", "lat": 37.7749, "lon": -122.4394},
        {"name": "Sunset Boulevard", "lat": 37.7799, "lon": -122.4344},
        {"name": "Ocean Avenue", "lat": 37.7849, "lon": -122.4294},
        {"name": "Beach Street", "lat": 37.7899, "lon": -122.4244},
        {"name": "Harbor Road", "lat": 37.7949, "lon": -122.4194},
        {"name": "School West Entrance", "lat": 37.8049, "lon": -122.3894}
    ]
    
    # Create all stops
    all_stops = []
    route1_stop_ids = []
    route2_stop_ids = []
    route3_stop_ids = []
    route4_stop_ids = []
    
    for idx, stop_data in enumerate(route1_stops_data):
        stop_id = str(uuid.uuid4())
        route1_stop_ids.append(stop_id)
        all_stops.append({
            "stop_id": stop_id,
            "stop_name": stop_data["name"],
            "lat": stop_data["lat"],
            "lon": stop_data["lon"],
            "order_index": idx
        })
    
    for idx, stop_data in enumerate(route2_stops_data):
        stop_id = str(uuid.uuid4())
        route2_stop_ids.append(stop_id)
        all_stops.append({
            "stop_id": stop_id,
            "stop_name": stop_data["name"],
            "lat": stop_data["lat"],
            "lon": stop_data["lon"],
            "order_index": idx
        })
    
    for idx, stop_data in enumerate(route3_stops_data):
        stop_id = str(uuid.uuid4())
        route3_stop_ids.append(stop_id)
        all_stops.append({
            "stop_id": stop_id,
            "stop_name": stop_data["name"],
            "lat": stop_data["lat"],
            "lon": stop_data["lon"],
            "order_index": idx
        })
    
    for idx, stop_data in enumerate(route4_stops_data):
        stop_id = str(uuid.uuid4())
        route4_stop_ids.append(stop_id)
        all_stops.append({
            "stop_id": stop_id,
            "stop_name": stop_data["name"],
            "lat": stop_data["lat"],
            "lon": stop_data["lon"],
            "order_index": idx
        })
    
    await db.stops.insert_many(all_stops)
    print(f"✅ Created {len(all_stops)} stops across 4 routes")
    
    # Create routes
    route1_id = str(uuid.uuid4())
    route2_id = str(uuid.uuid4())
    route3_id = str(uuid.uuid4())
    route4_id = str(uuid.uuid4())
    
    routes = [
        {
            "route_id": route1_id,
            "route_name": "Route A - North District",
            "stop_ids": route1_stop_ids,
            "map_path": [{"lat": s["lat"], "lon": s["lon"]} for s in route1_stops_data],
            "remarks": "Morning route covering north residential area"
        },
        {
            "route_id": route2_id,
            "route_name": "Route B - South District",
            "stop_ids": route2_stop_ids,
            "map_path": [{"lat": s["lat"], "lon": s["lon"]} for s in route2_stops_data],
            "remarks": "Morning route covering south residential area"
        },
        {
            "route_id": route3_id,
            "route_name": "Route C - East District",
            "stop_ids": route3_stop_ids,
            "map_path": [{"lat": s["lat"], "lon": s["lon"]} for s in route3_stops_data],
            "remarks": "Afternoon route covering east business district"
        },
        {
            "route_id": route4_id,
            "route_name": "Route D - West District",
            "stop_ids": route4_stop_ids,
            "map_path": [{"lat": s["lat"], "lon": s["lon"]} for s in route4_stops_data],
            "remarks": "Afternoon route covering west coastal area"
        }
    ]
    
    await db.routes.insert_many(routes)
    print(f"✅ Created {len(routes)} routes")
    
    print("\n" + "=" * 60)
    print("🚌 CREATING BUSES")
    print("=" * 60)
    
    # Create buses with varying capacities for testing
    bus1_id = str(uuid.uuid4())
    bus2_id = str(uuid.uuid4())
    bus3_id = str(uuid.uuid4())
    bus4_id = str(uuid.uuid4())
    
    buses = [
        {
            "bus_id": bus1_id,
            "bus_number": "BUS-001",
            "driver_name": "Robert Johnson",
            "driver_phone": "+1-555-0101",
            "route_id": route1_id,
            "capacity": 5,  # Small capacity for testing capacity warnings
            "remarks": "Test bus - Small capacity (5 students)"
        },
        {
            "bus_id": bus2_id,
            "bus_number": "BUS-002",
            "driver_name": "Sarah Martinez",
            "driver_phone": "+1-555-0102",
            "route_id": route2_id,
            "capacity": 3,  # Very small capacity - will trigger warning
            "remarks": "Test bus - Very small capacity (3 students)"
        },
        {
            "bus_id": bus3_id,
            "bus_number": "BUS-003",
            "driver_name": "Michael Chen",
            "driver_phone": "+1-555-0103",
            "route_id": route3_id,
            "capacity": 45,
            "remarks": "Large capacity bus for busy route"
        },
        {
            "bus_id": bus4_id,
            "bus_number": "BUS-004",
            "driver_name": "Lisa Anderson",
            "driver_phone": "+1-555-0104",
            "route_id": route4_id,
            "capacity": 38,
            "remarks": "Standard capacity coastal route"
        }
    ]
    
    await db.buses.insert_many(buses)
    print(f"✅ Created {len(buses)} buses with drivers")
    
    print("\n" + "=" * 60)
    print("👥 CREATING USERS (ADMINS, TEACHERS, PARENTS)")
    print("=" * 60)
    
    # Generate password hash once (same password for all demo accounts)
    password_hash = bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create admins
    admin1_id = str(uuid.uuid4())
    admin2_id = str(uuid.uuid4())
    
    # Create teachers
    teacher1_id = str(uuid.uuid4())
    teacher2_id = str(uuid.uuid4())
    teacher3_id = str(uuid.uuid4())
    
    # Pre-generate student IDs for linking
    # Creating 20 students with some sharing parents (Many:1 relationship test)
    student_ids = [str(uuid.uuid4()) for _ in range(20)]
    
    # Create parent IDs - fewer parents than students to demonstrate Many:1
    # 12 parents for 20 students = multiple children per parent
    parent_ids = [str(uuid.uuid4()) for _ in range(12)]
    
    users = [
        # ADMINS
        {
            "user_id": admin1_id,
            "email": "admin@school.com",
            "password_hash": password_hash,
            "role": "admin",
            "name": "James Anderson",
            "phone": "+1-555-9001",
            "photo": None,
            "address": "School Administration Office, Main Building",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [],
            "is_elevated_admin": True
        },
        {
            "user_id": admin2_id,
            "email": "admin2@school.com",
            "password_hash": password_hash,
            "role": "admin",
            "name": "Patricia Williams",
            "phone": "+1-555-9002",
            "photo": None,
            "address": "School Administration Office, East Wing",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [],
            "is_elevated_admin": False
        },
        
        # TEACHERS
        {
            "user_id": teacher1_id,
            "email": "teacher@school.com",
            "password_hash": password_hash,
            "role": "teacher",
            "name": "Mary Johnson",
            "phone": "+1-555-2001",
            "photo": None,
            "address": "321 Teacher Lane, San Francisco, CA",
            "assigned_class": "Grade 5",
            "assigned_section": "A",
            "student_ids": [student_ids[0], student_ids[1], student_ids[2], student_ids[3], student_ids[4], student_ids[15], student_ids[18]],
            "is_elevated_admin": False
        },
        {
            "user_id": teacher2_id,
            "email": "teacher2@school.com",
            "password_hash": password_hash,
            "role": "teacher",
            "name": "Robert Smith",
            "phone": "+1-555-2002",
            "photo": None,
            "address": "456 Educator Drive, San Francisco, CA",
            "assigned_class": "Grade 6",
            "assigned_section": "B",
            "student_ids": [student_ids[5], student_ids[6], student_ids[7], student_ids[8], student_ids[9], student_ids[16], student_ids[19]],
            "is_elevated_admin": False
        },
        {
            "user_id": teacher3_id,
            "email": "teacher3@school.com",
            "password_hash": password_hash,
            "role": "teacher",
            "name": "Sarah Wilson",
            "phone": "+1-555-2003",
            "photo": None,
            "address": "789 School Street, San Francisco, CA",
            "assigned_class": "Grade 4",
            "assigned_section": "A",
            "student_ids": [student_ids[10], student_ids[11], student_ids[12], student_ids[13], student_ids[14], student_ids[17]],
            "is_elevated_admin": False
        },
        
        # PARENTS (12 parents for 20 students - demonstrating Many:1 relationship)
        {
            "user_id": parent_ids[0],
            "email": "parent@school.com",
            "password_hash": password_hash,
            "role": "parent",
            "name": "John Parent",
            "phone": "+1-555-3001",
            "photo": None,
            "address": "123 Oak St, San Francisco, CA 94102",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student_ids[0], student_ids[1]],  # TWO children: Emma & Liam
            "is_elevated_admin": False
        },
        {
            "user_id": parent_ids[1],
            "email": "parent2@school.com",
            "password_hash": password_hash,
            "role": "parent",
            "name": "Sarah Brown",
            "phone": "+1-555-3002",
            "photo": None,
            "address": "456 Pine Ave, San Francisco, CA 94103",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student_ids[2]],  # ONE child: Sophia
            "is_elevated_admin": False
        },
        {
            "user_id": parent_ids[2],
            "email": "parent3@school.com",
            "password_hash": password_hash,
            "role": "parent",
            "name": "Michael Davis",
            "phone": "+1-555-3003",
            "photo": None,
            "address": "789 Elm St, San Francisco, CA 94104",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student_ids[3], student_ids[4]],  # TWO children: Noah & Olivia
            "is_elevated_admin": False
        },
        {
            "user_id": parent_ids[3],
            "email": "parent4@school.com",
            "password_hash": password_hash,
            "role": "parent",
            "name": "Emily Martinez",
            "phone": "+1-555-3004",
            "photo": None,
            "address": "234 Maple Dr, San Francisco, CA 94105",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student_ids[5], student_ids[6], student_ids[7]],  # THREE children: Ethan, Ava, Mason
            "is_elevated_admin": False
        },
        {
            "user_id": parent_ids[4],
            "email": "parent5@school.com",
            "password_hash": password_hash,
            "role": "parent",
            "name": "David Wilson",
            "phone": "+1-555-3005",
            "photo": None,
            "address": "567 Cedar Ln, San Francisco, CA 94106",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student_ids[8], student_ids[9]],  # TWO children: Isabella, James
            "is_elevated_admin": False
        },
        {
            "user_id": parent_ids[5],
            "email": "parent6@school.com",
            "password_hash": password_hash,
            "role": "parent",
            "name": "Jennifer Taylor",
            "phone": "+1-555-3006",
            "photo": None,
            "address": "890 Birch Ave, San Francisco, CA 94107",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student_ids[10]],  # ONE child: Charlotte
            "is_elevated_admin": False
        },
        {
            "user_id": parent_ids[6],
            "email": "parent7@school.com",
            "password_hash": password_hash,
            "role": "parent",
            "name": "Christopher Garcia",
            "phone": "+1-555-3007",
            "photo": None,
            "address": "123 Walnut St, San Francisco, CA 94108",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student_ids[11], student_ids[12]],  # TWO children: Benjamin, Amelia
            "is_elevated_admin": False
        },
        {
            "user_id": parent_ids[7],
            "email": "parent8@school.com",
            "password_hash": password_hash,
            "role": "parent",
            "name": "Amanda Rodriguez",
            "phone": "+1-555-3008",
            "photo": None,
            "address": "456 Sunset Blvd, San Francisco, CA 94109",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student_ids[13]],  # ONE child: Lucas
            "is_elevated_admin": False
        },
        {
            "user_id": parent_ids[8],
            "email": "parent9@school.com",
            "password_hash": password_hash,
            "role": "parent",
            "name": "Matthew Lee",
            "phone": "+1-555-3009",
            "photo": None,
            "address": "789 Ocean Ave, San Francisco, CA 94110",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student_ids[14], student_ids[15]],  # TWO children: Mia, Alexander
            "is_elevated_admin": False
        },
        {
            "user_id": parent_ids[9],
            "email": "parent10@school.com",
            "password_hash": password_hash,
            "role": "parent",
            "name": "Jessica Harris",
            "phone": "+1-555-3010",
            "photo": None,
            "address": "234 Beach St, San Francisco, CA 94111",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student_ids[16]],  # ONE child: Harper
            "is_elevated_admin": False
        },
        {
            "user_id": parent_ids[10],
            "email": "parent11@school.com",
            "password_hash": password_hash,
            "role": "parent",
            "name": "Daniel Clark",
            "phone": "+1-555-3011",
            "photo": None,
            "address": "567 Harbor Rd, San Francisco, CA 94112",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student_ids[17], student_ids[18]],  # TWO children: Evelyn, Henry
            "is_elevated_admin": False
        },
        {
            "user_id": parent_ids[11],
            "email": "parent12@school.com",
            "password_hash": password_hash,
            "role": "parent",
            "name": "Lisa Lewis",
            "phone": "+1-555-3012",
            "photo": None,
            "address": "890 Market St, San Francisco, CA 94113",
            "assigned_class": None,
            "assigned_section": None,
            "student_ids": [student_ids[19]],  # ONE child: Sebastian
            "is_elevated_admin": False
        }
    ]
    
    await db.users.insert_many(users)
    print(f"✅ Created {len(users)} users (2 admins, 3 teachers, 12 parents)")
    
    print("\n" + "=" * 60)
    print("👦 CREATING STUDENTS")
    print("=" * 60)
    
    # Create students with proper linking
    students_data = [
        # Grade 5 - Section A (Teacher 1)
        {
            "student_id": student_ids[0],
            "name": "Emma Johnson",
            "roll_number": "G5A-001",
            "phone": "+1-555-4001",
            "photo": None,
            "class_name": "Grade 5",
            "section": "A",
            "parent_id": parent_ids[0],
            "teacher_id": teacher1_id,
            "bus_id": bus1_id,
            "stop_id": route1_stop_ids[1],
            "emergency_contact": "+1-555-9101",
            "remarks": "Allergic to peanuts"
        },
        {
            "student_id": student_ids[1],
            "name": "Liam Smith",
            "roll_number": "G5A-002",
            "phone": "+1-555-4002",
            "photo": None,
            "class_name": "Grade 5",
            "section": "A",
            "parent_id": parent_ids[1],
            "teacher_id": teacher1_id,
            "bus_id": bus1_id,
            "stop_id": route1_stop_ids[2],
            "emergency_contact": "+1-555-9102",
            "remarks": None
        },
        {
            "student_id": student_ids[2],
            "name": "Sophia Brown",
            "roll_number": "G5A-003",
            "phone": "+1-555-4003",
            "photo": None,
            "class_name": "Grade 5",
            "section": "A",
            "parent_id": parent_ids[2],
            "teacher_id": teacher1_id,
            "bus_id": bus2_id,
            "stop_id": route2_stop_ids[0],
            "emergency_contact": "+1-555-9103",
            "remarks": "Needs glasses for reading"
        },
        {
            "student_id": student_ids[3],
            "name": "Noah Davis",
            "roll_number": "G5A-004",
            "phone": "+1-555-4004",
            "photo": None,
            "class_name": "Grade 5",
            "section": "A",
            "parent_id": parent_ids[3],
            "teacher_id": teacher1_id,
            "bus_id": bus2_id,
            "stop_id": route2_stop_ids[1],
            "emergency_contact": "+1-555-9104",
            "remarks": None
        },
        {
            "student_id": student_ids[4],
            "name": "Olivia Martinez",
            "roll_number": "G5A-005",
            "phone": "+1-555-4005",
            "photo": None,
            "class_name": "Grade 5",
            "section": "A",
            "parent_id": parent_ids[4],
            "teacher_id": teacher1_id,
            "bus_id": bus3_id,
            "stop_id": route3_stop_ids[0],
            "emergency_contact": "+1-555-9105",
            "remarks": "School choir member"
        },
        
        # Grade 6 - Section B (Teacher 2)
        {
            "student_id": student_ids[5],
            "name": "Ethan Wilson",
            "roll_number": "G6B-001",
            "phone": "+1-555-4006",
            "photo": None,
            "class_name": "Grade 6",
            "section": "B",
            "parent_id": parent_ids[5],
            "teacher_id": teacher2_id,
            "bus_id": bus3_id,
            "stop_id": route3_stop_ids[1],
            "emergency_contact": "+1-555-9106",
            "remarks": None
        },
        {
            "student_id": student_ids[6],
            "name": "Ava Taylor",
            "roll_number": "G6B-002",
            "phone": "+1-555-4007",
            "photo": None,
            "class_name": "Grade 6",
            "section": "B",
            "parent_id": parent_ids[6],
            "teacher_id": teacher2_id,
            "bus_id": bus3_id,
            "stop_id": route3_stop_ids[2],
            "emergency_contact": "+1-555-9107",
            "remarks": "Basketball team captain"
        },
        {
            "student_id": student_ids[7],
            "name": "Mason Garcia",
            "roll_number": "G6B-003",
            "phone": "+1-555-4008",
            "photo": None,
            "class_name": "Grade 6",
            "section": "B",
            "parent_id": parent_ids[7],
            "teacher_id": teacher2_id,
            "bus_id": bus4_id,
            "stop_id": route4_stop_ids[0],
            "emergency_contact": "+1-555-9108",
            "remarks": None
        },
        {
            "student_id": student_ids[8],
            "name": "Isabella Rodriguez",
            "roll_number": "G6B-004",
            "phone": "+1-555-4009",
            "photo": None,
            "class_name": "Grade 6",
            "section": "B",
            "parent_id": parent_ids[8],
            "teacher_id": teacher2_id,
            "bus_id": bus4_id,
            "stop_id": route4_stop_ids[1],
            "emergency_contact": "+1-555-9109",
            "remarks": "Debate club member"
        },
        {
            "student_id": student_ids[9],
            "name": "Lucas Lee",
            "roll_number": "G6B-005",
            "phone": "+1-555-4010",
            "photo": None,
            "class_name": "Grade 6",
            "section": "B",
            "parent_id": parent_ids[9],
            "teacher_id": teacher2_id,
            "bus_id": bus4_id,
            "stop_id": route4_stop_ids[2],
            "emergency_contact": "+1-555-9110",
            "remarks": None
        },
        
        # Grade 4 - Section A (Teacher 3)
        {
            "student_id": student_ids[10],
            "name": "Mia Harris",
            "roll_number": "G4A-001",
            "phone": "+1-555-4011",
            "photo": None,
            "class_name": "Grade 4",
            "section": "A",
            "parent_id": parent_ids[10],
            "teacher_id": teacher3_id,
            "bus_id": bus1_id,
            "stop_id": route1_stop_ids[0],
            "emergency_contact": "+1-555-9111",
            "remarks": None
        },
        {
            "student_id": student_ids[11],
            "name": "Benjamin Clark",
            "roll_number": "G4A-002",
            "phone": "+1-555-4012",
            "photo": None,
            "class_name": "Grade 4",
            "section": "A",
            "parent_id": parent_ids[11],
            "teacher_id": teacher3_id,
            "bus_id": bus1_id,
            "stop_id": route1_stop_ids[3],
            "emergency_contact": "+1-555-9112",
            "remarks": "Art club member"
        },
        {
            "student_id": student_ids[12],
            "name": "Charlotte Lewis",
            "roll_number": "G4A-003",
            "phone": "+1-555-4013",
            "photo": None,
            "class_name": "Grade 4",
            "section": "A",
            "parent_id": parent_ids[12],
            "teacher_id": teacher3_id,
            "bus_id": bus2_id,
            "stop_id": route2_stop_ids[2],
            "emergency_contact": "+1-555-9113",
            "remarks": None
        },
        {
            "student_id": student_ids[13],
            "name": "James Walker",
            "roll_number": "G4A-004",
            "phone": "+1-555-4014",
            "photo": None,
            "class_name": "Grade 4",
            "section": "A",
            "parent_id": parent_ids[13],
            "teacher_id": teacher3_id,
            "bus_id": bus2_id,
            "stop_id": route2_stop_ids[3],
            "emergency_contact": "+1-555-9114",
            "remarks": "Soccer team member"
        },
        {
            "student_id": student_ids[14],
            "name": "Mia Hall",
            "roll_number": "G4A-005",
            "phone": "+1-555-4015",
            "photo": None,
            "class_name": "Grade 4",
            "section": "A",
            "parent_id": parent_ids[8],  # Matthew Lee's first child
            "teacher_id": teacher3_id,
            "bus_id": bus4_id,
            "stop_id": route4_stop_ids[3],
            "emergency_contact": "+1-555-9115",
            "remarks": "Library monitor"
        },
        
        # Additional students to reach 20 total (demonstrating Many:1 parent relationship)
        {
            "student_id": student_ids[15],
            "name": "Alexander Lee",
            "roll_number": "G5A-006",
            "phone": "+1-555-4016",
            "photo": None,
            "class_name": "Grade 5",
            "section": "A",
            "parent_id": parent_ids[8],  # Matthew Lee's second child
            "teacher_id": teacher1_id,
            "bus_id": bus1_id,
            "stop_id": route1_stop_ids[0],
            "emergency_contact": "+1-555-9116",
            "remarks": "Science club member"
        },
        {
            "student_id": student_ids[16],
            "name": "Harper Harris",
            "roll_number": "G6B-006",
            "phone": "+1-555-4017",
            "photo": None,
            "class_name": "Grade 6",
            "section": "B",
            "parent_id": parent_ids[9],  # Jessica Harris's child
            "teacher_id": teacher2_id,
            "bus_id": bus3_id,
            "stop_id": route3_stop_ids[3],
            "emergency_contact": "+1-555-9117",
            "remarks": "Drama club member"
        },
        {
            "student_id": student_ids[17],
            "name": "Evelyn Clark",
            "roll_number": "G4A-006",
            "phone": "+1-555-4018",
            "photo": None,
            "class_name": "Grade 4",
            "section": "A",
            "parent_id": parent_ids[10],  # Daniel Clark's first child
            "teacher_id": teacher3_id,
            "bus_id": bus2_id,
            "stop_id": route2_stop_ids[1],
            "emergency_contact": "+1-555-9118",
            "remarks": "Math team member"
        },
        {
            "student_id": student_ids[18],
            "name": "Henry Clark",
            "roll_number": "G5A-007",
            "phone": "+1-555-4019",
            "photo": None,
            "class_name": "Grade 5",
            "section": "A",
            "parent_id": parent_ids[10],  # Daniel Clark's second child
            "teacher_id": teacher1_id,
            "bus_id": bus1_id,
            "stop_id": route1_stop_ids[2],
            "emergency_contact": "+1-555-9119",
            "remarks": "Chess club captain"
        },
        {
            "student_id": student_ids[19],
            "name": "Sebastian Lewis",
            "roll_number": "G6B-007",
            "phone": "+1-555-4020",
            "photo": None,
            "class_name": "Grade 6",
            "section": "B",
            "parent_id": parent_ids[11],  # Lisa Lewis's child
            "teacher_id": teacher2_id,
            "bus_id": bus4_id,
            "stop_id": route4_stop_ids[4],
            "emergency_contact": "+1-555-9120",
            "remarks": "Student council member"
        }
    ]
    
    await db.students.insert_many(students_data)
    print(f"✅ Created {len(students_data)} students with roll numbers and proper linking")
    
    print("\n" + "=" * 60)
    print("📅 CREATING ATTENDANCE RECORDS")
    print("=" * 60)
    
    # Create sample attendance records for the past week
    attendance_records = []
    today = datetime.now(timezone.utc)
    
    for day_offset in range(7):
        date = (today - timedelta(days=day_offset)).strftime("%Y-%m-%d")
        
        for student_id in student_ids:
            # AM attendance (90% present)
            if random.random() > 0.1:
                attendance_records.append({
                    "attendance_id": str(uuid.uuid4()),
                    "student_id": student_id,
                    "date": date,
                    "trip": "AM",
                    "status": random.choice(["green", "green", "green", "yellow"]),
                    "confidence": round(random.uniform(0.85, 0.98), 2),
                    "last_update": (today - timedelta(days=day_offset)).isoformat()
                })
            
            # PM attendance (85% present)
            if random.random() > 0.15:
                attendance_records.append({
                    "attendance_id": str(uuid.uuid4()),
                    "student_id": student_id,
                    "date": date,
                    "trip": "PM",
                    "status": random.choice(["green", "green", "yellow"]),
                    "confidence": round(random.uniform(0.82, 0.96), 2),
                    "last_update": (today - timedelta(days=day_offset)).isoformat()
                })
    
    await db.attendance.insert_many(attendance_records)
    print(f"✅ Created {len(attendance_records)} attendance records for past 7 days")
    
    print("\n" + "=" * 60)
    print("🚌 CREATING BUS LOCATIONS")
    print("=" * 60)
    
    # Create initial bus locations
    bus_locations = [
        {
            "bus_id": bus1_id,
            "lat": route1_stops_data[1]["lat"],
            "lon": route1_stops_data[1]["lon"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "bus_id": bus2_id,
            "lat": route2_stops_data[0]["lat"],
            "lon": route2_stops_data[0]["lon"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "bus_id": bus3_id,
            "lat": route3_stops_data[1]["lat"],
            "lon": route3_stops_data[1]["lon"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "bus_id": bus4_id,
            "lat": route4_stops_data[2]["lat"],
            "lon": route4_stops_data[2]["lon"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    for loc in bus_locations:
        await db.bus_locations.insert_one(loc)
    print(f"✅ Created {len(bus_locations)} initial bus location records")
    
    print("\n" + "=" * 60)
    print("📅 CREATING HOLIDAYS")
    print("=" * 60)
    
    # Create holidays
    current_year = datetime.now().year
    holidays = [
        {
            "holiday_id": str(uuid.uuid4()),
            "date": f"{current_year}-01-01",
            "name": "New Year's Day"
        },
        {
            "holiday_id": str(uuid.uuid4()),
            "date": f"{current_year}-07-04",
            "name": "Independence Day"
        },
        {
            "holiday_id": str(uuid.uuid4()),
            "date": f"{current_year}-11-28",
            "name": "Thanksgiving Day"
        },
        {
            "holiday_id": str(uuid.uuid4()),
            "date": f"{current_year}-12-25",
            "name": "Christmas Day"
        },
        {
            "holiday_id": str(uuid.uuid4()),
            "date": f"{current_year+1}-01-01",
            "name": "New Year's Day"
        }
    ]
    
    await db.holidays.insert_many(holidays)
    print(f"✅ Created {len(holidays)} holiday records")
    
    print("\n" + "=" * 60)
    print("🔔 CREATING SAMPLE NOTIFICATIONS")
    print("=" * 60)
    
    # Create some sample notifications
    notifications = [
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": parent_ids[0],
            "message": "Identity verification failed for Emma Johnson during morning bus boarding",
            "event_type": "identity_mismatch",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "read": False
        },
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": parent_ids[2],
            "message": "Sophia Brown's bus route has been updated",
            "event_type": "route_update",
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "read": False
        }
    ]
    
    await db.notifications.insert_many(notifications)
    print(f"✅ Created {len(notifications)} sample notifications")
    
    print("\n" + "=" * 60)
    print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    print("\n📊 SUMMARY:")
    print("   • Admins: 2")
    print("   • Teachers: 3")
    print("   • Parents: 12")
    print("   • Students: 20")
    print("   • Buses: 4")
    print("   • Routes: 4")
    print(f"   • Stops: {len(all_stops)}")
    print(f"   • Attendance Records: {len(attendance_records)}")
    print(f"   • Holidays: {len(holidays)}")
    print(f"   • Notifications: {len(notifications)}")
    
    print("\n" + TEST_CREDENTIALS)
    
    print("\n🔗 DATA LINKING:")
    print("   • Grade 5-A: 7 students → Teacher: Mary Johnson (teacher@school.com)")
    print("   • Grade 6-B: 7 students → Teacher: Robert Smith (teacher2@school.com)")
    print("   • Grade 4-A: 6 students → Teacher: Sarah Wilson (teacher3@school.com)")
    print("   • 12 parents managing 20 students (Many:1 relationship)")
    print("   • Some parents have multiple children (2-3 kids each)")
    print("   • Each student linked to: Parent, Teacher, Bus, and Bus Stop")
    print("   • Each parent has access to their children's dashboards")
    print("   • Each teacher can view their assigned students")
    
    print("\n🚀 NEXT STEPS:")
    print("   1. Start the application: sudo supervisorctl restart all")
    print("   2. Login with any of the demo credentials above")
    print("   3. Explore dashboards based on your role")
    print("   4. Test features: attendance tracking, bus locations, notifications")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_data())
