#!/usr/bin/env python3
"""
Orphaned Photo Migration Script
================================
This script helps migrate photos from old student directories to new ones.
Useful when student_ids change but photo files still exist.

It can:
1. List all orphaned photo directories (not in current database)
2. Attempt to match orphaned photos to current students by name/index
3. Copy photos from old directories to new ones

Usage:
    python migrate_orphaned_photos.py --list        # List orphaned directories
    python migrate_orphaned_photos.py --migrate     # Migrate by index matching
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import shutil
from typing import List, Dict
import argparse

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Directories
PHOTO_DIR = ROOT_DIR / 'photos'
STUDENT_PHOTO_DIR = PHOTO_DIR / 'students'


async def get_current_student_ids() -> List[str]:
    """Get list of student_ids currently in database"""
    students = await db.students.find({}, {"student_id": 1}).to_list(None)
    return [s['student_id'] for s in students]


def get_photo_directories() -> List[Path]:
    """Get all student photo directories from filesystem"""
    if not STUDENT_PHOTO_DIR.exists():
        return []
    return [d for d in STUDENT_PHOTO_DIR.iterdir() if d.is_dir()]


async def find_orphaned_directories() -> List[Path]:
    """
    Find photo directories that don't correspond to any current student
    """
    current_ids = await get_current_student_ids()
    all_dirs = get_photo_directories()
    
    orphaned = []
    for dir_path in all_dirs:
        dir_name = dir_path.name
        if dir_name not in current_ids:
            orphaned.append(dir_path)
    
    return orphaned


async def list_orphaned_photos():
    """
    List all orphaned photo directories
    """
    print("\n" + "=" * 70)
    print("🔍 ORPHANED PHOTO DIRECTORIES")
    print("=" * 70)
    
    orphaned = await find_orphaned_directories()
    
    if not orphaned:
        print("✅ No orphaned directories found!")
        return
    
    print(f"⚠️  Found {len(orphaned)} orphaned directories:\n")
    
    for idx, dir_path in enumerate(orphaned, 1):
        dir_name = dir_path.name
        profile_photo = dir_path / 'profile.jpg'
        has_photo = profile_photo.exists()
        
        photo_status = "✅ Has profile.jpg" if has_photo else "❌ No profile.jpg"
        print(f"[{idx}] {dir_name}")
        print(f"    {photo_status}")
        
        # Check attendance photos
        attendance_dir = dir_path / 'attendance'
        if attendance_dir.exists():
            attendance_photos = list(attendance_dir.glob('*.jpg'))
            if attendance_photos:
                print(f"    📸 {len(attendance_photos)} attendance photo(s)")
    
    print("\n" + "=" * 70)


async def migrate_photos_by_index():
    """
    Migrate orphaned photos to current students by matching index order
    Assumes orphaned photos are from a previous seed with same order
    """
    print("\n" + "=" * 70)
    print("🔄 MIGRATING ORPHANED PHOTOS (BY INDEX)")
    print("=" * 70)
    
    # Get current students (ordered)
    students = await db.students.find().sort("name", 1).to_list(None)
    
    # Get orphaned directories (sorted)
    orphaned = await find_orphaned_directories()
    orphaned_with_photos = [d for d in orphaned if (d / 'profile.jpg').exists()]
    orphaned_with_photos.sort()
    
    print(f"📚 Current students: {len(students)}")
    print(f"📁 Orphaned directories with photos: {len(orphaned_with_photos)}")
    
    if len(orphaned_with_photos) == 0:
        print("\n⚠️  No orphaned photos to migrate")
        return
    
    # Try to match count
    migrate_count = min(len(students), len(orphaned_with_photos))
    
    print(f"\n🔄 Will attempt to migrate {migrate_count} photos...\n")
    
    migrated = 0
    errors = 0
    
    for idx in range(migrate_count):
        student = students[idx]
        old_dir = orphaned_with_photos[idx]
        
        student_id = student['student_id']
        student_name = student['name']
        new_dir = STUDENT_PHOTO_DIR / student_id
        
        print(f"[{idx + 1}/{migrate_count}] {student_name}")
        print(f"   From: {old_dir.name}")
        print(f"   To:   {student_id}")
        
        try:
            # Ensure new directory exists
            new_dir.mkdir(parents=True, exist_ok=True)
            (new_dir / 'attendance').mkdir(exist_ok=True)
            
            # Copy profile photo
            old_photo = old_dir / 'profile.jpg'
            new_photo = new_dir / 'profile.jpg'
            
            if old_photo.exists():
                shutil.copy2(old_photo, new_photo)
                print(f"   ✅ Copied profile.jpg")
                migrated += 1
            
            # Copy attendance photos
            old_attendance = old_dir / 'attendance'
            new_attendance = new_dir / 'attendance'
            
            if old_attendance.exists():
                attendance_photos = list(old_attendance.glob('*.jpg'))
                for photo in attendance_photos:
                    dest = new_attendance / photo.name
                    shutil.copy2(photo, dest)
                if attendance_photos:
                    print(f"   ✅ Copied {len(attendance_photos)} attendance photo(s)")
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            errors += 1
    
    print("\n" + "=" * 70)
    print("📊 MIGRATION SUMMARY")
    print("=" * 70)
    print(f"✅ Successfully migrated: {migrated}")
    print(f"❌ Errors: {errors}")
    print("=" * 70)
    
    if migrated > 0:
        print("\n💡 Run restore_student_photos.py to verify and update database links")


async def clean_orphaned_directories(confirm: bool = False):
    """
    Remove orphaned photo directories
    WARNING: This deletes data!
    """
    print("\n" + "=" * 70)
    print("🗑️  CLEAN ORPHANED DIRECTORIES")
    print("=" * 70)
    
    orphaned = await find_orphaned_directories()
    
    if not orphaned:
        print("✅ No orphaned directories to clean")
        return
    
    print(f"⚠️  Found {len(orphaned)} orphaned directories")
    
    if not confirm:
        print("\n❌ This is a DRY RUN. Use --confirm to actually delete.")
        print("   The following directories would be deleted:\n")
        for dir_path in orphaned:
            print(f"   - {dir_path.name}")
        return
    
    print("\n🗑️  Deleting orphaned directories...")
    
    deleted = 0
    for dir_path in orphaned:
        try:
            shutil.rmtree(dir_path)
            print(f"   ✅ Deleted: {dir_path.name}")
            deleted += 1
        except Exception as e:
            print(f"   ❌ Error deleting {dir_path.name}: {str(e)}")
    
    print(f"\n✅ Deleted {deleted} orphaned directories")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Manage orphaned student photo directories'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all orphaned photo directories'
    )
    parser.add_argument(
        '--migrate',
        action='store_true',
        help='Migrate orphaned photos to current students (by index)'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Remove orphaned directories (use with --confirm)'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirm destructive operations'
    )
    
    args = parser.parse_args()
    
    if args.list:
        asyncio.run(list_orphaned_photos())
    elif args.migrate:
        asyncio.run(migrate_photos_by_index())
    elif args.clean:
        asyncio.run(clean_orphaned_directories(args.confirm))
    else:
        print("Usage: python migrate_orphaned_photos.py [--list|--migrate|--clean]")
        print("Run with -h for more help")


if __name__ == "__main__":
    main()
