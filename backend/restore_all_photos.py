#!/usr/bin/env python3
"""
Universal Photo Restoration Script
===================================
Restores and relinks photos for ALL entities: students, parents, teachers, admins.
Generates placeholder images via thispersondoesnotexist.com when real photos are missing.

Usage:
    python restore_all_photos.py [--verify-only] [--no-placeholders]
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys
import argparse
import requests
import time
from PIL import Image
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Directories
BACKUP_DIR = ROOT_DIR / 'backups'
PHOTO_DIR = ROOT_DIR / 'photos'

# Entity configurations: role -> (photo_dir, path_format)
ENTITY_CONFIGS = {
    'students': {
        'collection': 'students',
        'id_field': 'student_id',
        'photo_dir': PHOTO_DIR / 'students',
        'path_format': '/api/photos/students/{id}/profile.jpg',
        'file_path': lambda id: PHOTO_DIR / 'students' / id / 'profile.jpg',
        'has_subdirs': True  # Students have subdirectories
    },
    'admins': {
        'collection': 'users',
        'id_field': 'user_id',
        'query': {'role': 'admin'},
        'photo_dir': PHOTO_DIR / 'admins',
        'path_format': '/api/photos/admins/{id}.jpg',
        'file_path': lambda id: PHOTO_DIR / 'admins' / f'{id}.jpg',
        'has_subdirs': False
    },
    'teachers': {
        'collection': 'users',
        'id_field': 'user_id',
        'query': {'role': 'teacher'},
        'photo_dir': PHOTO_DIR / 'teachers',
        'path_format': '/api/photos/teachers/{id}.jpg',
        'file_path': lambda id: PHOTO_DIR / 'teachers' / f'{id}.jpg',
        'has_subdirs': False
    },
    'parents': {
        'collection': 'users',
        'id_field': 'user_id',
        'query': {'role': 'parent'},
        'photo_dir': PHOTO_DIR / 'parents',
        'path_format': '/api/photos/parents/{id}.jpg',
        'file_path': lambda id: PHOTO_DIR / 'parents' / f'{id}.jpg',
        'has_subdirs': False
    }
}


class PhotoRestoreStats:
    """Track restoration statistics"""
    def __init__(self):
        self.by_entity = {}
        self.total_processed = 0
        self.total_created = 0
        self.total_verified = 0
        self.total_generated = 0
        self.total_updated = 0
        self.errors = []
    
    def init_entity(self, entity_name: str):
        if entity_name not in self.by_entity:
            self.by_entity[entity_name] = {
                'processed': 0,
                'directories_created': 0,
                'photos_verified': 0,
                'photos_generated': 0,
                'database_updated': 0,
                'errors': 0
            }
    
    def add(self, entity_name: str, metric: str, count: int = 1):
        self.init_entity(entity_name)
        self.by_entity[entity_name][metric] += count
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print("📊 RESTORATION SUMMARY")
        print("=" * 70)
        
        for entity_name, stats in self.by_entity.items():
            print(f"\n{entity_name.upper()}:")
            print(f"   Processed: {stats['processed']}")
            print(f"   ✅ Photos verified: {stats['photos_verified']}")
            print(f"   🎨 Placeholders generated: {stats['photos_generated']}")
            print(f"   📁 Directories created: {stats['directories_created']}")
            print(f"   🔄 Database updated: {stats['database_updated']}")
            if stats['errors'] > 0:
                print(f"   ❌ Errors: {stats['errors']}")
        
        # Calculate totals
        for entity_stats in self.by_entity.values():
            self.total_processed += entity_stats['processed']
            self.total_verified += entity_stats['photos_verified']
            self.total_generated += entity_stats['photos_generated']
            self.total_updated += entity_stats['database_updated']
            self.total_created += entity_stats['directories_created']
        
        print("\n" + "-" * 70)
        print(f"TOTAL ACROSS ALL ENTITIES:")
        print(f"   Processed: {self.total_processed}")
        print(f"   ✅ Photos verified: {self.total_verified}")
        print(f"   🎨 Placeholders generated: {self.total_generated}")
        print(f"   📁 Directories created: {self.total_created}")
        print(f"   🔄 Database updated: {self.total_updated}")
        
        if self.errors:
            print(f"\n❌ Total errors: {len(self.errors)}")
            for error in self.errors[:5]:
                print(f"   - {error}")
        
        print("=" * 70)


def get_latest_backup() -> Optional[Path]:
    """Find the most recent backup file"""
    if not BACKUP_DIR.exists():
        return None
    
    backup_files = list(BACKUP_DIR.glob('seed_backup_*.json'))
    if not backup_files:
        return None
    
    backup_files.sort(reverse=True)
    return backup_files[0]


def generate_placeholder_image(entity_type: str, entity_id: str, entity_name: str) -> Optional[bytes]:
    """
    Generate a placeholder image from thispersondoesnotexist.com
    Returns image bytes or None if failed
    """
    try:
        # Use thispersondoesnotexist.com API
        url = "https://thispersondoesnotexist.com/"
        
        # Add random parameter to prevent caching
        response = requests.get(url, timeout=10, params={'t': time.time()})
        
        if response.status_code == 200:
            # Verify it's a valid image
            img = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as JPEG
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            return output.getvalue()
        
        return None
    
    except Exception as e:
        print(f"      ⚠️  Failed to generate placeholder: {str(e)}")
        return None


def save_placeholder_image(file_path: Path, entity_type: str, entity_id: str, entity_name: str) -> bool:
    """
    Generate and save a placeholder image
    Returns True if successful
    """
    image_bytes = generate_placeholder_image(entity_type, entity_id, entity_name)
    
    if image_bytes:
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save the image
            with open(file_path, 'wb') as f:
                f.write(image_bytes)
            
            return True
        except Exception as e:
            print(f"      ❌ Failed to save placeholder: {str(e)}")
            return False
    
    return False


def ensure_directory_structure(entity_config: Dict, entity_id: str, stats: PhotoRestoreStats, entity_name: str) -> Path:
    """
    Ensure directory structure exists for an entity
    """
    photo_dir = entity_config['photo_dir']
    
    if entity_config['has_subdirs']:
        # Students: /photos/students/{student_id}/
        entity_dir = photo_dir / entity_id
        attendance_dir = entity_dir / 'attendance'
        
        if not entity_dir.exists():
            entity_dir.mkdir(parents=True, exist_ok=True)
            stats.add(entity_name, 'directories_created')
        
        if not attendance_dir.exists():
            attendance_dir.mkdir(parents=True, exist_ok=True)
        
        return entity_dir
    else:
        # Other entities: /photos/teachers/, /photos/parents/, etc.
        if not photo_dir.exists():
            photo_dir.mkdir(parents=True, exist_ok=True)
            stats.add(entity_name, 'directories_created')
        
        return photo_dir


async def restore_entity_photos(
    entity_name: str,
    entity_config: Dict,
    backup_data: Dict,
    stats: PhotoRestoreStats,
    generate_placeholders: bool = True
) -> None:
    """
    Restore photos for a specific entity type
    """
    print(f"\n{'=' * 70}")
    print(f"📸 PROCESSING {entity_name.upper()}")
    print(f"{'=' * 70}")
    
    # Get entities from backup or database
    if entity_name == 'students':
        entities = backup_data.get('collections', {}).get('students', [])
        collection = db.students
    else:
        # For users (admins, teachers, parents)
        entities = [
            u for u in backup_data.get('collections', {}).get('users', [])
            if u.get('role') == entity_name.rstrip('s')  # Remove plural
        ]
        collection = db.users
    
    if not entities:
        print(f"⚠️  No {entity_name} found in backup")
        return
    
    print(f"📚 Found {len(entities)} {entity_name} in backup\n")
    
    # Ensure base directory exists
    entity_config['photo_dir'].mkdir(parents=True, exist_ok=True)
    
    # Process each entity
    for idx, entity in enumerate(entities, 1):
        entity_id = entity.get(entity_config['id_field'])
        entity_display_name = entity.get('name', 'Unknown')
        
        print(f"[{idx}/{len(entities)}] {entity_display_name} ({entity_id[:20]}...)")
        stats.add(entity_name, 'processed')
        
        if not entity_id:
            print(f"   ⚠️  Skipping - no ID field")
            stats.errors.append(f"{entity_name}: {entity_display_name} - no ID")
            stats.add(entity_name, 'errors')
            continue
        
        # Step 1: Ensure directory structure
        ensure_directory_structure(entity_config, entity_id, stats, entity_name)
        
        # Step 2: Get file path
        file_path = entity_config['file_path'](entity_id)
        
        # Step 3: Check if photo exists
        photo_exists = file_path.exists()
        
        if photo_exists:
            # Verify it's a valid image
            try:
                img = Image.open(file_path)
                img.verify()
                stats.add(entity_name, 'photos_verified')
                print(f"   ✅ Photo verified")
            except Exception as e:
                print(f"   ⚠️  Photo corrupted, regenerating...")
                photo_exists = False
        
        # Step 4: Generate placeholder if missing
        if not photo_exists and generate_placeholders:
            print(f"   🎨 Generating placeholder from thispersondoesnotexist.com...")
            if save_placeholder_image(file_path, entity_name, entity_id, entity_display_name):
                stats.add(entity_name, 'photos_generated')
                print(f"   ✅ Placeholder generated successfully")
            else:
                print(f"   ❌ Failed to generate placeholder")
                stats.errors.append(f"{entity_name}: {entity_display_name} - placeholder generation failed")
                stats.add(entity_name, 'errors')
        elif not photo_exists:
            print(f"   ⚠️  Photo missing (placeholder generation disabled)")
        
        # Step 5: Get correct photo path for database
        correct_path = entity_config['path_format'].format(id=entity_id)
        
        # Step 6: Update database if needed
        query = {entity_config['id_field']: entity_id}
        if entity_name != 'students':
            query['role'] = entity_name.rstrip('s')
        
        db_entity = await collection.find_one(query)
        
        if db_entity:
            current_path = db_entity.get('photo')
            if current_path != correct_path:
                try:
                    await collection.update_one(
                        query,
                        {"$set": {"photo": correct_path}}
                    )
                    stats.add(entity_name, 'database_updated')
                    print(f"   🔄 Database updated: {correct_path}")
                except Exception as e:
                    error_msg = f"{entity_name}: {entity_display_name} - DB update failed: {str(e)}"
                    stats.errors.append(error_msg)
                    stats.add(entity_name, 'errors')
                    print(f"   ❌ {error_msg}")
        else:
            print(f"   ⚠️  Not found in database")
            stats.errors.append(f"{entity_name}: {entity_display_name} - not in database")
            stats.add(entity_name, 'errors')


async def restore_attendance_photos(stats: PhotoRestoreStats, generate_placeholders: bool = True) -> None:
    """
    Restore attendance photos from database records
    Generates placeholders for missing attendance scan photos
    """
    print(f"\n{'=' * 70}")
    print(f"📸 PROCESSING ATTENDANCE PHOTOS")
    print(f"{'=' * 70}")
    
    entity_name = 'attendance'
    stats.init_entity(entity_name)
    
    # Get all attendance records with scan photos
    attendance_records = await db.attendance.find(
        {'scan_photo': {'$exists': True, '$ne': None}}
    ).to_list(None)
    
    if not attendance_records:
        print("⚠️  No attendance records with photos found")
        return
    
    print(f"📚 Found {len(attendance_records)} attendance records with photos\n")
    
    # Process each attendance record
    for idx, record in enumerate(attendance_records, 1):
        student_id = record.get('student_id')
        date = record.get('date')
        trip = record.get('trip')
        scan_photo = record.get('scan_photo')
        
        if not student_id or not scan_photo:
            continue
        
        stats.add(entity_name, 'processed')
        
        # Parse photo path to get file location
        # Expected format: /api/photos/students/{student_id}/attendance/{date}_{trip}.jpg
        try:
            # Extract file path from API path
            if scan_photo.startswith('/api/photos/'):
                relative_path = scan_photo.replace('/api/photos/', '')
                file_path = PHOTO_DIR / relative_path
            else:
                continue
            
            # Check if photo exists
            photo_exists = file_path.exists()
            
            if photo_exists:
                # Verify it's a valid image
                try:
                    img = Image.open(file_path)
                    img.verify()
                    stats.add(entity_name, 'photos_verified')
                    if idx % 10 == 0:  # Print every 10th to avoid spam
                        print(f"   [{idx}/{len(attendance_records)}] ✅ Verified")
                except Exception as e:
                    print(f"   [{idx}/{len(attendance_records)}] ⚠️  Corrupted, regenerating...")
                    photo_exists = False
            
            # Generate placeholder if missing
            if not photo_exists and generate_placeholders:
                print(f"   [{idx}/{len(attendance_records)}] 🎨 Generating placeholder for {date} {trip}...")
                if save_placeholder_image(file_path, 'attendance', student_id, f'{date}_{trip}'):
                    stats.add(entity_name, 'photos_generated')
                    print(f"      ✅ Placeholder generated")
                else:
                    print(f"      ❌ Failed to generate placeholder")
                    stats.add(entity_name, 'errors')
            elif not photo_exists:
                if idx % 10 == 0:
                    print(f"   [{idx}/{len(attendance_records)}] ⚠️  Photo missing (placeholder generation disabled)")
        
        except Exception as e:
            error_msg = f"Attendance {student_id} {date} {trip}: {str(e)}"
            stats.errors.append(error_msg)
            stats.add(entity_name, 'errors')
    
    print(f"\n✅ Processed {len(attendance_records)} attendance photos")


async def restore_all_photos(backup_path: Optional[Path] = None, generate_placeholders: bool = True) -> PhotoRestoreStats:
    """
    Main restoration function for all entities
    """
    stats = PhotoRestoreStats()
    
    print("\n" + "=" * 70)
    print("🔄 UNIVERSAL PHOTO RESTORATION & RELINK")
    print("=" * 70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Find backup file
    if backup_path is None:
        backup_path = get_latest_backup()
    
    if not backup_path or not backup_path.exists():
        print("❌ No backup file found!")
        stats.errors.append("No backup file found")
        return stats
    
    print(f"\n📦 Loading backup: {backup_path.name}")
    
    # Load backup data
    try:
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load backup: {str(e)}")
        stats.errors.append(f"Failed to load backup: {str(e)}")
        return stats
    
    # Process each entity type
    for entity_name, entity_config in ENTITY_CONFIGS.items():
        try:
            await restore_entity_photos(entity_name, entity_config, backup_data, stats, generate_placeholders)
        except Exception as e:
            error_msg = f"Failed to process {entity_name}: {str(e)}"
            print(f"\n❌ {error_msg}")
            stats.errors.append(error_msg)
    
    # Process attendance photos
    try:
        await restore_attendance_photos(stats, generate_placeholders)
    except Exception as e:
        error_msg = f"Failed to process attendance photos: {str(e)}"
        print(f"\n❌ {error_msg}")
        stats.errors.append(error_msg)
    
    # Print summary
    stats.print_summary()
    
    return stats


async def verify_all_photos():
    """
    Verification function - checks all entities and reports issues
    """
    print("\n" + "=" * 70)
    print("🔍 UNIVERSAL PHOTO VERIFICATION")
    print("=" * 70)
    
    total_issues = 0
    
    for entity_name, entity_config in ENTITY_CONFIGS.items():
        print(f"\n{entity_name.upper()}:")
        
        # Get entities from database
        collection = db[entity_config['collection']]
        query = entity_config.get('query', {})
        entities = await collection.find(query).to_list(None)
        
        print(f"   Checking {len(entities)} {entity_name}...")
        
        issues = []
        
        for entity in entities:
            entity_id = entity.get(entity_config['id_field'])
            entity_name_display = entity.get('name', 'Unknown')
            photo_path = entity.get('photo')
            
            # Check if photo path is set
            if not photo_path:
                issues.append(f"❌ {entity_name_display}: No photo path in database")
                continue
            
            # Check if photo path is correct format
            expected_path = entity_config['path_format'].format(id=entity_id)
            if photo_path != expected_path:
                issues.append(f"⚠️  {entity_name_display}: Incorrect path - {photo_path}")
            
            # Check if actual file exists
            file_path = entity_config['file_path'](entity_id)
            if not file_path.exists():
                issues.append(f"⚠️  {entity_name_display}: File missing")
        
        if issues:
            print(f"   ⚠️  Found {len(issues)} issues:")
            for issue in issues[:3]:
                print(f"      {issue}")
            if len(issues) > 3:
                print(f"      ... and {len(issues) - 3} more")
            total_issues += len(issues)
        else:
            print(f"   ✅ All photos properly linked!")
    
    print("\n" + "=" * 70)
    if total_issues == 0:
        print("✅ ALL PHOTOS ARE PROPERLY LINKED ACROSS ALL ENTITIES!")
    else:
        print(f"⚠️  Total issues found: {total_issues}")
        print("Run without --verify-only to fix these issues")
    print("=" * 70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Restore and relink photos for all entities (students, teachers, parents, admins)'
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
    parser.add_argument(
        '--no-placeholders',
        action='store_true',
        help='Do not generate placeholder images for missing photos'
    )
    
    args = parser.parse_args()
    
    backup_path = Path(args.backup_file) if args.backup_file else None
    
    if args.verify_only:
        asyncio.run(verify_all_photos())
    else:
        generate_placeholders = not args.no_placeholders
        asyncio.run(restore_all_photos(backup_path, generate_placeholders))


if __name__ == "__main__":
    main()
