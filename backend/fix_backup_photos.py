"""
Fix Backup Photos Script
Replaces photo_path with photo field and updates all photo URLs in the backup
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

BACKUP_PATH = Path('/app/backend/backups/seed_backup_20251114_0532.json')


def convert_photo_path_to_url(photo_path: str) -> str:
    """
    Convert backend photo path to API URL
    backend/photos/students/xyz/profile.jpg -> /api/photos/students/xyz/profile.jpg
    """
    if not photo_path:
        return None
    
    # Remove 'backend/' prefix if present
    if photo_path.startswith('backend/'):
        photo_path = photo_path[8:]  # Remove 'backend/'
    
    # Add /api/ prefix if not present
    if not photo_path.startswith('/api/photos/'):
        if photo_path.startswith('photos/'):
            photo_path = '/api/' + photo_path
        elif photo_path.startswith('/photos/'):
            photo_path = '/api' + photo_path
        else:
            photo_path = '/api/photos/' + photo_path
    
    return photo_path


def fix_backup_photos():
    """Main function to fix photo fields in backup"""
    
    print("=" * 70)
    print("📸 FIXING BACKUP PHOTOS")
    print("=" * 70)
    
    # Create backup of original file
    backup_copy = BACKUP_PATH.with_suffix('.json.bak')
    shutil.copy(BACKUP_PATH, backup_copy)
    print(f"✅ Created backup: {backup_copy.name}")
    
    # Load the backup file
    with open(BACKUP_PATH, 'r') as f:
        backup_data = json.load(f)
    
    collections = backup_data.get('collections', {})
    
    # Fix STUDENTS: replace photo_path with photo
    students = collections.get('students', [])
    students_fixed = 0
    students_removed_photo_path = 0
    
    print(f"\n📚 Processing {len(students)} students...")
    for student in students:
        if 'photo_path' in student:
            photo_path = student.pop('photo_path')  # Remove photo_path field
            students_removed_photo_path += 1
            
            # Convert and set photo field
            if photo_path:
                student['photo'] = convert_photo_path_to_url(photo_path)
                students_fixed += 1
            else:
                student['photo'] = None
    
    print(f"   ✅ Removed 'photo_path' field from {students_removed_photo_path} students")
    print(f"   ✅ Fixed {students_fixed} student photo URLs")
    
    # Fix USERS: generate proper photo URLs based on role and user_id
    users = collections.get('users', [])
    users_fixed = 0
    
    print(f"\n👥 Processing {len(users)} users...")
    for user in users:
        role = user.get('role')
        user_id = user.get('user_id')
        
        if role and user_id:
            # Generate photo URL based on role
            if role == 'admin':
                photo_url = f"/api/photos/admins/{user_id}.jpg"
            elif role == 'teacher':
                photo_url = f"/api/photos/teachers/{user_id}.jpg"
            elif role == 'parent':
                photo_url = f"/api/photos/parents/{user_id}.jpg"
            else:
                photo_url = None
            
            if photo_url:
                user['photo'] = photo_url
                users_fixed += 1
    
    print(f"   ✅ Fixed {users_fixed} user photo URLs")
    
    # Update timestamp
    backup_data['timestamp'] = datetime.now().isoformat()
    backup_data['last_modified'] = datetime.now().isoformat()
    backup_data['modification_note'] = "Replaced photo_path with photo field and updated all photo URLs"
    
    # Save the fixed backup
    with open(BACKUP_PATH, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"\n💾 Saved updated backup: {BACKUP_PATH.name}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ BACKUP FIX COMPLETED")
    print("=" * 70)
    print(f"Total students processed: {len(students)}")
    print(f"  - Removed photo_path field: {students_removed_photo_path}")
    print(f"  - Fixed photo URLs: {students_fixed}")
    print(f"\nTotal users processed: {len(users)}")
    print(f"  - Fixed photo URLs: {users_fixed}")
    print(f"\nOriginal backup saved as: {backup_copy.name}")


if __name__ == "__main__":
    fix_backup_photos()
