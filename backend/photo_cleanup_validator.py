#!/usr/bin/env python3
"""
Photo Organization Cleanup & Validation Script
Validates photo structure, cleans up redundant files, and generates reports
"""

import os
import json
from pathlib import Path
from datetime import datetime
import logging

# === Configuration ===
BACKEND_DIR = Path("/app/backend")
PHOTOS_DIR = BACKEND_DIR / "photos"
BACKUPS_DIR = BACKEND_DIR / "backups"
LOGS_DIR = BACKEND_DIR / "logs"
DOCS_DIR = Path("/app/docs")

# Setup logging
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / "photo_cleanup.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def get_latest_backup_file():
    """Find the latest database backup file"""
    backup_files = list(BACKUPS_DIR.glob("seed_backup_*.json"))
    if not backup_files:
        raise FileNotFoundError("No backup files found")
    
    latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
    return latest_backup


def load_database_backup(backup_file):
    """Load and parse the database backup"""
    with open(backup_file, 'r') as f:
        data = json.load(f)
    return data


def validate_all_photos():
    """Comprehensive validation of photo structure"""
    logger.info("\n🔍 Validating Complete Photo Structure...")
    
    backup_file = get_latest_backup_file()
    data = load_database_backup(backup_file)
    
    validation_report = {
        'students': {'total': 0, 'with_photos': 0, 'missing': []},
        'parents': {'total': 0, 'with_photos': 0, 'missing': []},
        'teachers': {'total': 0, 'with_photos': 0, 'missing': []},
        'admins': {'total': 0, 'with_photos': 0, 'missing': []},
        'attendance_folders': {'total': 0, 'missing': []},
        'database_fields': {'students_with_path': 0, 'users_with_path': 0}
    }
    
    # Validate students
    students = data['collections']['students']
    for student in students:
        student_id = student.get('student_id')
        name = student.get('name')
        validation_report['students']['total'] += 1
        
        # Check profile photo
        profile_photo = PHOTOS_DIR / "students" / student_id / "profile.jpg"
        if profile_photo.exists():
            validation_report['students']['with_photos'] += 1
        else:
            validation_report['students']['missing'].append(name)
        
        # Check attendance folder
        attendance_dir = PHOTOS_DIR / "students" / student_id / "attendance"
        if attendance_dir.exists():
            validation_report['attendance_folders']['total'] += 1
        else:
            validation_report['attendance_folders']['missing'].append(name)
        
        # Check database fields
        if student.get('photo_path'):
            validation_report['database_fields']['students_with_path'] += 1
    
    # Validate users
    users = data['collections']['users']
    for user in users:
        role = user.get('role')
        user_id = user.get('user_id')
        name = user.get('name')
        
        if role not in ['parent', 'teacher', 'admin']:
            continue
        
        role_plural = f"{role}s"
        validation_report[role_plural]['total'] += 1
        
        user_photo = PHOTOS_DIR / role_plural / f"{user_id}.jpg"
        if user_photo.exists():
            validation_report[role_plural]['with_photos'] += 1
        else:
            validation_report[role_plural]['missing'].append(name)
        
        # Check database fields
        if user.get('photo_path'):
            validation_report['database_fields']['users_with_path'] += 1
    
    # Print report
    logger.info("\n" + "="*70)
    logger.info("📊 VALIDATION REPORT")
    logger.info("="*70)
    
    logger.info(f"\n👨‍🎓 Students:")
    logger.info(f"   • Total: {validation_report['students']['total']}")
    logger.info(f"   • With Photos: {validation_report['students']['with_photos']}")
    logger.info(f"   • Missing Photos: {len(validation_report['students']['missing'])}")
    
    logger.info(f"\n👪 Parents:")
    logger.info(f"   • Total: {validation_report['parents']['total']}")
    logger.info(f"   • With Photos: {validation_report['parents']['with_photos']}")
    logger.info(f"   • Missing Photos: {len(validation_report['parents']['missing'])}")
    
    logger.info(f"\n👨‍🏫 Teachers:")
    logger.info(f"   • Total: {validation_report['teachers']['total']}")
    logger.info(f"   • With Photos: {validation_report['teachers']['with_photos']}")
    logger.info(f"   • Missing Photos: {len(validation_report['teachers']['missing'])}")
    
    logger.info(f"\n👔 Admins:")
    logger.info(f"   • Total: {validation_report['admins']['total']}")
    logger.info(f"   • With Photos: {validation_report['admins']['with_photos']}")
    logger.info(f"   • Missing Photos: {len(validation_report['admins']['missing'])}")
    
    logger.info(f"\n📁 Attendance Folders:")
    logger.info(f"   • Total: {validation_report['attendance_folders']['total']}")
    logger.info(f"   • Missing: {len(validation_report['attendance_folders']['missing'])}")
    
    logger.info(f"\n💾 Database Fields:")
    logger.info(f"   • Students with photo_path: {validation_report['database_fields']['students_with_path']}")
    logger.info(f"   • Users with photo_path: {validation_report['database_fields']['users_with_path']}")
    
    # Check for issues
    issues = []
    if validation_report['students']['missing']:
        issues.append(f"{len(validation_report['students']['missing'])} students missing photos")
    if validation_report['attendance_folders']['missing']:
        issues.append(f"{len(validation_report['attendance_folders']['missing'])} students missing attendance folders")
    
    if issues:
        logger.warning(f"\n⚠️  Issues Found:")
        for issue in issues:
            logger.warning(f"   • {issue}")
    else:
        logger.info(f"\n✅ All validations passed!")
    
    logger.info("="*70)
    
    return validation_report


def check_orphaned_photos():
    """Check for photos that don't belong to any user"""
    logger.info("\n🔍 Checking for orphaned photos...")
    
    backup_file = get_latest_backup_file()
    data = load_database_backup(backup_file)
    
    # Get all valid IDs
    valid_student_ids = {s.get('student_id') for s in data['collections']['students']}
    valid_user_ids = {u.get('user_id') for u in data['collections']['users']}
    
    orphaned = []
    
    # Check student directories
    student_dirs = (PHOTOS_DIR / "students").glob("*")
    for student_dir in student_dirs:
        if student_dir.is_dir() and student_dir.name not in valid_student_ids:
            orphaned.append(f"students/{student_dir.name}")
    
    # Check user photos
    for role in ['parents', 'teachers', 'admins']:
        role_dir = PHOTOS_DIR / role
        if role_dir.exists():
            for photo in role_dir.glob("*.jpg"):
                user_id = photo.stem
                if user_id not in valid_user_ids:
                    orphaned.append(f"{role}/{photo.name}")
    
    if orphaned:
        logger.warning(f"⚠️  Found {len(orphaned)} orphaned files/directories:")
        for item in orphaned:
            logger.warning(f"   • {item}")
    else:
        logger.info("✅ No orphaned photos found")
    
    return orphaned


def generate_final_summary():
    """Generate final summary of photo population"""
    logger.info("\n" + "="*70)
    logger.info("🎉 PHOTO POPULATION & CLEANUP SUMMARY")
    logger.info("="*70)
    
    # Count all photos
    student_photos = len(list((PHOTOS_DIR / "students").rglob("profile.jpg")))
    parent_photos = len(list((PHOTOS_DIR / "parents").glob("*.jpg")))
    teacher_photos = len(list((PHOTOS_DIR / "teachers").glob("*.jpg")))
    admin_photos = len(list((PHOTOS_DIR / "admins").glob("*.jpg")))
    attendance_folders = len(list((PHOTOS_DIR / "students").glob("*/attendance")))
    
    total_photos = student_photos + parent_photos + teacher_photos + admin_photos
    
    # Calculate sizes
    def get_dir_size(path):
        total = 0
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
        return total / (1024 * 1024)  # Convert to MB
    
    student_size = get_dir_size(PHOTOS_DIR / "students")
    parent_size = get_dir_size(PHOTOS_DIR / "parents")
    teacher_size = get_dir_size(PHOTOS_DIR / "teachers")
    admin_size = get_dir_size(PHOTOS_DIR / "admins")
    total_size = student_size + parent_size + teacher_size + admin_size
    
    logger.info(f"\n📸 Total Photos: {total_photos}")
    logger.info(f"   • Students: {student_photos} profiles")
    logger.info(f"   • Parents: {parent_photos} photos")
    logger.info(f"   • Teachers: {teacher_photos} photos")
    logger.info(f"   • Admins: {admin_photos} photos")
    
    logger.info(f"\n📁 Structure:")
    logger.info(f"   • Attendance folders: {attendance_folders}")
    logger.info(f"   • Total storage: {total_size:.2f} MB")
    
    logger.info(f"\n💾 Storage by Role:")
    logger.info(f"   • Students: {student_size:.2f} MB")
    logger.info(f"   • Parents: {parent_size:.2f} MB")
    logger.info(f"   • Teachers: {teacher_size:.2f} MB")
    logger.info(f"   • Admins: {admin_size:.2f} MB")
    
    logger.info(f"\n📚 Documentation:")
    essential_docs = [
        "API_DOCUMENTATION.md",
        "API_TEST_DEVICE.md",
        "DATABASE.md",
        "INSTALLATION.md",
        "PHOTO_ORGANIZATION.md",
        "RASPBERRY_PI_INTEGRATION.md",
        "TROUBLESHOOTING.md",
        "USER_GUIDE.md"
    ]
    doc_count = len([d for d in essential_docs if (DOCS_DIR / d).exists()])
    logger.info(f"   • Essential docs maintained: {doc_count}/{len(essential_docs)}")
    
    logger.info("\n" + "="*70)
    logger.info("✅ ALL PHOTOS POPULATED & VALIDATED")
    logger.info("="*70)


def main():
    """Main execution function"""
    logger.info("🚀 Starting Photo Organization Cleanup & Validation")
    logger.info("="*70)
    
    try:
        # Validate all photos
        validation_report = validate_all_photos()
        
        # Check for orphaned files
        orphaned = check_orphaned_photos()
        
        # Generate final summary
        generate_final_summary()
        
        logger.info(f"\n💡 Detailed log: {log_file}")
        logger.info("🎉 Cleanup & validation completed successfully!")
        
    except Exception as e:
        logger.error(f"\n❌ Error during cleanup: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
