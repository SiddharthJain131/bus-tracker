#!/usr/bin/env python3
"""
Populate Attendance Samples Script
Generates sample attendance records with yellow→green sequences
and downloads photos from thispersondoesnotexist.com for missing photos.
"""

import json
import os
import sys
import time
import uuid
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict

# Constants
BACKEND_DIR = Path(__file__).parent
BACKUPS_DIR = BACKEND_DIR / "backups"
ATTENDANCE_BACKUP_DIR = BACKUPS_DIR / "attendance"
PHOTOS_DIR = BACKEND_DIR / "photos" / "students"
ATTENDANCE_BACKUP_FILE = ATTENDANCE_BACKUP_DIR / "attendance_backup_20251114_0532.json"
MAIN_BACKUP_FILE = BACKUPS_DIR / "seed_backup_20251114_0532.json"

# Photo generation settings
PHOTO_SOURCE_URL = "https://thispersondoesnotexist.com/"
RETRY_DELAY = 2  # seconds between photo downloads

def load_students() -> List[Dict]:
    """Load student data from main backup."""
    print("\n📖 Loading student data from main backup...")
    with open(MAIN_BACKUP_FILE, 'r') as f:
        data = json.load(f)
    students = data['collections']['students']
    print(f"   ✅ Found {len(students)} students")
    return students

def download_photo(save_path: Path) -> bool:
    """
    Download a photo from thispersondoesnotexist.com
    Returns True if successful, False otherwise.
    """
    try:
        # Make request with headers to avoid blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(PHOTO_SOURCE_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Save the image
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        return True
    except Exception as e:
        print(f"   ⚠️  Failed to download photo: {e}")
        return False

def generate_sample_attendance_records(students: List[Dict]) -> List[Dict]:
    """
    Generate sample attendance records with yellow→green sequences.
    Creates records for the past 7 days with varied patterns.
    """
    print("\n🎨 Generating sample attendance records...")
    records = []
    today = datetime.now(timezone.utc)
    
    # Generate records for past 7 days
    for day_offset in range(7):
        date = today - timedelta(days=day_offset)
        date_str = date.strftime("%Y-%m-%d")
        
        # Select 5 random students for each day
        sample_students = students[:5] if day_offset % 2 == 0 else students[5:10]
        
        for student in sample_students:
            student_id = student['student_id']
            
            # Morning sequence (yellow → green)
            # First scan at pickup stop (yellow)
            morning_pickup_time = date.replace(hour=7, minute=30) + timedelta(minutes=(day_offset * 5))
            records.append({
                "_id": f"att_{uuid.uuid4().hex[:16]}",
                "attendance_id": str(uuid.uuid4()),
                "student_id": student_id,
                "date": date_str,
                "trip": "AM",
                "status": "yellow",
                "confidence": round(0.85 + (day_offset * 0.02), 2),
                "last_update": morning_pickup_time.isoformat(),
                "scan_photo": None,  # Will be populated with photo URL
                "scan_timestamp": morning_pickup_time.isoformat()
            })
            
            # Second scan at school (green) - only for some days
            if day_offset < 5:  # Last 2 days stay yellow
                morning_school_time = morning_pickup_time + timedelta(minutes=25)
                records.append({
                    "_id": f"att_{uuid.uuid4().hex[:16]}",
                    "attendance_id": str(uuid.uuid4()),
                    "student_id": student_id,
                    "date": date_str,
                    "trip": "AM",
                    "status": "green",
                    "confidence": round(0.88 + (day_offset * 0.01), 2),
                    "last_update": morning_school_time.isoformat(),
                    "scan_photo": None,  # Will be populated with photo URL
                    "scan_timestamp": morning_school_time.isoformat()
                })
            
            # Evening sequence (yellow → green)
            # First scan at school (yellow)
            evening_school_time = date.replace(hour=15, minute=10) + timedelta(minutes=(day_offset * 3))
            records.append({
                "_id": f"att_{uuid.uuid4().hex[:16]}",
                "attendance_id": str(uuid.uuid4()),
                "student_id": student_id,
                "date": date_str,
                "trip": "PM",
                "status": "yellow",
                "confidence": round(0.83 + (day_offset * 0.02), 2),
                "last_update": evening_school_time.isoformat(),
                "scan_photo": None,  # Will be populated with photo URL
                "scan_timestamp": evening_school_time.isoformat()
            })
            
            # Second scan at home (green) - only for some days
            if day_offset < 4:  # Last 3 days stay yellow
                evening_home_time = evening_school_time + timedelta(minutes=30)
                records.append({
                    "_id": f"att_{uuid.uuid4().hex[:16]}",
                    "attendance_id": str(uuid.uuid4()),
                    "student_id": student_id,
                    "date": date_str,
                    "trip": "PM",
                    "status": "green",
                    "confidence": round(0.86 + (day_offset * 0.01), 2),
                    "last_update": evening_home_time.isoformat(),
                    "scan_photo": None,  # Will be populated with photo URL
                    "scan_timestamp": evening_home_time.isoformat()
                })
    
    print(f"   ✅ Generated {len(records)} attendance records")
    return records

def populate_photos_for_records(records: List[Dict], students: List[Dict]) -> tuple:
    """
    Download and save photos for attendance records.
    Returns (updated_records, photo_count).
    """
    print("\n📸 Downloading photos for attendance records...")
    
    # Create student ID to name mapping
    student_map = {s['student_id']: s['name'] for s in students}
    
    photo_count = 0
    updated_records = []
    
    for i, record in enumerate(records, 1):
        student_id = record['student_id']
        student_name = student_map.get(student_id, 'Unknown')
        date = record['date']
        trip = record['trip']
        status = record['status']
        
        # Create photo filename
        photo_filename = f"{date}_{trip}_{status}.jpg"
        attendance_dir = PHOTOS_DIR / student_id / "attendance"
        photo_path = attendance_dir / photo_filename
        
        # Check if photo already exists
        if photo_path.exists():
            print(f"   [{i}/{len(records)}] ✓ Photo already exists: {photo_filename}")
            photo_url = f"/photos/students/{student_id}/attendance/{photo_filename}"
            record['scan_photo'] = photo_url
            updated_records.append(record)
            continue
        
        # Download photo
        print(f"   [{i}/{len(records)}] Downloading photo for {student_name} - {date} {trip} ({status})...")
        success = download_photo(photo_path)
        
        if success:
            photo_count += 1
            photo_url = f"/photos/students/{student_id}/attendance/{photo_filename}"
            record['scan_photo'] = photo_url
            print(f"   ✅ Saved: {photo_filename}")
            
            # Small delay to avoid rate limiting
            if i < len(records):
                time.sleep(RETRY_DELAY)
        else:
            print(f"   ⚠️  Failed to download photo for {photo_filename}")
        
        updated_records.append(record)
    
    print(f"\n   ✅ Downloaded {photo_count} new photos")
    return updated_records, photo_count

def update_attendance_backup(records: List[Dict]):
    """Update the attendance backup file with new records."""
    print("\n💾 Updating attendance backup file...")
    
    # Load existing backup
    with open(ATTENDANCE_BACKUP_FILE, 'r') as f:
        backup_data = json.load(f)
    
    # Get existing records
    existing_records = backup_data['collections']['attendance']
    print(f"   ℹ️  Existing records: {len(existing_records)}")
    
    # Merge with new records (replace if attendance_id matches, otherwise append)
    existing_ids = {r['attendance_id'] for r in existing_records}
    new_records = [r for r in records if r['attendance_id'] not in existing_ids]
    
    all_records = existing_records + new_records
    print(f"   ℹ️  New records added: {len(new_records)}")
    print(f"   ℹ️  Total records: {len(all_records)}")
    
    # Update backup
    backup_data['collections']['attendance'] = all_records
    backup_data['timestamp'] = datetime.now(timezone.utc).isoformat()
    
    # Write backup
    with open(ATTENDANCE_BACKUP_FILE, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"   ✅ Attendance backup updated")

def main():
    """Main execution function."""
    print("\n" + "="*70)
    print("  🎯 POPULATE ATTENDANCE SAMPLES WITH PHOTOS")
    print("="*70)
    
    # Load students
    students = load_students()
    
    # Generate sample attendance records
    records = generate_sample_attendance_records(students)
    
    # Download and populate photos
    updated_records, photo_count = populate_photos_for_records(records, students)
    
    # Update attendance backup
    update_attendance_backup(updated_records)
    
    print("\n" + "="*70)
    print("  ✅ ATTENDANCE SAMPLES POPULATION COMPLETED")
    print("="*70)
    print(f"\n📊 Summary:")
    print(f"   • Total attendance records: {len(updated_records)}")
    print(f"   • Photos downloaded: {photo_count}")
    print(f"   • Yellow scans (in-transit): {sum(1 for r in updated_records if r['status'] == 'yellow')}")
    print(f"   • Green scans (completed): {sum(1 for r in updated_records if r['status'] == 'green')}")
    print(f"\n💡 Yellow scans now display attendance data just like green scans.")
    print(f"💡 Frontend updated to allow clicking on yellow status cells.")
    print(f"\n✅ All tasks completed successfully!")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
