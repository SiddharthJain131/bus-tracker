"""
Regenerate Attendance Records with Correct Student IDs
This script deletes all existing attendance records and creates new ones
linked to the current students in the database.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone, timedelta
import random
import uuid

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]


async def regenerate_attendance():
    """
    Regenerate attendance records for all current students
    Creates records for the past 14 days with realistic distribution
    """
    print("=" * 60)
    print("🔄 REGENERATING ATTENDANCE RECORDS")
    print("=" * 60)
    
    # Get all current students
    students = await db.students.find({}, {'_id': 0, 'student_id': 1, 'name': 1}).to_list(None)
    student_ids = [s['student_id'] for s in students]
    
    print(f"\n📚 Found {len(student_ids)} students")
    for s in students[:5]:
        print(f"   • {s['name']}: {s['student_id']}")
    if len(students) > 5:
        print(f"   ... and {len(students) - 5} more")
    
    # Delete all existing attendance records
    deleted_count = await db.attendance.delete_many({})
    print(f"\n🗑️  Deleted {deleted_count.deleted_count} old attendance records")
    
    # Generate new attendance records
    print(f"\n✨ Generating new attendance records...")
    attendance_records = []
    today = datetime.now(timezone.utc)
    
    # Generate for past 14 days
    for day_offset in range(14):
        date = (today - timedelta(days=day_offset)).strftime("%Y-%m-%d")
        timestamp = (today - timedelta(days=day_offset)).isoformat()
        
        for student_id in student_ids:
            # AM attendance (90% present for recent days, lower for older days)
            presence_rate = 0.90 if day_offset < 7 else 0.75
            
            if random.random() < presence_rate:
                status = random.choice(["green", "green", "green", "yellow"])
                confidence = round(random.uniform(0.85, 0.98), 2)
                
                attendance_records.append({
                    "attendance_id": str(uuid.uuid4()),
                    "student_id": student_id,
                    "date": date,
                    "trip": "AM",
                    "status": status,
                    "confidence": confidence,
                    "last_update": timestamp,
                    "scan_photo": f"/api/photos/students/{student_id}/attendance/{date}_AM.jpg",
                    "scan_timestamp": timestamp
                })
            
            # PM attendance (85% present)
            presence_rate = 0.85 if day_offset < 7 else 0.70
            
            if random.random() < presence_rate:
                status = random.choice(["green", "green", "green", "yellow"])
                confidence = round(random.uniform(0.82, 0.96), 2)
                
                attendance_records.append({
                    "attendance_id": str(uuid.uuid4()),
                    "student_id": student_id,
                    "date": date,
                    "trip": "PM",
                    "status": status,
                    "confidence": confidence,
                    "last_update": timestamp,
                    "scan_photo": f"/api/photos/students/{student_id}/attendance/{date}_PM.jpg",
                    "scan_timestamp": timestamp
                })
    
    # Insert new records
    if attendance_records:
        await db.attendance.insert_many(attendance_records)
        print(f"✅ Created {len(attendance_records)} new attendance records")
    
    # Verify the new records
    print(f"\n🔍 VERIFICATION")
    print("=" * 60)
    
    # Count total records
    total = await db.attendance.count_documents({})
    print(f"Total attendance records: {total}")
    
    # Check linkage
    all_student_ids = await db.students.distinct('student_id')
    all_att_student_ids = await db.attendance.distinct('student_id')
    matched = len(set(all_student_ids) & set(all_att_student_ids))
    
    print(f"Students in DB: {len(all_student_ids)}")
    print(f"Unique students in attendance: {len(all_att_student_ids)}")
    print(f"✅ Matched students: {matched}")
    
    if matched == len(all_student_ids):
        print("\n✨ SUCCESS! All students now have attendance records")
    else:
        print(f"\n⚠️  Warning: {len(all_student_ids) - matched} students missing attendance")
    
    # Show date range
    pipeline = [
        {'$group': {'_id': '$date', 'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}}
    ]
    dates = []
    async for doc in db.attendance.aggregate(pipeline):
        dates.append(doc['_id'])
    
    if dates:
        print(f"\nDate range: {dates[0]} to {dates[-1]} ({len(dates)} days)")
    
    print("\n" + "=" * 60)
    print("✅ ATTENDANCE REGENERATION COMPLETED")
    print("=" * 60)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(regenerate_attendance())
