#!/usr/bin/env python3
"""
Script to update photo fields in the database:
1. Rename photo_path to photo for students
2. Replace null values with actual photo paths
3. Update all users and students with correct photo paths
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = "school_management"

PHOTOS_DIR = Path("/app/backend/photos")

async def update_database():
    print("=" * 70)
    print("DATABASE PHOTO FIELD UPDATE")
    print("=" * 70)
    print()
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    stats = {
        'admins_updated': 0,
        'teachers_updated': 0,
        'parents_updated': 0,
        'students_updated': 0,
        'students_renamed': 0
    }
    
    # 1. Rename photo_path to photo for all students
    print("📝 Step 1: Renaming photo_path to photo for students...")
    students_with_photo_path = await db.students.count_documents({"photo_path": {"$exists": True}})
    if students_with_photo_path > 0:
        result = await db.students.update_many(
            {"photo_path": {"$exists": True}},
            [{"$set": {"photo": "$photo_path"}}, {"$unset": ["photo_path"]}]
        )
        stats['students_renamed'] = result.modified_count
        print(f"   ✓ Renamed photo_path to photo for {result.modified_count} students")
    else:
        print("   ℹ No students with photo_path field found")
    print()
    
    # 2. Update admins with null or missing photos
    print("📝 Step 2: Updating admins with missing photos...")
    admins = await db.users.find({"role": "admin"}).to_list(1000)
    for admin in admins:
        user_id = admin.get('user_id')
        photo = admin.get('photo')
        
        if not photo or photo == 'null':
            # Check if photo file exists
            photo_path = PHOTOS_DIR / 'admins' / f"{user_id}.jpg"
            if photo_path.exists():
                new_photo = f"/api/photos/admins/{user_id}.jpg"
                await db.users.update_one(
                    {"user_id": user_id},
                    {"$set": {"photo": new_photo}}
                )
                stats['admins_updated'] += 1
                print(f"   ✓ Updated admin {admin.get('name')}: {new_photo}")
    
    if stats['admins_updated'] == 0:
        print("   ℹ All admins already have photos")
    print()
    
    # 3. Update teachers with null or missing photos
    print("📝 Step 3: Updating teachers with missing photos...")
    teachers = await db.users.find({"role": "teacher"}).to_list(1000)
    for teacher in teachers:
        user_id = teacher.get('user_id')
        photo = teacher.get('photo')
        
        if not photo or photo == 'null':
            # Check if photo file exists
            photo_path = PHOTOS_DIR / 'teachers' / f"{user_id}.jpg"
            if photo_path.exists():
                new_photo = f"/api/photos/teachers/{user_id}.jpg"
                await db.users.update_one(
                    {"user_id": user_id},
                    {"$set": {"photo": new_photo}}
                )
                stats['teachers_updated'] += 1
                print(f"   ✓ Updated teacher {teacher.get('name')}: {new_photo}")
    
    if stats['teachers_updated'] == 0:
        print("   ℹ All teachers already have photos")
    print()
    
    # 4. Update parents with null or missing photos
    print("📝 Step 4: Updating parents with missing photos...")
    parents = await db.users.find({"role": "parent"}).to_list(1000)
    for parent in parents:
        user_id = parent.get('user_id')
        photo = parent.get('photo')
        
        if not photo or photo == 'null':
            # Check if photo file exists
            photo_path = PHOTOS_DIR / 'parents' / f"{user_id}.jpg"
            if photo_path.exists():
                new_photo = f"/api/photos/parents/{user_id}.jpg"
                await db.users.update_one(
                    {"user_id": user_id},
                    {"$set": {"photo": new_photo}}
                )
                stats['parents_updated'] += 1
                print(f"   ✓ Updated parent {parent.get('name')}: {new_photo}")
    
    if stats['parents_updated'] == 0:
        print("   ℹ All parents already have photos")
    print()
    
    # 5. Update students with null or missing photos
    print("📝 Step 5: Updating students with missing photos...")
    students = await db.students.find({}).to_list(1000)
    for student in students:
        student_id = student.get('student_id')
        photo = student.get('photo')
        
        if not photo or photo == 'null':
            # Check if photo file exists
            photo_path = PHOTOS_DIR / 'students' / student_id / 'profile.jpg'
            if photo_path.exists():
                new_photo = f"/api/photos/students/{student_id}/profile.jpg"
                await db.students.update_one(
                    {"student_id": student_id},
                    {"$set": {"photo": new_photo}}
                )
                stats['students_updated'] += 1
                print(f"   ✓ Updated student {student.get('name')}: {new_photo}")
    
    if stats['students_updated'] == 0:
        print("   ℹ All students already have photos")
    print()
    
    # Print summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Students (photo_path → photo): {stats['students_renamed']}")
    print(f"  Admins updated:                {stats['admins_updated']}")
    print(f"  Teachers updated:              {stats['teachers_updated']}")
    print(f"  Parents updated:               {stats['parents_updated']}")
    print(f"  Students updated:              {stats['students_updated']}")
    print()
    print(f"  Total updates: {sum(stats.values())}")
    print("=" * 70)
    print()
    print("✅ Database update complete!")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(update_database())
