#!/usr/bin/env python3
"""
Fix Photo Paths in Seed Backup
Updates user and student photo paths to match actual photo files.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

# Constants
BACKEND_DIR = Path(__file__).parent
BACKUPS_DIR = BACKEND_DIR / "backups"
PHOTOS_DIR = BACKEND_DIR / "photos"
SEED_BACKUP_FILE = BACKUPS_DIR / "seed_backup_20251114_0532.json"
ATTENDANCE_BACKUP_FILE = BACKUPS_DIR / "attendance" / "attendance_backup_20251114_0532.json"

def main():
    print("\n" + "="*70)
    print("  🔧 FIX PHOTO PATHS IN BACKUPS")
    print("="*70)
    
    # Load seed backup
    print("\n📖 Loading seed backup...")
    with open(SEED_BACKUP_FILE, 'r') as f:
        seed_data = json.load(f)
    
    users = seed_data['collections']['users']
    students = seed_data['collections']['students']
    
    print(f"   ✅ Found {len(users)} users, {len(students)} students")
    
    # Fix user photos
    print("\n🔧 Fixing user photo paths...")
    user_updates = 0
    for user in users:
        user_id = user['user_id']
        role = user['role']
        
        # Determine role directory
        if role == 'admin':
            role_dir = 'admins'
        elif role == 'teacher':
            role_dir = 'teachers'
        elif role == 'parent':
            role_dir = 'parents'
        else:
            continue
        
        # Check if photo exists
        photo_file = PHOTOS_DIR / role_dir / f"{user_id}.jpg"
        if photo_file.exists():
            user['photo'] = f"backend/photos/{role_dir}/{user_id}.jpg"
            user_updates += 1
            print(f"   ✓ {user['name']}: backend/photos/{role_dir}/{user_id}.jpg")
    
    print(f"   ✅ Updated {user_updates} user photo paths")
    
    # Fix student photos  
    print("\n🔧 Fixing student photo paths...")
    student_updates = 0
    for student in students:
        student_id = student['student_id']
        
        # Check if profile photo exists
        photo_file = PHOTOS_DIR / "students" / student_id / "profile.jpg"
        if photo_file.exists():
            student['photo_path'] = f"backend/photos/students/{student_id}/profile.jpg"
            student_updates += 1
            print(f"   ✓ {student['name']}: profile.jpg")
        
        # Set attendance path
        attendance_dir = PHOTOS_DIR / "students" / student_id / "attendance"
        if attendance_dir.exists():
            student['attendance_path'] = f"backend/photos/students/{student_id}/attendance"
    
    print(f"   ✅ Updated {student_updates} student photo paths")
    
    # Fix attendance photo URLs
    print("\n🔧 Fixing attendance photo URLs...")
    with open(ATTENDANCE_BACKUP_FILE, 'r') as f:
        attendance_data = json.load(f)
    
    attendance_records = attendance_data['collections']['attendance']
    attendance_updates = 0
    
    for record in attendance_records:
        if record.get('scan_photo') and record['scan_photo'].startswith('/photos/'):
            # Convert /photos/... to /api/photos/...
            record['scan_photo'] = '/api' + record['scan_photo']
            attendance_updates += 1
    
    print(f"   ✅ Updated {attendance_updates} attendance photo URLs")
    
    # Save updated seed backup
    print("\n💾 Saving updated seed backup...")
    seed_data['timestamp'] = datetime.now(timezone.utc).isoformat()
    
    with open(SEED_BACKUP_FILE, 'w') as f:
        json.dump(seed_data, f, indent=2)
    
    print(f"   ✅ Seed backup updated")
    
    # Save updated attendance backup
    print("\n💾 Saving updated attendance backup...")
    attendance_data['timestamp'] = datetime.now(timezone.utc).isoformat()
    
    with open(ATTENDANCE_BACKUP_FILE, 'w') as f:
        json.dump(attendance_data, f, indent=2)
    
    print(f"   ✅ Attendance backup updated")
    
    print("\n" + "="*70)
    print("  ✅ PHOTO PATHS FIXED")
    print("="*70)
    print(f"\n📊 Summary:")
    print(f"   • User photos fixed: {user_updates}")
    print(f"   • Student photos fixed: {student_updates}")
    print(f"   • Attendance photo URLs fixed: {attendance_updates}")
    print("\n💡 Restart backend to load updated data!")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
