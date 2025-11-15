"""
Smart Backup System with Automatic Rotation
Exports database collections to JSON and maintains only N most recent backups
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
BACKUP_DIR = ROOT_DIR / 'backups'
BACKUP_LIMIT = int(os.environ.get('BACKUP_LIMIT', '3'))

# Collections to backup (excluding dynamic data)
# Note: users and students collections use 'photo' field (not 'photo_path')
# Photo field contains accessible URLs like '/api/photos/students/{id}/profile.jpg'
COLLECTIONS_TO_BACKUP = [
    'users',
    'students', 
    'buses',
    'routes',
    'stops',
    'holidays',
    'device_keys'
]


def ensure_backup_directory():
    """Create backups directory if it doesn't exist"""
    BACKUP_DIR.mkdir(exist_ok=True)
    print(f"📁 Backup directory ready: {BACKUP_DIR}")


def get_backup_files() -> List[Path]:
    """Get all backup files sorted by timestamp (newest first)"""
    if not BACKUP_DIR.exists():
        return []
    
    backup_files = list(BACKUP_DIR.glob('seed_backup_*.json'))
    # Sort by filename (which includes timestamp) in descending order
    backup_files.sort(reverse=True)
    return backup_files


def rotate_backups():
    """Delete old backups, keeping only BACKUP_LIMIT most recent files"""
    backup_files = get_backup_files()
    
    if len(backup_files) <= BACKUP_LIMIT:
        print(f"✅ Current backups: {len(backup_files)}/{BACKUP_LIMIT} (no rotation needed)")
        return
    
    # Delete excess backups
    files_to_delete = backup_files[BACKUP_LIMIT:]
    print(f"\n🔄 Rotating backups: keeping {BACKUP_LIMIT} most recent, deleting {len(files_to_delete)} old file(s)")
    
    for backup_file in files_to_delete:
        try:
            backup_file.unlink()
            print(f"   🗑️  Deleted: {backup_file.name}")
        except Exception as e:
            print(f"   ⚠️  Failed to delete {backup_file.name}: {e}")
    
    print(f"✅ Backup rotation complete: {len(get_backup_files())}/{BACKUP_LIMIT} backups remaining")


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


async def create_backup():
    """Create a new backup file with timestamp"""
    print("\n" + "=" * 60)
    print("💾 CREATING DATABASE BACKUP")
    print("=" * 60)
    
    ensure_backup_directory()
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    backup_filename = f"seed_backup_{timestamp}.json"
    backup_path = BACKUP_DIR / backup_filename
    
    # Export all collections
    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'collections': {}
    }
    
    print("\n📦 Exporting collections:")
    for collection_name in COLLECTIONS_TO_BACKUP:
        try:
            documents = await export_collection(collection_name)
            backup_data['collections'][collection_name] = documents
            print(f"   ✅ {collection_name}: {len(documents)} document(s)")
        except Exception as e:
            print(f"   ⚠️  {collection_name}: Export failed - {e}")
            backup_data['collections'][collection_name] = []
    
    # Save to JSON file
    try:
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        print(f"\n✅ Backup created successfully: {backup_filename}")
        print(f"   📍 Location: {backup_path}")
        
        file_size = backup_path.stat().st_size / 1024  # KB
        print(f"   📊 Size: {file_size:.2f} KB")
    except Exception as e:
        print(f"\n❌ Failed to save backup: {e}")
        raise
    
    # Rotate old backups
    rotate_backups()
    
    return backup_filename


async def main():
    """Main execution function"""
    try:
        print("\n🔧 Backup Configuration:")
        print(f"   • Backup Limit: {BACKUP_LIMIT} file(s)")
        print(f"   • Backup Directory: {BACKUP_DIR}")
        
        backup_filename = await create_backup()
        
        print("\n" + "=" * 60)
        print("✅ BACKUP PROCESS COMPLETED")
        print("=" * 60)
        
        # Show current backups
        backup_files = get_backup_files()
        if backup_files:
            print(f"\n📋 Current backups ({len(backup_files)}/{BACKUP_LIMIT}):")
            for i, backup_file in enumerate(backup_files, 1):
                print(f"   {i}. {backup_file.name}")
        
    except Exception as e:
        print(f"\n❌ BACKUP FAILED: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
