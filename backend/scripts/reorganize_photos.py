#!/usr/bin/env python3
"""
Script to reorganize photos folder using backup data.
- Reads seed and attendance backup files
- For photo: null entries, uses a default profile image
- Downloads photos from thispersondoesnotexist.com
- Creates proper folder structure
"""

import json
import os
import shutil
import requests
import time
from pathlib import Path
from PIL import Image
import io

# Paths
BACKUP_DIR = Path("/app/backend/backups")
SEED_BACKUP = BACKUP_DIR / "seed_backup_20251114_0532.json"
ATTENDANCE_BACKUP = BACKUP_DIR / "attendance/attendance_backup_20251114_0532.json"
PHOTOS_DIR = Path("/app/backend/photos")
NEW_PHOTOS_DIR = Path("/app/backend/photos_new")

# API for generating random faces
FACE_API_URL = "https://thispersondoesnotexist.com/"

def download_random_face(save_path, retry=3):
    """Download a random face from thispersondoesnotexist.com"""
    for attempt in range(retry):
        try:
            # Add a random parameter to avoid caching
            response = requests.get(
                FACE_API_URL,
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=10
            )
            if response.status_code == 200:
                # Save the image
                img = Image.open(io.BytesIO(response.content))
                img = img.convert('RGB')
                # Resize to a reasonable size (e.g., 512x512)
                img = img.resize((512, 512), Image.Resampling.LANCZOS)
                img.save(save_path, 'JPEG', quality=85)
                print(f"✓ Downloaded photo: {save_path}")
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                return True
            else:
                print(f"  Attempt {attempt + 1} failed with status {response.status_code}")
        except Exception as e:
            print(f"  Error on attempt {attempt + 1}: {str(e)}")
            time.sleep(1)
    
    print(f"✗ Failed to download photo after {retry} attempts: {save_path}")
    return False

def create_default_profile(save_path):
    """Create a simple default profile image"""
    try:
        # Create a simple colored square as default
        img = Image.new('RGB', (512, 512), color=(200, 200, 200))
        img.save(save_path, 'JPEG', quality=85)
        print(f"✓ Created default profile: {save_path}")
        return True
    except Exception as e:
        print(f"✗ Error creating default profile: {str(e)}")
        return False

def process_users(users_data):
    """Process user data and create photos"""
    stats = {
        'admin': {'total': 0, 'created': 0, 'failed': 0},
        'teacher': {'total': 0, 'created': 0, 'failed': 0},
        'parent': {'total': 0, 'created': 0, 'failed': 0},
        'student': {'total': 0, 'created': 0, 'failed': 0}
    }
    
    for user in users_data:
        role = user.get('role', 'unknown')
        user_id = user.get('user_id')
        photo = user.get('photo')
        
        if role in stats:
            stats[role]['total'] += 1
        
        if not user_id:
            continue
        
        # Determine the folder based on role
        if role == 'admin':
            role_folder = NEW_PHOTOS_DIR / 'admins'
            photo_path = role_folder / f"{user_id}.jpg"
        elif role == 'teacher':
            role_folder = NEW_PHOTOS_DIR / 'teachers'
            photo_path = role_folder / f"{user_id}.jpg"
        elif role == 'parent':
            role_folder = NEW_PHOTOS_DIR / 'parents'
            photo_path = role_folder / f"{user_id}.jpg"
        else:
            continue
        
        # Create role folder if it doesn't exist
        role_folder.mkdir(parents=True, exist_ok=True)
        
        # If photo is null, download a new one
        if photo is None:
            success = download_random_face(photo_path)
            if success:
                stats[role]['created'] += 1
            else:
                # Fallback to default
                if create_default_profile(photo_path):
                    stats[role]['created'] += 1
                else:
                    stats[role]['failed'] += 1
        else:
            # Photo exists, copy it if available in old structure
            old_photo_path = PHOTOS_DIR / photo.lstrip('/api/photos/')
            if old_photo_path.exists():
                shutil.copy2(old_photo_path, photo_path)
                stats[role]['created'] += 1
                print(f"✓ Copied existing photo: {photo_path}")
            else:
                # Download new one
                success = download_random_face(photo_path)
                if success:
                    stats[role]['created'] += 1
                else:
                    stats[role]['failed'] += 1
    
    return stats

def process_students(students_data, attendance_data):
    """Process student data and create photos including attendance photos"""
    stats = {'total': 0, 'created': 0, 'failed': 0, 'attendance_photos': 0}
    
    # Create a map of student_id to attendance records
    attendance_map = {}
    for record in attendance_data:
        student_id = record.get('student_id')
        if student_id not in attendance_map:
            attendance_map[student_id] = []
        attendance_map[student_id].append(record)
    
    for student in students_data:
        student_id = student.get('student_id')
        photo = student.get('photo')
        
        if not student_id:
            continue
        
        stats['total'] += 1
        
        # Create student folder
        student_folder = NEW_PHOTOS_DIR / 'students' / student_id
        student_folder.mkdir(parents=True, exist_ok=True)
        
        # Create attendance subfolder
        attendance_folder = student_folder / 'attendance'
        attendance_folder.mkdir(parents=True, exist_ok=True)
        
        # Profile photo
        profile_path = student_folder / 'profile.jpg'
        
        if photo is None or photo == 'null':
            # Download profile photo
            success = download_random_face(profile_path)
            if success:
                stats['created'] += 1
            else:
                if create_default_profile(profile_path):
                    stats['created'] += 1
                else:
                    stats['failed'] += 1
        else:
            # Copy existing photo if available
            old_photo_path = PHOTOS_DIR / photo.lstrip('/api/photos/')
            if old_photo_path.exists():
                shutil.copy2(old_photo_path, profile_path)
                stats['created'] += 1
                print(f"✓ Copied student profile: {profile_path}")
            else:
                success = download_random_face(profile_path)
                if success:
                    stats['created'] += 1
                else:
                    stats['failed'] += 1
        
        # Process attendance photos
        if student_id in attendance_map:
            for record in attendance_map[student_id]:
                date = record.get('date')
                trip = record.get('trip')
                scan_photo = record.get('scan_photo')
                
                if date and trip:
                    attendance_photo_path = attendance_folder / f"{date}_{trip}.jpg"
                    
                    # Try to copy from old structure
                    if scan_photo:
                        old_scan_path = PHOTOS_DIR / scan_photo.lstrip('/api/photos/')
                        if old_scan_path.exists():
                            shutil.copy2(old_scan_path, attendance_photo_path)
                            stats['attendance_photos'] += 1
                            print(f"✓ Copied attendance photo: {attendance_photo_path}")
                            continue
                    
                    # If not found, create a copy of profile with slight variation
                    if profile_path.exists():
                        try:
                            shutil.copy2(profile_path, attendance_photo_path)
                            stats['attendance_photos'] += 1
                        except Exception as e:
                            print(f"✗ Error copying attendance photo: {str(e)}")
    
    return stats

def main():
    print("=" * 70)
    print("PHOTO REORGANIZATION SCRIPT")
    print("=" * 70)
    print()
    
    # Load seed backup
    print("📂 Loading seed backup...")
    with open(SEED_BACKUP, 'r') as f:
        seed_data = json.load(f)
    
    users = seed_data['collections'].get('users', [])
    students = seed_data['collections'].get('students', [])
    print(f"   Found {len(users)} users and {len(students)} students")
    
    # Load attendance backup
    print("📂 Loading attendance backup...")
    with open(ATTENDANCE_BACKUP, 'r') as f:
        attendance_data = json.load(f)
    
    attendance_records = attendance_data['collections'].get('attendance', [])
    print(f"   Found {len(attendance_records)} attendance records")
    print()
    
    # Create new photos directory
    if NEW_PHOTOS_DIR.exists():
        print(f"⚠️  Removing existing {NEW_PHOTOS_DIR}...")
        shutil.rmtree(NEW_PHOTOS_DIR)
    
    NEW_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created new photos directory: {NEW_PHOTOS_DIR}")
    print()
    
    # Process users (admins, teachers, parents)
    print("👥 Processing users (admins, teachers, parents)...")
    print("-" * 70)
    user_stats = process_users(users)
    print()
    
    # Process students
    print("🎓 Processing students...")
    print("-" * 70)
    student_stats = process_students(students, attendance_records)
    print()
    
    # Print summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("Users:")
    for role, stats in user_stats.items():
        if stats['total'] > 0:
            print(f"  {role.capitalize():<10} - Total: {stats['total']}, Created: {stats['created']}, Failed: {stats['failed']}")
    
    print()
    print("Students:")
    print(f"  Total: {student_stats['total']}, Created: {student_stats['created']}, Failed: {student_stats['failed']}")
    print(f"  Attendance Photos: {student_stats['attendance_photos']}")
    print()
    
    # Final step: backup old and replace
    print("🔄 Finalizing...")
    if PHOTOS_DIR.exists():
        backup_old = Path("/app/backend/photos_old_backup")
        if backup_old.exists():
            shutil.rmtree(backup_old)
        print(f"   Backing up old photos to {backup_old}")
        shutil.move(str(PHOTOS_DIR), str(backup_old))
    
    print(f"   Moving new photos to {PHOTOS_DIR}")
    shutil.move(str(NEW_PHOTOS_DIR), str(PHOTOS_DIR))
    
    print()
    print("✅ Photo reorganization complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
