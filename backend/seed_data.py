"""
Comprehensive Seed Data Generator for Bus Tracker System
Creates realistic demo data for all roles and entities with proper linking
NOW WITH AUTO-RESTORE: Automatically restores from latest backup if available
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
import json
from typing import Optional, Dict, Any

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Backup directory
BACKUP_DIR = ROOT_DIR / 'backups'

# Collections to restore from backup (excluding dynamic data)
RESTORABLE_COLLECTIONS = [
    'users',
    'students',
    'buses',
    'routes',
    'stops',
    'holidays',
    'device_keys'
]

# Test credentials for easy login
TEST_CREDENTIALS = ""


def get_latest_backup() -> Optional[Path]:
    """Find the most recent backup file"""
    if not BACKUP_DIR.exists():
        return None
    
    backup_files = list(BACKUP_DIR.glob('seed_backup_*.json'))
    if not backup_files:
        return None
    
    # Sort by filename (timestamp) in descending order
    backup_files.sort(reverse=True)
    return backup_files[0]


async def restore_from_backup(backup_path: Path) -> bool:
    """
    Restore database from backup file
    Excludes dynamic data (attendance, logs, notifications)
    Returns True if successful, False otherwise
    """
    print("\n" + "=" * 60)
    print(f"📦 RESTORING FROM BACKUP: {backup_path.name}")
    print("=" * 60)
    
    try:
        # Load backup data
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        backup_timestamp = backup_data.get('timestamp', 'Unknown')
        print(f"   📅 Backup created: {backup_timestamp}")
        
        collections_data = backup_data.get('collections', {})
        
        # Restore each collection
        print("\n📥 Restoring collections:")
        restored_count = 0
        
        for collection_name in RESTORABLE_COLLECTIONS:
            if collection_name not in collections_data:
                print(f"   ⚠️  {collection_name}: Not found in backup, skipping")
                continue
            
            documents = collections_data[collection_name]
            
            if not documents:
                print(f"   ℹ️  {collection_name}: Empty in backup, skipping")
                continue
            
            try:
                # Remove _id field from documents (let MongoDB generate new ones)
                clean_documents = []
                for doc in documents:
                    clean_doc = {k: v for k, v in doc.items() if k != '_id'}
                    clean_documents.append(clean_doc)
                
                # Insert documents
                if clean_documents:
                    await db[collection_name].insert_many(clean_documents)
                    print(f"   ✅ {collection_name}: {len(clean_documents)} document(s) restored")
                    restored_count += 1
            except Exception as e:
                print(f"   ❌ {collection_name}: Restore failed - {e}")
                return False
        
        print(f"\n✅ Successfully restored {restored_count} collection(s) from backup")
        return True
        
    except json.JSONDecodeError as e:
        print(f"\n❌ Backup file is corrupted or invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Restore failed: {e}")
        return False


def get_latest_attendance_backup() -> Optional[Path]:
    """Find the most recent attendance backup file"""
    attendance_backup_dir = BACKUP_DIR / 'attendance'
    if not attendance_backup_dir.exists():
        return None
    
    backup_files = list(attendance_backup_dir.glob('attendance_backup_*.json'))
    if not backup_files:
        return None
    
    # Sort by filename (timestamp) in descending order
    backup_files.sort(reverse=True)
    return backup_files[0]


async def restore_attendance_from_backup(backup_path: Path) -> bool:
    """
    Restore attendance data from attendance-specific backup file
    Includes: attendance, events (scan events), and photo references
    Returns True if successful, False otherwise
    """
    print("\n" + "=" * 60)
    print(f"📸 RESTORING ATTENDANCE FROM BACKUP: {backup_path.name}")
    print("=" * 60)
    
    try:
        # Load backup data
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        backup_timestamp = backup_data.get('timestamp', 'Unknown')
        backup_type = backup_data.get('backup_type', 'Unknown')
        print(f"   📅 Backup created: {backup_timestamp}")
        print(f"   📋 Backup type: {backup_type}")
        
        collections_data = backup_data.get('collections', {})
        photo_references = backup_data.get('photo_references', {})
        
        # Restore attendance collections
        print("\n📥 Restoring attendance collections:")
        restored_count = 0
        
        attendance_collections = ['attendance', 'events']
        for collection_name in attendance_collections:
            if collection_name not in collections_data:
                print(f"   ⚠️  {collection_name}: Not found in backup, skipping")
                continue
            
            documents = collections_data[collection_name]
            
            if not documents:
                print(f"   ℹ️  {collection_name}: Empty in backup, skipping")
                continue
            
            try:
                # Clear existing data first
                await db[collection_name].delete_many({})
                
                # Remove _id field from documents (let MongoDB generate new ones)
                clean_documents = []
                for doc in documents:
                    clean_doc = {k: v for k, v in doc.items() if k != '_id'}
                    clean_documents.append(clean_doc)
                
                # Insert documents
                if clean_documents:
                    await db[collection_name].insert_many(clean_documents)
                    print(f"   ✅ {collection_name}: {len(clean_documents)} document(s) restored")
                    restored_count += 1
            except Exception as e:
                print(f"   ❌ {collection_name}: Restore failed - {e}")
                return False
        
        # Log photo references info
        print("\n📸 Attendance photo references:")
        scan_photos = photo_references.get('scan_photos', [])
        attendance_folders = photo_references.get('student_attendance_folders', [])
        print(f"   ℹ️  Scan photos: {len(scan_photos)} reference(s)")
        print(f"   ℹ️  Attendance folders: {len(attendance_folders)} folder(s)")
        
        print(f"\n✅ Successfully restored {restored_count} attendance collection(s) from backup")
        return True
        
    except json.JSONDecodeError as e:
        print(f"\n❌ Attendance backup file is corrupted or invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Attendance restore failed: {e}")
        return False

async def create_sample_notifs():
    # Create sample notifications for admin even when restoring from backup
    print("\n" + "=" * 60)
    print("🔔 CREATING SAMPLE NOTIFICATIONS FOR ADMIN")
    print("=" * 60)
    
    admin_user = await db.users.find_one({"role": "admin"})
    if admin_user:
        now = datetime.now(timezone.utc)
        admin_notifications = [
            {
                "notification_id": str(uuid.uuid4()),
                "user_id": admin_user['user_id'],
                "title": "System Update",
                "message": "Bus tracking system has been updated with new features",
                "type": "update",
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "read": False
            },
            {
                "notification_id": str(uuid.uuid4()),
                "user_id": admin_user['user_id'],
                "title": "New Device Registered",
                "message": "A new Raspberry Pi device was registered for BUS-001",
                "type": "update",
                "timestamp": (now - timedelta(hours=5)).isoformat(),
                "read": False
            },
            {
                "notification_id": str(uuid.uuid4()),
                "user_id": admin_user['user_id'],
                "title": "Attendance Summary",
                "message": "Daily attendance report: 18/20 students marked present",
                "type": "update",
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "read": True
            }
        ]
        await db.notifications.insert_many(admin_notifications)
        print(f"✅ Created {len(admin_notifications)} notifications for admin")
        print("\n⚠️  Note: Notifications created fresh (not from backup)")

    
async def create_stops_and_routes():
    """Create stops and routes. Returns dict with ids and stop data used by other functions."""
    print("\n" + "=" * 60)
    print("📍 CREATING STOPS AND ROUTES")
    print("=" * 60)

    # stop / route seed data (same as previous inline data)
    route1_stops_data = [
        {"name": "Main Gate North", "lat": 37.7749, "lon": -122.4194, "morning_time": "07:00", "evening_time": "15:00"},
        {"name": "Park Avenue", "lat": 37.7849, "lon": -122.4094, "morning_time": "07:10", "evening_time": "15:10"},
        {"name": "Market Street", "lat": 37.7949, "lon": -122.3994, "morning_time": "07:20", "evening_time": "15:20"},
        {"name": "Oak Boulevard", "lat": 37.8019, "lon": -122.3944, "morning_time": "07:30", "evening_time": "15:30"},
        {"name": "School North Entrance", "lat": 37.8049, "lon": -122.3894, "morning_time": "07:40", "evening_time": "15:40"}
    ]
    route2_stops_data = [
        {"name": "South Gate", "lat": 37.7649, "lon": -122.4294, "morning_time": "06:45", "evening_time": "15:15"},
        {"name": "Elm Street", "lat": 37.7699, "lon": -122.4244, "morning_time": "06:55", "evening_time": "15:25"},
        {"name": "Maple Avenue", "lat": 37.7749, "lon": -122.4194, "morning_time": "07:05", "evening_time": "15:35"},
        {"name": "Pine Road", "lat": 37.7799, "lon": -122.4144, "morning_time": "07:15", "evening_time": "15:45"}
    ]
    route3_stops_data = [
        {"name": "East Gate", "lat": 37.7849, "lon": -122.3794, "morning_time": "07:15", "evening_time": "15:30"},
        {"name": "Cedar Lane", "lat": 37.7899, "lon": -122.3844, "morning_time": "07:25", "evening_time": "15:40"},
        {"name": "Birch Street", "lat": 37.7949, "lon": -122.3894, "morning_time": "07:35", "evening_time": "15:50"},
        {"name": "Walnut Drive", "lat": 37.7999, "lon": -122.3944, "morning_time": "07:45", "evening_time": "16:00"},
        {"name": "School East Entrance", "lat": 37.8049, "lon": -122.3894, "morning_time": "07:55", "evening_time": "16:10"}
    ]
    route4_stops_data = [
        {"name": "West Gate", "lat": 37.7749, "lon": -122.4394, "morning_time": "06:30", "evening_time": "15:45"},
        {"name": "Sunset Boulevard", "lat": 37.7799, "lon": -122.4344, "morning_time": "06:40", "evening_time": "15:55"},
        {"name": "Ocean Avenue", "lat": 37.7849, "lon": -122.4294, "morning_time": "06:50", "evening_time": "16:05"},
        {"name": "Beach Street", "lat": 37.7899, "lon": -122.4244, "morning_time": "07:00", "evening_time": "16:15"},
        {"name": "Harbor Road", "lat": 37.7949, "lon": -122.4194, "morning_time": "07:10", "evening_time": "16:25"},
        {"name": "School West Entrance", "lat": 37.8049, "lon": -122.3894, "morning_time": "07:20", "evening_time": "16:35"}
    ]

    all_stops = []
    route_stop_ids = {"route1": [], "route2": [], "route3": [], "route4": []}

    for idx, s in enumerate(route1_stops_data):
        sid = str(uuid.uuid4()); route_stop_ids["route1"].append(sid)
        all_stops.append({
            "stop_id": sid, "stop_name": s["name"], "lat": s["lat"], "lon": s["lon"],
            "order_index": idx, "morning_expected_time": s["morning_time"], "evening_expected_time": s["evening_time"]
        })
    for idx, s in enumerate(route2_stops_data):
        sid = str(uuid.uuid4()); route_stop_ids["route2"].append(sid)
        all_stops.append({
            "stop_id": sid, "stop_name": s["name"], "lat": s["lat"], "lon": s["lon"],
            "order_index": idx, "morning_expected_time": s["morning_time"], "evening_expected_time": s["evening_time"]
        })
    for idx, s in enumerate(route3_stops_data):
        sid = str(uuid.uuid4()); route_stop_ids["route3"].append(sid)
        all_stops.append({
            "stop_id": sid, "stop_name": s["name"], "lat": s["lat"], "lon": s["lon"],
            "order_index": idx, "morning_expected_time": s["morning_time"], "evening_expected_time": s["evening_time"]
        })
    for idx, s in enumerate(route4_stops_data):
        sid = str(uuid.uuid4()); route_stop_ids["route4"].append(sid)
        all_stops.append({
            "stop_id": sid, "stop_name": s["name"], "lat": s["lat"], "lon": s["lon"],
            "order_index": idx, "morning_expected_time": s["morning_time"], "evening_expected_time": s["evening_time"]
        })

    await db.stops.insert_many(all_stops)
    print(f"✅ Created {len(all_stops)} stops across 4 routes")

    # Create routes and return ids
    route1_id = str(uuid.uuid4()); route2_id = str(uuid.uuid4())
    route3_id = str(uuid.uuid4()); route4_id = str(uuid.uuid4())

    routes = [
        {"route_id": route1_id, "route_name": "Route A - North District", "stop_ids": route_stop_ids["route1"],
         "map_path": [{"lat": s["lat"], "lon": s["lon"]} for s in route1_stops_data], "remarks": "Morning route covering north residential area"},
        {"route_id": route2_id, "route_name": "Route B - South District", "stop_ids": route_stop_ids["route2"],
         "map_path": [{"lat": s["lat"], "lon": s["lon"]} for s in route2_stops_data], "remarks": "Morning route covering south residential area"},
        {"route_id": route3_id, "route_name": "Route C - East District", "stop_ids": route_stop_ids["route3"],
         "map_path": [{"lat": s["lat"], "lon": s["lon"]} for s in route3_stops_data], "remarks": "Afternoon route covering east business district"},
        {"route_id": route4_id, "route_name": "Route D - West District", "stop_ids": route_stop_ids["route4"],
         "map_path": [{"lat": s["lat"], "lon": s["lon"]} for s in route4_stops_data], "remarks": "Afternoon route covering west coastal area"}
    ]

    await db.routes.insert_many(routes)
    print(f"✅ Created {len(routes)} routes")

    return {
        "route_ids": [route1_id, route2_id, route3_id, route4_id],
        "route_stop_ids": route_stop_ids,
        "routes_raw": (route1_stops_data, route2_stops_data, route3_stops_data, route4_stops_data)
    }


async def create_buses(route_ids):
    print("\n" + "=" * 60)
    print("🚌 CREATING BUSES")
    print("=" * 60)
    buses = [
        {"bus_number": "BUS-001", "driver_name": "Robert Johnson", "driver_phone": "+1-555-0101", "route_id": route_ids[0], "capacity": 5, "remarks": "Test bus - Small capacity (5 students)"},
        {"bus_number": "BUS-002", "driver_name": "Sarah Martinez", "driver_phone": "+1-555-0102", "route_id": route_ids[1], "capacity": 3, "remarks": "Test bus - Very small capacity (3 students)"},
        {"bus_number": "BUS-003", "driver_name": "Michael Chen", "driver_phone": "+1-555-0103", "route_id": route_ids[2], "capacity": 45, "remarks": "Large capacity bus for busy route"},
        {"bus_number": "BUS-004", "driver_name": "Lisa Anderson", "driver_phone": "+1-555-0104", "route_id": route_ids[3], "capacity": 38, "remarks": "Standard capacity coastal route"}
    ]
    await db.buses.insert_many(buses)
    print(f"✅ Created {len(buses)} buses with drivers")
    return [b["bus_number"] for b in buses]


async def create_users_and_ids():
    print("\n" + "=" * 60)
    print("👥 CREATING USERS (ADMINS, TEACHERS, PARENTS)")
    print("=" * 60)
    password_hash = bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    admin1_id = str(uuid.uuid4()); admin2_id = str(uuid.uuid4())
    teacher1_id = str(uuid.uuid4()); teacher2_id = str(uuid.uuid4()); teacher3_id = str(uuid.uuid4())
    student_ids = [str(uuid.uuid4()) for _ in range(20)]
    parent_ids = [str(uuid.uuid4()) for _ in range(12)]

    users = [
        {"user_id": admin1_id, "email": "admin@school.com", "password_hash": password_hash, "role": "admin", "name": "James Anderson", "phone": "+1-555-9001", "photo": f"/api/photos/admins/{admin1_id}.jpg", "address": "School Administration Office, Main Building", "assigned_class": None, "assigned_section": None, "student_ids": [], "is_elevated_admin": True},
        {"user_id": admin2_id, "email": "admin2@school.com", "password_hash": password_hash, "role": "admin", "name": "Patricia Williams", "phone": "+1-555-9002", "photo": f"/api/photos/admins/{admin2_id}.jpg", "address": "School Administration Office, East Wing", "assigned_class": None, "assigned_section": None, "student_ids": [], "is_elevated_admin": False},
        {"user_id": teacher1_id, "email": "teacher@school.com", "password_hash": password_hash, "role": "teacher", "name": "Mary Johnson", "phone": "+1-555-2001", "photo": f"/api/photos/teachers/{teacher1_id}.jpg", "address": "321 Teacher Lane, San Francisco, CA", "assigned_class": "5", "assigned_section": "A", "student_ids": [], "is_elevated_admin": False},
        {"user_id": teacher2_id, "email": "teacher2@school.com", "password_hash": password_hash, "role": "teacher", "name": "Robert Smith", "phone": "+1-555-2002", "photo": f"/api/photos/teachers/{teacher2_id}.jpg", "address": "456 Educator Drive, San Francisco, CA", "assigned_class": "6", "assigned_section": "B", "student_ids": [], "is_elevated_admin": False},
        {"user_id": teacher3_id, "email": "teacher3@school.com", "password_hash": password_hash, "role": "teacher", "name": "Sarah Wilson", "phone": "+1-555-2003", "photo": f"/api/photos/teachers/{teacher3_id}.jpg", "address": "789 School Street, San Francisco, CA", "assigned_class": "4", "assigned_section": "A", "student_ids": [], "is_elevated_admin": False},
    ]
    # parents creation (keep concise)
    for i, pid in enumerate(parent_ids):
        users.append({"user_id": pid, "email": f"parent{i+1}@school.com", "password_hash": password_hash, "role": "parent", "name": f"Parent {i+1}", "phone": f"+1-555-30{10+i}", "photo": f"/api/photos/parents/{pid}.jpg", "address": "Unknown", "assigned_class": None, "assigned_section": None, "student_ids": [], "is_elevated_admin": False})

    await db.users.insert_many(users)
    print(f"✅ Created {len(users)} users (2 admins, 3 teachers, 12 parents)")
    return {"admin_ids": [admin1_id, admin2_id], "teacher_ids": [teacher1_id, teacher2_id, teacher3_id], "parent_ids": parent_ids, "student_ids": student_ids}


async def create_students_and_linking(ids_map, route_stop_ids):
    print("\n" + "=" * 60)
    print("👦 CREATING STUDENTS")
    print("=" * 60)
    student_ids = ids_map["student_ids"]
    teacher_ids = ids_map["teacher_ids"]
    parent_ids = ids_map["parent_ids"]

    # generate simplified student objects mapped to parents/teachers/buses/stops
    students_data = []
    for i, sid in enumerate(student_ids):
        students_data.append({
            "student_id": sid,
            "name": f"Student {i+1}",
            "roll_number": f"RN-{i+1:03}",
            "tag_id": f"RFID-{1000+i}",
            "phone": f"+1-555-4{100+i}",
            "photo": f"/api/photos/students/{sid}/profile.jpg",
            "class_name": str(4 + (i % 3)),
            "section": "A",
            "parent_id": parent_ids[i % len(parent_ids)],
            "teacher_id": teacher_ids[i % len(teacher_ids)],
            "bus_number": f"BUS-00{(i % 4) + 1}",
            "stop_id": route_stop_ids["route1"][min(1, len(route_stop_ids["route1"]) - 1)],
            "emergency_contact": f"+1-555-91{10+i}",
            "remarks": None
        })
    await db.students.insert_many(students_data)
    print(f"✅ Created {len(students_data)} students with roll numbers and proper linking")
    return student_ids


async def create_attendance_records(student_ids):
    print("\n" + "=" * 60)
    print("📅 CREATING ATTENDANCE RECORDS")
    print("=" * 60)
    attendance_records = []
    today = datetime.now(timezone.utc)
    for day_offset in range(7):
        date = (today - timedelta(days=day_offset)).strftime("%Y-%m-%d")
        for student_id in student_ids:
            if random.random() > 0.1:
                attendance_records.append({"attendance_id": str(uuid.uuid4()), "student_id": student_id, "date": date, "trip": "AM", "status": random.choice(["green", "green", "green", "yellow"]), "confidence": round(random.uniform(0.85, 0.98), 2), "last_update": (today - timedelta(days=day_offset)).isoformat()})
            if random.random() > 0.15:
                attendance_records.append({"attendance_id": str(uuid.uuid4()), "student_id": student_id, "date": date, "trip": "PM", "status": random.choice(["green", "green", "yellow"]), "confidence": round(random.uniform(0.82, 0.96), 2), "last_update": (today - timedelta(days=day_offset)).isoformat()})
    await db.attendance.insert_many(attendance_records)
    print(f"✅ Created {len(attendance_records)} attendance records for past 7 days")


async def create_bus_locations_and_holidays(route_stop_samples):
    print("\n" + "=" * 60)
    print("🚌 CREATING BUS LOCATIONS")
    print("=" * 60)
    bus_locations = [
        {"bus_number": "BUS-001", "lat": route_stop_samples[0][1]["lat"], "lon": route_stop_samples[0][1]["lon"], "timestamp": datetime.now(timezone.utc).isoformat()},
        {"bus_number": "BUS-002", "lat": route_stop_samples[1][0]["lat"], "lon": route_stop_samples[1][0]["lon"], "timestamp": datetime.now(timezone.utc).isoformat()},
        {"bus_number": "BUS-003", "lat": route_stop_samples[2][1]["lat"], "lon": route_stop_samples[2][1]["lon"], "timestamp": datetime.now(timezone.utc).isoformat()},
        {"bus_number": "BUS-004", "lat": route_stop_samples[3][2]["lat"], "lon": route_stop_samples[3][2]["lon"], "timestamp": datetime.now(timezone.utc).isoformat()}
    ]
    for loc in bus_locations:
        await db.bus_locations.insert_one(loc)
    print(f"✅ Created {len(bus_locations)} initial bus location records")

    print("\n" + "=" * 60)
    print("📅 CREATING HOLIDAYS")
    print("=" * 60)
    current_year = datetime.now().year
    holidays = [
        {"holiday_id": str(uuid.uuid4()), "date": f"{current_year}-01-01", "name": "New Year's Day"},
        {"holiday_id": str(uuid.uuid4()), "date": f"{current_year}-07-04", "name": "Independence Day"},
        {"holiday_id": str(uuid.uuid4()), "date": f"{current_year}-11-28", "name": "Thanksgiving Day"},
        {"holiday_id": str(uuid.uuid4()), "date": f"{current_year}-12-25", "name": "Christmas Day"},
        {"holiday_id": str(uuid.uuid4()), "date": f"{current_year+1}-01-01", "name": "New Year's Day"}
    ]
    await db.holidays.insert_many(holidays)
    print(f"✅ Created {len(holidays)} holiday records")


async def create_sample_notifications_for_demo(ids_map):
    # Reuse existing create_sample_notifs logic but ensure it runs when called
    await create_sample_notifs()


async def seed_data():
    print("=" * 60)
    print("🌱 STARTING COMPREHENSIVE DATABASE SEEDING")
    print("=" * 60)

    latest_backup = get_latest_backup()
    use_backup = False

    if latest_backup:
        print(f"\n🔍 Latest backup found: {latest_backup.name}")
        print("   Attempting to restore from backup...")
        use_backup = True
    else:
        print("\nℹ️  No backup found, will use default seed data")

    # Clear existing data
    collections = ['users', 'students', 'attendance', 'events', 'bus_locations', 'notifications', 'holidays', 'buses', 'routes', 'stops', 'email_logs']
    print("\n🗑️  Clearing existing data:")
    for collection in collections:
        count = await db[collection].count_documents({})
        await db[collection].delete_many({})
        print(f"   ✅ Cleared {count} records from {collection}")

    if use_backup:
        restore_success = await restore_from_backup(latest_backup)
        if restore_success:
            # Try attendance restore and still ensure notifications exist
            latest_attendance_backup = get_latest_attendance_backup()
            if latest_attendance_backup:
                attendance_restore_success = await restore_attendance_from_backup(latest_attendance_backup)
                if not attendance_restore_success:
                    print("\n⚠️  Attendance backup restore failed, attendance data will be empty")
            else:
                print("\nℹ️  No attendance backup found, attendance data will be empty")

            await create_sample_notifs()
            # Ensure admin notifications exist
            print("\n" + "=" * 60)
            print("✅ SEEDING COMPLETED (FROM BACKUP)")
            print("=" * 60)
            print(TEST_CREDENTIALS)
            client.close()
            return
        else:
            print("\n⚠️  Backup restore failed, falling back to default seed data...")

    # Proceed with default seeding using modular functions
    print("\n" + "=" * 60)
    print("📝 USING DEFAULT SEED DATA")
    print("=" * 60)

    # 1) stops & routes
    layout = await create_stops_and_routes()

    # 2) buses
    bus_numbers = await create_buses(layout["route_ids"])

    # 3) users
    ids_map = await create_users_and_ids()

    # 4) students (needs ids_map and route/stop ids)
    student_ids = await create_students_and_linking(ids_map, layout["route_stop_ids"])

    # 5) attendance
    await create_attendance_records(student_ids)

    # 6) bus locations + holidays
    await create_bus_locations_and_holidays(layout["routes_raw"])

    # 7) sample notifications
    try:
        await create_sample_notifications_for_demo(ids_map)
    except Exception as e:
        print(f"\n⚠️  create_sample_notifications_for_demo failed: {e}")

    print("\n✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\n📊 SUMMARY:")
    print(f"   • Admins: {len(ids_map['admin_ids'])}")
    print(f"   • Teachers: {len(ids_map['teacher_ids'])}")
    print(f"   • Parents: {len(ids_map['parent_ids'])}")
    print(f"   • Students: {len(ids_map['student_ids'])}")
    print(f"   • Buses: {len(bus_numbers)}")
    print(f"   • Routes: {len(layout['route_ids'])}")
    print(f"   • Stops: {sum(len(v) for v in layout['route_stop_ids'].values())}")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_data())
