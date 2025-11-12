#!/usr/bin/env python3
"""
Enhanced Photo Population Script for Bus Tracker
Populates photos for all user roles using AI-generated placeholder images
Integrates with organized photo structure and updates database
"""

import os
import json
import requests
import shutil
from pathlib import Path
from datetime import datetime
from time import sleep
import logging

# === Configuration ===
BACKEND_DIR = Path("/app/backend")
PHOTOS_DIR = BACKEND_DIR / "photos"
BACKUPS_DIR = BACKEND_DIR / "backups"
LOGS_DIR = BACKEND_DIR / "logs"

# Photo generation settings
BASE_URL = "https://thispersondoesnotexist.com/"
DELAY_SEC = 2  # Polite delay between requests
TIMEOUT_SEC = 15

# Setup logging
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / "photo_maker.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def download_ai_photo(output_path):
    """Download AI-generated photo from thispersondoesnotexist.com"""
    try:
        response = requests.get(
            BASE_URL, 
            timeout=TIMEOUT_SEC, 
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            logger.info(f"✓ Downloaded: {output_path}")
            return True
        else:
            logger.warning(f"⚠️  Failed ({response.status_code}): {output_path}")
            return False
    except Exception as e:
        logger.error(f"❌ Error downloading {output_path}: {e}")
        return False


def get_latest_backup_file():
    """Find the latest database backup file"""
    backup_files = list(BACKUPS_DIR.glob("seed_backup_*.json"))
    if not backup_files:
        raise FileNotFoundError("No backup files found in /app/backend/backups/")
    
    latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
    logger.info(f"📄 Using database backup: {latest_backup}")
    return latest_backup


def load_database_backup(backup_file):
    """Load and parse the database backup"""
    with open(backup_file, 'r') as f:
        data = json.load(f)
    return data


def populate_student_photos(students_data):
    """Generate profile photos for all students"""
    logger.info("\n👨‍🎓 Populating student photos...")
    
    populated_count = 0
    skipped_count = 0
    
    for student in students_data:
        student_id = student.get('student_id')
        name = student.get('name', 'Unknown')
        
        # Create student directory structure
        student_dir = PHOTOS_DIR / "students" / student_id
        student_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure attendance folder exists
        attendance_dir = student_dir / "attendance"
        attendance_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if profile photo already exists
        profile_photo = student_dir / "profile.jpg"
        
        if profile_photo.exists():
            logger.info(f"   ⏭️  Skipped (exists): {name} - {student_id}")
            skipped_count += 1
            continue
        
        # Download new photo
        logger.info(f"   📸 Generating photo for: {name} - {student_id}")
        if download_ai_photo(profile_photo):
            populated_count += 1
            sleep(DELAY_SEC)  # Polite delay
        else:
            logger.warning(f"   ⚠️  Failed to generate photo for: {name}")
    
    logger.info(f"✅ Student photos: {populated_count} generated, {skipped_count} existing")
    return populated_count, skipped_count


def populate_user_photos(users_data):
    """Generate photos for parents, teachers, and admins"""
    logger.info("\n👥 Populating user role photos...")
    
    stats = {
        'parents': {'generated': 0, 'skipped': 0},
        'teachers': {'generated': 0, 'skipped': 0},
        'admins': {'generated': 0, 'skipped': 0}
    }
    
    for user in users_data:
        role = user.get('role')
        user_id = user.get('user_id')
        name = user.get('name', 'Unknown')
        
        if role not in ['parent', 'teacher', 'admin']:
            continue
        
        role_plural = f"{role}s"
        role_dir = PHOTOS_DIR / role_plural
        role_dir.mkdir(parents=True, exist_ok=True)
        
        user_photo = role_dir / f"{user_id}.jpg"
        
        if user_photo.exists():
            logger.info(f"   ⏭️  Skipped ({role}): {name} - photo exists")
            stats[role_plural]['skipped'] += 1
            continue
        
        # Download new photo
        logger.info(f"   📸 Generating photo for {role}: {name} - {user_id}")
        if download_ai_photo(user_photo):
            stats[role_plural]['generated'] += 1
            sleep(DELAY_SEC)  # Polite delay
        else:
            logger.warning(f"   ⚠️  Failed to generate photo for {role}: {name}")
    
    # Log statistics
    for role_plural, counts in stats.items():
        logger.info(f"✅ {role_plural.capitalize()}: {counts['generated']} generated, {counts['skipped']} existing")
    
    return stats


def update_database_with_photos(backup_file, students_data, users_data):
    """Update database backup with photo paths"""
    logger.info("\n💾 Updating database backup with photo paths...")
    
    # Create backup of original
    backup_copy = backup_file.parent / f"{backup_file.stem}.bak"
    if not backup_copy.exists():  # Only create if doesn't exist
        shutil.copy2(backup_file, backup_copy)
        logger.info(f"   ✓ Created backup: {backup_copy}")
    
    # Load current backup
    data = load_database_backup(backup_file)
    
    updated_students = 0
    updated_users = 0
    
    # Update students
    for student in data['collections']['students']:
        student_id = student.get('student_id')
        student_dir = PHOTOS_DIR / "students" / student_id
        profile_photo = student_dir / "profile.jpg"
        attendance_dir = student_dir / "attendance"
        
        # Update paths
        if profile_photo.exists():
            photo_path = f"backend/photos/students/{student_id}/profile.jpg"
            student['photo_path'] = photo_path
            student['photo'] = photo_path
        
        # Always set attendance path
        student['attendance_path'] = f"backend/photos/students/{student_id}/attendance"
        updated_students += 1
    
    # Update users
    for user in data['collections']['users']:
        role = user.get('role')
        user_id = user.get('user_id')
        
        if role in ['parent', 'teacher', 'admin']:
            role_plural = f"{role}s"
            user_photo = PHOTOS_DIR / role_plural / f"{user_id}.jpg"
            
            if user_photo.exists():
                photo_path = f"backend/photos/{role_plural}/{user_id}.jpg"
                user['photo_path'] = photo_path
                user['photo'] = photo_path
            else:
                # Set path even if photo doesn't exist yet (reserved)
                user['photo_path'] = f"backend/photos/{role_plural}/{user_id}.jpg"
            
            updated_users += 1
    
    # Add metadata
    if 'photo_population' not in data:
        data['photo_population'] = {}
    
    data['photo_population']['last_updated'] = datetime.now().isoformat()
    data['photo_population']['populated_by'] = 'populate_photos.py'
    
    # Write updated backup
    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"✅ Database updated: {updated_students} students, {updated_users} users")


def validate_photo_structure():
    """Validate that all required photos exist"""
    logger.info("\n🔍 Validating photo structure...")
    
    backup_file = get_latest_backup_file()
    data = load_database_backup(backup_file)
    
    issues = []
    
    # Check students
    students = data['collections']['students']
    for student in students:
        student_id = student.get('student_id')
        name = student.get('name')
        
        # Check profile photo
        profile_photo = PHOTOS_DIR / "students" / student_id / "profile.jpg"
        if not profile_photo.exists():
            issues.append(f"Missing student profile: {name} ({student_id})")
        
        # Check attendance folder
        attendance_dir = PHOTOS_DIR / "students" / student_id / "attendance"
        if not attendance_dir.exists():
            issues.append(f"Missing attendance folder: {name} ({student_id})")
    
    # Check users
    users = data['collections']['users']
    for user in users:
        role = user.get('role')
        user_id = user.get('user_id')
        name = user.get('name')
        
        if role in ['parent', 'teacher', 'admin']:
            role_plural = f"{role}s"
            user_photo = PHOTOS_DIR / role_plural / f"{user_id}.jpg"
            if not user_photo.exists():
                # This is not an error, just informational
                logger.info(f"   ℹ️  Photo not yet uploaded: {role} - {name}")
    
    if issues:
        logger.warning(f"⚠️  Found {len(issues)} issues:")
        for issue in issues:
            logger.warning(f"   - {issue}")
    else:
        logger.info("✅ All required photos and folders present")
    
    return len(issues) == 0


def generate_summary_report():
    """Generate a summary report of photo population"""
    logger.info("\n" + "="*70)
    logger.info("📊 PHOTO POPULATION SUMMARY")
    logger.info("="*70)
    
    # Count photos
    student_photos = len(list((PHOTOS_DIR / "students").rglob("profile.jpg")))
    parent_photos = len(list((PHOTOS_DIR / "parents").glob("*.jpg")))
    teacher_photos = len(list((PHOTOS_DIR / "teachers").glob("*.jpg")))
    admin_photos = len(list((PHOTOS_DIR / "admins").glob("*.jpg")))
    attendance_folders = len(list((PHOTOS_DIR / "students").glob("*/attendance")))
    
    logger.info(f"\n📸 Photos by Role:")
    logger.info(f"   • Students: {student_photos} profile photos")
    logger.info(f"   • Parents: {parent_photos} photos")
    logger.info(f"   • Teachers: {teacher_photos} photos")
    logger.info(f"   • Admins: {admin_photos} photos")
    logger.info(f"\n📁 Structure:")
    logger.info(f"   • Attendance folders: {attendance_folders}")
    
    logger.info("\n" + "="*70)
    logger.info("✅ PHOTO POPULATION COMPLETE")
    logger.info("="*70)


def main():
    """Main execution function"""
    logger.info("🚀 Starting Bus Tracker Photo Population")
    logger.info("="*70)
    
    try:
        # Load database backup
        backup_file = get_latest_backup_file()
        data = load_database_backup(backup_file)
        
        students = data['collections']['students']
        users = data['collections']['users']
        
        logger.info(f"📊 Database contains:")
        logger.info(f"   • {len(students)} students")
        logger.info(f"   • {len(users)} users")
        
        # Populate student photos
        student_stats = populate_student_photos(students)
        
        # Populate user photos
        user_stats = populate_user_photos(users)
        
        # Update database
        update_database_with_photos(backup_file, students, users)
        
        # Validate structure
        validate_photo_structure()
        
        # Generate summary
        generate_summary_report()
        
        logger.info(f"\n💡 Log file: {log_file}")
        logger.info(f"🎉 Photo population completed successfully!")
        
    except Exception as e:
        logger.error(f"\n❌ Error during photo population: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
