"""
Attendance-Specific Backup System with Automatic Rotation
Exports attendance-related collections to JSON and maintains only N most recent backups
Includes: attendance, events (scan events), and attendance photo references
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import List, Dict, Any

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Backup configuration
ATTENDANCE_BACKUP_DIR = ROOT_DIR / 'backups' / 'attendance'
BACKUP_LIMIT = int(os.environ.get('BACKUP_LIMIT', '3'))

# Collections to backup (attendance-specific only)
ATTENDANCE_COLLECTIONS = [
    'attendance',  # Main attendance records
    'events'       # Scan events
]


def ensure_backup_directory():
    """Create attendance backups directory if it doesn't exist"""
    ATTENDANCE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Attendance backup directory ready: {ATTENDANCE_BACKUP_DIR}")


def get_backup_files() -> List[Path]:
    """Get all attendance backup files sorted by timestamp (newest first)"""
    if not ATTENDANCE_BACKUP_DIR.exists():
        return []
    
    backup_files = list(ATTENDANCE_BACKUP_DIR.glob('attendance_backup_*.json'))
    # Sort by filename (which includes timestamp) in descending order
    backup_files.sort(reverse=True)
    return backup_files


def rotate_backups():
    """Delete old backups, keeping only BACKUP_LIMIT most recent files"""
    backup_files = get_backup_files()
    
    if len(backup_files) <= BACKUP_LIMIT:
        print(f"✅ Current attendance backups: {len(backup_files)}/{BACKUP_LIMIT} (no rotation needed)")
        return
    
    # Delete excess backups
    files_to_delete = backup_files[BACKUP_LIMIT:]
    print(f"\n🔄 Rotating attendance backups: keeping {BACKUP_LIMIT} most recent, deleting {len(files_to_delete)} old file(s)")
    
    for backup_file in files_to_delete:
        try:
            backup_file.unlink()
            print(f"   🗑️  Deleted: {backup_file.name}")
        except Exception as e:
            print(f"   ⚠️  Failed to delete {backup_file.name}: {e}")
    
    print(f"✅ Attendance backup rotation complete: {len(get_backup_files())}/{BACKUP_LIMIT} backups remaining")


async def export_collection(collection_name: str) -> List[Dict[str, Any]]:
    """Export all documents from a collection"""
    documents = []
    cursor = db[collection_name].find({})
    
    async for doc in cursor:
        # Convert ObjectId to string if present
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        documents.append(doc)
    
    return documents


async def collect_attendance_photo_references() -> Dict[str, Any]:
    """Collect all photo references from attendance records"""
    photo_refs = {
        'scan_photos': [],
        'student_attendance_folders': []
    }
    
    # Get unique scan photos from attendance records
    cursor = db.attendance.find({"scan_photo": {"$exists": True, "$ne": None}})
    async for record in cursor:
        if record.get('scan_photo'):
            photo_refs['scan_photos'].append({
                'attendance_id': record.get('attendance_id'),
                'student_id': record.get('student_id'),
                'date': record.get('date'),
                'photo_url': record.get('scan_photo')
            })
    
    # Get student attendance folders from students collection
    cursor = db.students.find({"attendance_path": {"$exists": True, "$ne": None}})
    async for student in cursor:
        if student.get('attendance_path'):
            photo_refs['student_attendance_folders'].append({
                'student_id': student.get('student_id'),
                'attendance_path': student.get('attendance_path')
            })
    
    return photo_refs


async def create_backup():
    """Create a new attendance backup file with timestamp"""
    print("\n" + "=" * 60)
    print("📸 CREATING ATTENDANCE-SPECIFIC BACKUP")
    print("=" * 60)
    
    ensure_backup_directory()
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    backup_filename = f"attendance_backup_{timestamp}.json"
    backup_path = ATTENDANCE_BACKUP_DIR / backup_filename
    
    # Export all attendance collections
    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'backup_type': 'attendance',
        'collections': {},
        'photo_references': {}
    }
    
    print("\n📦 Exporting attendance collections:")
    for collection_name in ATTENDANCE_COLLECTIONS:
        try:
            documents = await export_collection(collection_name)
            backup_data['collections'][collection_name] = documents
            print(f"   ✅ {collection_name}: {len(documents)} document(s)")
        except Exception as e:
            print(f"   ⚠️  {collection_name}: Export failed - {e}")
            backup_data['collections'][collection_name] = []
    
    # Collect attendance photo references
    print("\n📸 Collecting attendance photo references:")
    try:
        photo_refs = await collect_attendance_photo_references()
        backup_data['photo_references'] = photo_refs
        print(f"   ✅ Scan photos: {len(photo_refs['scan_photos'])} reference(s)")
        print(f"   ✅ Attendance folders: {len(photo_refs['student_attendance_folders'])} folder(s)")
    except Exception as e:
        print(f"   ⚠️  Photo reference collection failed - {e}")
        backup_data['photo_references'] = {'scan_photos': [], 'student_attendance_folders': []}
    
    # Save to JSON file
    try:
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        print(f"\n✅ Attendance backup created successfully: {backup_filename}")
        print(f"   📍 Location: {backup_path}")
        
        file_size = backup_path.stat().st_size / 1024  # KB
        print(f"   📊 Size: {file_size:.2f} KB")
    except Exception as e:
        print(f"\n❌ Failed to save attendance backup: {e}")
        raise
    
    # Rotate old backups
    rotate_backups()
    
    return backup_filename


async def main():
    """Main execution function"""
    try:
        print("\n🔧 Attendance Backup Configuration:")
        print(f"   • Backup Limit: {BACKUP_LIMIT} file(s)")
        print(f"   • Backup Directory: {ATTENDANCE_BACKUP_DIR}")
        
        backup_filename = await create_backup()
        
        print("\n" + "=" * 60)
        print("✅ ATTENDANCE BACKUP PROCESS COMPLETED")
        print("=" * 60)
        
        # Show current backups
        backup_files = get_backup_files()
        if backup_files:
            print(f"\n📋 Current attendance backups ({len(backup_files)}/{BACKUP_LIMIT}):")
            for i, backup_file in enumerate(backup_files, 1):
                print(f"   {i}. {backup_file.name}")
        
    except Exception as e:
        print(f"\n❌ ATTENDANCE BACKUP FAILED: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
