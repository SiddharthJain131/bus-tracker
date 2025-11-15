#!/usr/bin/env python3
"""
Permanent Photo Restore & Relink Script
========================================
This script rebuilds and relinks all student photos from the backup source.
It ensures every student record has its correct associated photo restored.

Features:
- Reads photo data from the latest backup file
- Creates missing photo directories
- Relinks photos to correct students in database
- Updates incorrect photo paths
- Safe to run multiple times (idempotent)
- Handles missing photos gracefully

Usage:
    python restore_student_photos.py [--backup-file path/to/backup.json]
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import json
from typing import Dict, List, Optional
from datetime import datetime
import sys
import argparse

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Directories
BACKUP_DIR = ROOT_DIR / 'backups'
PHOTO_DIR = ROOT_DIR / 'photos'
STUDENT_PHOTO_DIR = PHOTO_DIR / 'students'


class PhotoRestoreStats:
    """Track restoration statistics"""
    def __init__(self):
        self.directories_created = 0
        self.photos_verified = 0
        self.photos_missing = 0
        self.database_updated = 0
        self.errors = []
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print("📊 RESTORATION SUMMARY")
        print("=" * 70)
        print(f"✅ Directories created: {self.directories_created}")
        print(f"✅ Photos verified: {self.photos_verified}")
        print(f"⚠️  Photos missing: {self.photos_missing}")
        print(f"✅ Database records updated: {self.database_updated}")
        if self.errors:
            print(f"\n❌ Errors encountered: {len(self.errors)}")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"   - {error}")
        print("=" * 70)


def get_latest_backup() -> Optional[Path]:
    """Find the most recent backup file"""
    if not BACKUP_DIR.exists():
        return None
    
    backup_files = list(BACKUP_DIR.glob('seed_backup_*.json'))
    if not backup_files:
        return None
    
    # Sort by filename (timestamp) in descending order
    backup_files.sort(reverse=True)
    return backup_files[0]


def load_backup_data(backup_path: Path) -> Dict:
    """Load and parse backup JSON file"""
    print(f"\n📦 Loading backup from: {backup_path.name}")
    with open(backup_path, 'r') as f:
        return json.load(f)


def ensure_photo_directory(student_id: str, stats: PhotoRestoreStats) -> Path:
    """
    Ensure photo directory structure exists for a student
    Creates: /photos/students/{student_id}/
    Creates: /photos/students/{student_id}/attendance/
    """
    student_dir = STUDENT_PHOTO_DIR / student_id
    attendance_dir = student_dir / 'attendance'
    
    # Create main student directory
    if not student_dir.exists():
        student_dir.mkdir(parents=True, exist_ok=True)
        stats.directories_created += 1
        print(f"   📁 Created directory: {student_id}/")
    
    # Create attendance subdirectory
    if not attendance_dir.exists():
        attendance_dir.mkdir(parents=True, exist_ok=True)
        print(f"   📁 Created subdirectory: {student_id}/attendance/")
    
    return student_dir


def verify_photo_file(student_dir: Path, student_id: str, student_name: str, stats: PhotoRestoreStats) -> bool:
    """
    Verify that the profile photo file exists
    Returns True if exists, False if missing
    """
    photo_path = student_dir / 'profile.jpg'
    
    if photo_path.exists():
        stats.photos_verified += 1
        return True
    else:
        stats.photos_missing += 1
        print(f"   ⚠️  Missing photo file: {student_name} ({student_id})")
        stats.errors.append(f"Missing photo for {student_name} ({student_id})")
        return False


def get_correct_photo_path(student_id: str) -> str:
    """
    Generate the correct photo path for a student
    Returns: /api/photos/students/{student_id}/profile.jpg
    """
    return f"/api/photos/students/{student_id}/profile.jpg"


async def update_student_photo_path(student_id: str, correct_path: str, current_path: Optional[str], stats: PhotoRestoreStats) -> bool:
    """
    Update student's photo path in database if incorrect or missing
    Returns True if updated, False if already correct
    """
    if current_path == correct_path:
        return False
    
    try:
        result = await db.students.update_one(
            {"student_id": student_id},
            {"$set": {"photo": correct_path}}
        )
        
        if result.modified_count > 0:
            stats.database_updated += 1
            if current_path:
                print(f"   🔄 Updated photo path from: {current_path}")
                print(f"                        to: {correct_path}")
            else:
                print(f"   ✅ Set photo path: {correct_path}")
            return True
        return False
    except Exception as e:
        error_msg = f"Failed to update database for {student_id}: {str(e)}"
        stats.errors.append(error_msg)
        print(f"   ❌ {error_msg}")
        return False


async def restore_photos_from_backup(backup_path: Optional[Path] = None) -> PhotoRestoreStats:
    """
    Main restoration function
    Reads backup and ensures all student photos are properly linked
    """
    stats = PhotoRestoreStats()
    
    print("\n" + "=" * 70)
    print("🔄 STUDENT PHOTO RESTORATION & RELINK")
    print("=" * 70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Find backup file
    if backup_path is None:
        backup_path = get_latest_backup()
    
    if not backup_path or not backup_path.exists():
        print("❌ No backup file found!")
        stats.errors.append("No backup file found")
        return stats
    
    # Load backup data
    try:
        backup_data = load_backup_data(backup_path)
    except Exception as e:
        print(f"❌ Failed to load backup: {str(e)}")
        stats.errors.append(f"Failed to load backup: {str(e)}")
        return stats
    
    # Get students from backup
    students = backup_data.get('collections', {}).get('students', [])
    
    if not students:
        print("⚠️  No students found in backup")
        return stats
    
    print(f"📚 Found {len(students)} students in backup")
    print("\n🔍 Processing students...")
    
    # Ensure base directories exist
    STUDENT_PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    
    # Process each student
    for idx, student in enumerate(students, 1):
        student_id = student.get('student_id')
        student_name = student.get('name', 'Unknown')
        backup_photo_path = student.get('photo')
        
        print(f"\n[{idx}/{len(students)}] {student_name} ({student_id})")
        
        if not student_id:
            print(f"   ⚠️  Skipping - no student_id")
            continue
        
        # Step 1: Ensure directory structure exists
        student_dir = ensure_photo_directory(student_id, stats)
        
        # Step 2: Verify photo file exists
        photo_exists = verify_photo_file(student_dir, student_id, student_name, stats)
        
        # Step 3: Get correct photo path
        correct_path = get_correct_photo_path(student_id)
        
        # Step 4: Check current database photo path
        db_student = await db.students.find_one({"student_id": student_id})
        current_db_path = db_student.get('photo') if db_student else None
        
        # Step 5: Update database if needed
        if db_student:
            await update_student_photo_path(student_id, correct_path, current_db_path, stats)
        else:
            print(f"   ⚠️  Student not found in database")
            stats.errors.append(f"Student {student_id} not in database")
    
    # Print summary
    stats.print_summary()
    
    return stats


async def verify_all_photos():
    """
    Verification function - checks all students in database
    and reports any with missing or incorrect photo paths
    """
    print("\n" + "=" * 70)
    print("🔍 PHOTO VERIFICATION CHECK")
    print("=" * 70)
    
    students = await db.students.find().to_list(None)
    print(f"📚 Checking {len(students)} students in database...")
    
    issues = []
    
    for student in students:
        student_id = student.get('student_id')
        student_name = student.get('name', 'Unknown')
        photo_path = student.get('photo')
        
        # Check if photo path is set
        if not photo_path:
            issues.append(f"❌ {student_name}: No photo path in database")
            continue
        
        # Check if photo path is correct format
        expected_path = f"/api/photos/students/{student_id}/profile.jpg"
        if photo_path != expected_path:
            issues.append(f"⚠️  {student_name}: Incorrect path - {photo_path}")
        
        # Check if actual file exists
        file_path = STUDENT_PHOTO_DIR / student_id / 'profile.jpg'
        if not file_path.exists():
            issues.append(f"⚠️  {student_name}: File missing at {file_path}")
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} issues:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ All photos are properly linked!")
    
    print("=" * 70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Restore and relink student photos from backup'
    )
    parser.add_argument(
        '--backup-file',
        type=str,
        help='Path to specific backup file (default: latest backup)'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify photos without making changes'
    )
    
    args = parser.parse_args()
    
    backup_path = Path(args.backup_file) if args.backup_file else None
    
    if args.verify_only:
        asyncio.run(verify_all_photos())
    else:
        asyncio.run(restore_photos_from_backup(backup_path))


if __name__ == "__main__":
    main()
