#!/usr/bin/env python3
"""
Photo Organization Script for Bus Tracker Backend
Reorganizes photos by role and adds attendance folders for students
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path

# Paths
BACKEND_DIR = Path("/app/backend")
PHOTOS_DIR = BACKEND_DIR / "photos"
BACKUPS_DIR = BACKEND_DIR / "backups"

def backup_current_state():
    """Create backup of current photos directory and database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup photos directory
    if PHOTOS_DIR.exists():
        backup_photos_dir = BACKEND_DIR / f"photos_backup_{timestamp}"
        print(f"📦 Creating backup of photos directory: {backup_photos_dir}")
        shutil.copytree(PHOTOS_DIR, backup_photos_dir)
        print(f"✅ Photos backed up to: {backup_photos_dir}")
    
    return timestamp

def get_latest_backup_file():
    """Find the latest database backup file"""
    backup_files = list(BACKUPS_DIR.glob("seed_backup_*.json"))
    if not backup_files:
        raise FileNotFoundError("No backup files found in /app/backend/backups/")
    
    latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
    print(f"📄 Using database backup: {latest_backup}")
    return latest_backup

def load_database_backup(backup_file):
    """Load and parse the database backup"""
    with open(backup_file, 'r') as f:
        data = json.load(f)
    return data

def create_role_directories():
    """Create the new directory structure"""
    print("\n📁 Creating role-based directory structure...")
    
    directories = [
        PHOTOS_DIR / "students",
        PHOTOS_DIR / "parents",
        PHOTOS_DIR / "teachers",
        PHOTOS_DIR / "admins"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ Created: {directory}")
    
    print("✅ Directory structure created")

def organize_student_photos(students_data):
    """Organize student photos and create attendance folders"""
    print("\n👨‍🎓 Organizing student photos...")
    
    # Get list of existing STU*.jpg files
    existing_photos = sorted(PHOTOS_DIR.glob("STU*.jpg"))
    
    if not existing_photos:
        print("⚠️  No STU*.jpg files found to organize")
        return {}
    
    photo_mappings = {}
    
    # Create folders for each student
    for idx, student in enumerate(students_data):
        student_id = student.get('student_id')
        roll_number = student.get('roll_number', f'STU{idx+1:03d}')
        name = student.get('name', 'Unknown')
        
        # Create student directory
        student_dir = PHOTOS_DIR / "students" / student_id
        student_dir.mkdir(parents=True, exist_ok=True)
        
        # Create attendance subdirectory
        attendance_dir = student_dir / "attendance"
        attendance_dir.mkdir(parents=True, exist_ok=True)
        
        # Move photo if available
        if idx < len(existing_photos):
            source_photo = existing_photos[idx]
            dest_photo = student_dir / "profile.jpg"
            
            shutil.copy2(source_photo, dest_photo)
            print(f"   ✓ {source_photo.name} → {student_id}/profile.jpg ({name})")
            
            photo_mappings[student_id] = {
                'photo_path': f"backend/photos/students/{student_id}/profile.jpg",
                'attendance_path': f"backend/photos/students/{student_id}/attendance",
                'has_photo': True
            }
        else:
            print(f"   ⚠️  No photo available for {student_id} ({name})")
            photo_mappings[student_id] = {
                'photo_path': None,
                'attendance_path': f"backend/photos/students/{student_id}/attendance",
                'has_photo': False
            }
    
    print(f"✅ Organized {len(photo_mappings)} student photo folders")
    return photo_mappings

def create_placeholder_photos_for_other_roles(users_data):
    """Create directories for parents, teachers, and admins"""
    print("\n👥 Organizing user role directories...")
    
    role_mappings = {
        'parents': {},
        'teachers': {},
        'admins': {}
    }
    
    for user in users_data:
        role = user.get('role')
        user_id = user.get('user_id')
        name = user.get('name', 'Unknown')
        
        if role in ['parent', 'teacher', 'admin']:
            role_plural = f"{role}s"
            user_photo_path = PHOTOS_DIR / role_plural / f"{user_id}.jpg"
            
            # For now, we don't have photos for these roles, but we create the path
            role_mappings[role_plural][user_id] = {
                'photo_path': f"backend/photos/{role_plural}/{user_id}.jpg" if user.get('photo') else None,
                'has_photo': False
            }
            
            print(f"   ✓ Path reserved for {role}: {user_id} ({name})")
    
    print(f"✅ Processed paths for {len([u for u in users_data if u.get('role') != 'parent'])} non-parent users")
    return role_mappings

def update_database_backup(backup_file, student_mappings, role_mappings):
    """Update database backup with new photo paths"""
    print("\n💾 Updating database backup with new photo paths...")
    
    # Load the backup
    data = load_database_backup(backup_file)
    
    # Create backup of original
    backup_copy = backup_file.parent / f"{backup_file.stem}.bak"
    shutil.copy2(backup_file, backup_copy)
    print(f"   ✓ Created backup: {backup_copy}")
    
    # Update students
    students = data['collections']['students']
    for student in students:
        student_id = student.get('student_id')
        if student_id in student_mappings:
            mapping = student_mappings[student_id]
            student['photo_path'] = mapping['photo_path']
            student['attendance_path'] = mapping['attendance_path']
            if mapping['has_photo']:
                student['photo'] = mapping['photo_path']
    
    # Update users (parents, teachers, admins)
    users = data['collections']['users']
    for user in users:
        role = user.get('role')
        user_id = user.get('user_id')
        
        if role in ['parent', 'teacher', 'admin']:
            role_plural = f"{role}s"
            if user_id in role_mappings.get(role_plural, {}):
                mapping = role_mappings[role_plural][user_id]
                user['photo_path'] = mapping['photo_path']
                # Don't set photo field if we don't have actual photo
    
    # Add metadata about the reorganization
    data['photo_organization'] = {
        'reorganized_at': datetime.now().isoformat(),
        'structure_version': '1.0',
        'description': 'Photos organized by role with attendance folders for students'
    }
    
    # Write updated backup
    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Database backup updated: {backup_file}")
    print(f"   ✓ Updated {len(students)} student records")
    print(f"   ✓ Updated {len(users)} user records")

def cleanup_old_photos():
    """Remove old STU*.jpg files from root photos directory"""
    print("\n🧹 Cleaning up old photo files...")
    
    old_photos = list(PHOTOS_DIR.glob("STU*.jpg"))
    if old_photos:
        for photo in old_photos:
            photo.unlink()
            print(f"   ✓ Removed: {photo.name}")
        print(f"✅ Cleaned up {len(old_photos)} old photo files")
    else:
        print("   ℹ️  No old photos to clean up")

def generate_summary_report(student_mappings, role_mappings):
    """Generate a summary report of the organization"""
    print("\n" + "="*60)
    print("📊 PHOTO ORGANIZATION SUMMARY")
    print("="*60)
    
    students_with_photos = sum(1 for m in student_mappings.values() if m['has_photo'])
    total_students = len(student_mappings)
    
    print(f"\n📸 Students:")
    print(f"   • Total students: {total_students}")
    print(f"   • With photos: {students_with_photos}")
    print(f"   • Without photos: {total_students - students_with_photos}")
    print(f"   • All have attendance folders: Yes")
    
    for role_name, mapping in role_mappings.items():
        print(f"\n👥 {role_name.capitalize()}:")
        print(f"   • Total: {len(mapping)}")
        print(f"   • Photo paths reserved: {len(mapping)}")
    
    print("\n📁 Directory Structure:")
    print(f"   • backend/photos/students/ - {total_students} folders")
    print(f"   • backend/photos/parents/ - Ready for uploads")
    print(f"   • backend/photos/teachers/ - Ready for uploads")
    print(f"   • backend/photos/admins/ - Ready for uploads")
    
    print("\n" + "="*60)
    print("✅ ORGANIZATION COMPLETE")
    print("="*60)

def main():
    """Main execution function"""
    print("🚀 Starting Bus Tracker Photo Organization")
    print("="*60)
    
    try:
        # Step 1: Backup current state
        timestamp = backup_current_state()
        
        # Step 2: Load database backup
        backup_file = get_latest_backup_file()
        data = load_database_backup(backup_file)
        
        # Step 3: Create new directory structure
        create_role_directories()
        
        # Step 4: Organize student photos
        students = data['collections']['students']
        student_mappings = organize_student_photos(students)
        
        # Step 5: Setup paths for other roles
        users = data['collections']['users']
        role_mappings = create_placeholder_photos_for_other_roles(users)
        
        # Step 6: Update database backup
        update_database_backup(backup_file, student_mappings, role_mappings)
        
        # Step 7: Cleanup old files
        cleanup_old_photos()
        
        # Step 8: Generate summary
        generate_summary_report(student_mappings, role_mappings)
        
        print("\n🎉 Photo organization completed successfully!")
        print(f"\n💡 Next steps:")
        print(f"   1. Review the changes in backend/photos/")
        print(f"   2. Update documentation in /docs/")
        print(f"   3. Test the application with new photo paths")
        
    except Exception as e:
        print(f"\n❌ Error during organization: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
