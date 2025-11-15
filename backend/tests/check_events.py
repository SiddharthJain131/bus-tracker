#!/usr/bin/env python3
"""
Check events in database directly
"""

import os
from pymongo import MongoClient
from datetime import datetime, timedelta

# Connect to MongoDB
mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/')
client = MongoClient(mongo_url)
db = client['bus_tracker']

print("="*70)
print("CHECKING DATABASE RECORDS")
print("="*70)
print()

# Check events collection
events = list(db['events'].find().sort('timestamp', -1).limit(10))
print(f"Recent events count: {len(events)}")

if events:
    print("\nLast 5 events:")
    for i, event in enumerate(events[:5], 1):
        timestamp = event.get('timestamp', 'N/A')
        student_id = event.get('student_id', 'N/A')
        tag_id = event.get('tag_id', 'N/A')
        verified = event.get('verified', 'N/A')
        print(f"\n  Event {i}:")
        print(f"    Student ID: {student_id}")
        print(f"    Tag ID: {tag_id}")
        print(f"    Verified: {verified}")
        print(f"    Timestamp: {timestamp}")

# Check attendance collection
today = datetime.now().strftime("%Y-%m-%d")
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

print(f"\n\nChecking attendance records:")
print(f"  Today: {today}")
print(f"  Yesterday: {yesterday}")

attendance_today = list(db['attendance'].find({"date": today}))
attendance_yesterday = list(db['attendance'].find({"date": yesterday}))

print(f"\n  Attendance records for today: {len(attendance_today)}")
if attendance_today:
    for record in attendance_today[:3]:
        print(f"    - Student: {record.get('student_id')}, AM: {record.get('am_status')}, PM: {record.get('pm_status')}")

print(f"\n  Attendance records for yesterday: {len(attendance_yesterday)}")
if attendance_yesterday:
    for record in attendance_yesterday[:3]:
        print(f"    - Student: {record.get('student_id')}, AM: {record.get('am_status')}, PM: {record.get('pm_status')}")

# Check our specific student
test_student_id = "770f57ab-da26-4830-9615-a22451c61808"
print(f"\n\nChecking specific test student: {test_student_id}")

student_events = list(db['events'].find({"student_id": test_student_id}).sort('timestamp', -1).limit(5))
print(f"  Events for this student: {len(student_events)}")
for event in student_events:
    print(f"    - Tag: {event.get('tag_id')}, Verified: {event.get('verified')}, Time: {event.get('timestamp')}")

student_attendance = list(db['attendance'].find({"student_id": test_student_id}).sort('date', -1).limit(5))
print(f"  Attendance records for this student: {len(student_attendance)}")
for record in student_attendance:
    print(f"    - Date: {record.get('date')}, AM: {record.get('am_status')}, PM: {record.get('pm_status')}")

print("\n" + "="*70)
print("✅ DATABASE CHECK COMPLETE")
print("="*70)
