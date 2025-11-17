"""
Enhanced Backup Manager with Integrity Checks, Metadata, and Status Tracking
Production-ready backup system with SHA256 checksums and comprehensive monitoring
"""

import asyncio
import json
import os
import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

# Backup configuration
BACKUP_DIR = ROOT_DIR / 'backups'
ATTENDANCE_BACKUP_DIR = BACKUP_DIR / 'attendance'
BACKUP_LIMIT = int(os.environ.get('BACKUP_LIMIT', '5'))  # Keep 5 most recent
BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))  # Keep for 30 days
MIN_STORAGE_MB = int(os.environ.get('MIN_STORAGE_MB', '100'))  # Minimum 100MB free space

# Collections to backup
MAIN_COLLECTIONS = ['users', 'students', 'buses', 'routes', 'stops', 'holidays', 'device_keys']
ATTENDANCE_COLLECTIONS = ['attendance', 'events']


class BackupManager:
    """Manages all backup operations with integrity checks and metadata"""
    
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Establish database connection"""
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[db_name]
        
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
    
    @staticmethod
    def ensure_directories():
        """Create backup directories if they don't exist"""
        BACKUP_DIR.mkdir(exist_ok=True)
        ATTENDANCE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Backup directories ready: {BACKUP_DIR}")
    
    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def check_storage_space() -> Tuple[bool, float]:
        """Check if sufficient storage space is available"""
        stat = shutil.disk_usage(BACKUP_DIR)
        free_mb = stat.free / (1024 * 1024)
        has_space = free_mb >= MIN_STORAGE_MB
        return has_space, free_mb
    
    @staticmethod
    def get_backup_files(backup_type: str = 'main') -> List[Path]:
        """Get all backup files sorted by timestamp (newest first)"""
        if backup_type == 'attendance':
            pattern = 'attendance_backup_*.json'
            directory = ATTENDANCE_BACKUP_DIR
        else:
            pattern = 'seed_backup_*.json'
            directory = BACKUP_DIR
        
        if not directory.exists():
            return []
        
        backup_files = list(directory.glob(pattern))
        backup_files.sort(reverse=True)
        return backup_files
    
    @staticmethod
    def get_metadata_path(backup_path: Path) -> Path:
        """Get metadata file path for a backup"""
        return backup_path.with_suffix('.meta.json')
    
    def create_metadata(self, backup_path: Path, backup_type: str, collections: Dict[str, int]) -> Dict[str, Any]:
        """Create metadata file with checksum and backup info"""
        checksum = self.calculate_sha256(backup_path)
        file_size = backup_path.stat().st_size
        
        metadata = {
            'backup_id': backup_path.stem,
            'backup_type': backup_type,
            'filename': backup_path.name,
            'timestamp': datetime.now().isoformat(),
            'checksum': checksum,
            'checksum_algorithm': 'SHA256',
            'file_size_bytes': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'collections': collections,
            'mongo_url': mongo_url.split('@')[-1] if '@' in mongo_url else mongo_url,  # Hide credentials
            'db_name': db_name,
            'version': '2.0'
        }
        
        meta_path = self.get_metadata_path(backup_path)
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata created: {meta_path.name}")
        return metadata
    
    def verify_backup(self, backup_path: Path) -> Tuple[bool, Optional[str]]:
        """Verify backup integrity using checksum"""
        meta_path = self.get_metadata_path(backup_path)
        
        if not meta_path.exists():
            return False, "Metadata file not found"
        
        try:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            stored_checksum = metadata.get('checksum')
            if not stored_checksum:
                return False, "No checksum in metadata"
            
            # Calculate current checksum
            current_checksum = self.calculate_sha256(backup_path)
            
            if current_checksum == stored_checksum:
                return True, "Integrity verified"
            else:
                return False, f"Checksum mismatch: expected {stored_checksum[:8]}..., got {current_checksum[:8]}..."
        
        except Exception as e:
            return False, f"Verification error: {str(e)}"
    
    def rotate_backups(self, backup_type: str = 'main'):
        """Delete old backups based on limit and retention policy"""
        backup_files = self.get_backup_files(backup_type)
        
        if len(backup_files) <= BACKUP_LIMIT:
            logger.info(f"Current {backup_type} backups: {len(backup_files)}/{BACKUP_LIMIT} (no rotation needed)")
            return
        
        # Delete excess backups
        files_to_delete = backup_files[BACKUP_LIMIT:]
        logger.info(f"Rotating {backup_type} backups: keeping {BACKUP_LIMIT} most recent, deleting {len(files_to_delete)} old file(s)")
        
        for backup_file in files_to_delete:
            try:
                # Delete backup and metadata
                backup_file.unlink()
                meta_path = self.get_metadata_path(backup_file)
                if meta_path.exists():
                    meta_path.unlink()
                logger.info(f"Deleted: {backup_file.name}")
            except Exception as e:
                logger.error(f"Failed to delete {backup_file.name}: {e}")
        
        logger.info(f"Backup rotation complete: {len(self.get_backup_files(backup_type))}/{BACKUP_LIMIT} {backup_type} backups remaining")
    
    def cleanup_old_backups(self, backup_type: str = 'main'):
        """Delete backups older than retention period"""
        backup_files = self.get_backup_files(backup_type)
        cutoff_date = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
        
        deleted_count = 0
        for backup_file in backup_files:
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                try:
                    backup_file.unlink()
                    meta_path = self.get_metadata_path(backup_file)
                    if meta_path.exists():
                        meta_path.unlink()
                    logger.info(f"Deleted old backup (> {BACKUP_RETENTION_DAYS} days): {backup_file.name}")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete old backup {backup_file.name}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old {backup_type} backup(s)")
    
    async def export_collection(self, collection_name: str) -> List[Dict[str, Any]]:
        """Export all documents from a collection"""
        documents = []
        cursor = self.db[collection_name].find({})
        
        async for doc in cursor:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            documents.append(doc)
        
        return documents
    
    async def create_main_backup(self) -> Tuple[bool, str, Optional[Dict]]:
        """Create main (seed) backup with all static collections"""
        try:
            logger.info("="*60)
            logger.info("💾 CREATING MAIN DATABASE BACKUP")
            logger.info("="*60)
            
            self.ensure_directories()
            
            # Check storage space
            has_space, free_mb = self.check_storage_space()
            if not has_space:
                error_msg = f"Insufficient storage space: {free_mb:.2f} MB free (minimum {MIN_STORAGE_MB} MB required)"
                logger.error(error_msg)
                return False, error_msg, None
            
            logger.info(f"Storage check passed: {free_mb:.2f} MB free")
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"seed_backup_{timestamp}.json"
            backup_path = BACKUP_DIR / backup_filename
            
            # Export collections
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'backup_type': 'main',
                'collections': {}
            }
            
            collection_counts = {}
            logger.info("Exporting collections:")
            
            for collection_name in MAIN_COLLECTIONS:
                try:
                    documents = await self.export_collection(collection_name)
                    backup_data['collections'][collection_name] = documents
                    collection_counts[collection_name] = len(documents)
                    logger.info(f"  ✅ {collection_name}: {len(documents)} document(s)")
                except Exception as e:
                    logger.error(f"  ⚠️ {collection_name}: Export failed - {e}")
                    backup_data['collections'][collection_name] = []
                    collection_counts[collection_name] = 0
            
            # Save backup
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Create metadata with checksum
            metadata = self.create_metadata(backup_path, 'main', collection_counts)
            
            logger.info(f"✅ Main backup created: {backup_filename}")
            logger.info(f"   Size: {metadata['file_size_mb']} MB")
            logger.info(f"   Checksum: {metadata['checksum'][:16]}...")
            
            # Rotate and cleanup
            self.rotate_backups('main')
            self.cleanup_old_backups('main')
            
            logger.info("="*60)
            logger.info("✅ MAIN BACKUP COMPLETED")
            logger.info("="*60)
            
            return True, backup_filename, metadata
        
        except Exception as e:
            error_msg = f"Main backup failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    async def create_attendance_backup(self) -> Tuple[bool, str, Optional[Dict]]:
        """Create attendance-specific backup"""
        try:
            logger.info("="*60)
            logger.info("📸 CREATING ATTENDANCE BACKUP")
            logger.info("="*60)
            
            self.ensure_directories()
            
            # Check storage space
            has_space, free_mb = self.check_storage_space()
            if not has_space:
                error_msg = f"Insufficient storage space: {free_mb:.2f} MB free (minimum {MIN_STORAGE_MB} MB required)"
                logger.error(error_msg)
                return False, error_msg, None
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"attendance_backup_{timestamp}.json"
            backup_path = ATTENDANCE_BACKUP_DIR / backup_filename
            
            # Export collections
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'backup_type': 'attendance',
                'collections': {},
                'photo_references': {}
            }
            
            collection_counts = {}
            logger.info("Exporting attendance collections:")
            
            for collection_name in ATTENDANCE_COLLECTIONS:
                try:
                    documents = await self.export_collection(collection_name)
                    backup_data['collections'][collection_name] = documents
                    collection_counts[collection_name] = len(documents)
                    logger.info(f"  ✅ {collection_name}: {len(documents)} document(s)")
                except Exception as e:
                    logger.error(f"  ⚠️ {collection_name}: Export failed - {e}")
                    backup_data['collections'][collection_name] = []
                    collection_counts[collection_name] = 0
            
            # Collect photo references
            logger.info("Collecting photo references...")
            photo_refs = await self._collect_photo_references()
            backup_data['photo_references'] = photo_refs
            collection_counts['photo_references'] = len(photo_refs.get('scan_photos', []))
            
            # Save backup
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Create metadata
            metadata = self.create_metadata(backup_path, 'attendance', collection_counts)
            
            logger.info(f"✅ Attendance backup created: {backup_filename}")
            logger.info(f"   Size: {metadata['file_size_mb']} MB")
            logger.info(f"   Checksum: {metadata['checksum'][:16]}...")
            
            # Rotate and cleanup
            self.rotate_backups('attendance')
            self.cleanup_old_backups('attendance')
            
            logger.info("="*60)
            logger.info("✅ ATTENDANCE BACKUP COMPLETED")
            logger.info("="*60)
            
            return True, backup_filename, metadata
        
        except Exception as e:
            error_msg = f"Attendance backup failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    async def _collect_photo_references(self) -> Dict[str, Any]:
        """Collect photo references from attendance records"""
        photo_refs = {'scan_photos': [], 'student_attendance_folders': []}
        
        # Scan photos from attendance
        cursor = self.db.attendance.find({"scan_photo": {"$exists": True, "$ne": None}})
        async for record in cursor:
            if record.get('scan_photo'):
                photo_refs['scan_photos'].append({
                    'attendance_id': record.get('attendance_id'),
                    'student_id': record.get('student_id'),
                    'date': record.get('date'),
                    'photo_url': record.get('scan_photo')
                })
        
        # Attendance folders from students
        cursor = self.db.students.find({"attendance_path": {"$exists": True, "$ne": None}})
        async for student in cursor:
            if student.get('attendance_path'):
                photo_refs['student_attendance_folders'].append({
                    'student_id': student.get('student_id'),
                    'attendance_path': student.get('attendance_path')
                })
        
        return photo_refs
    
    def get_backup_status(self, backup_type: str = 'main') -> Dict[str, Any]:
        """Get current backup status with health information"""
        backup_files = self.get_backup_files(backup_type)
        
        if not backup_files:
            return {
                'status': 'no_backups',
                'health': 'critical',
                'message': f'No {backup_type} backups found',
                'last_backup': None,
                'backup_count': 0
            }
        
        latest_backup = backup_files[0]
        meta_path = self.get_metadata_path(latest_backup)
        
        # Load metadata if exists
        metadata = {}
        if meta_path.exists():
            try:
                with open(meta_path, 'r') as f:
                    metadata = json.load(f)
            except:
                pass
        
        # Verify integrity
        is_valid, verify_msg = self.verify_backup(latest_backup)
        
        # Calculate age
        file_mtime = datetime.fromtimestamp(latest_backup.stat().st_mtime)
        age_hours = (datetime.now() - file_mtime).total_seconds() / 3600
        
        # Determine health
        if not is_valid:
            health = 'critical'
            status = 'corrupted'
        elif age_hours > 48:  # More than 2 days old
            health = 'warning'
            status = 'outdated'
        elif age_hours > 24:  # More than 1 day old
            health = 'caution'
            status = 'old'
        else:
            health = 'healthy'
            status = 'current'
        
        return {
            'status': status,
            'health': health,
            'message': verify_msg if not is_valid else f'Latest backup is {int(age_hours)} hours old',
            'last_backup': {
                'filename': latest_backup.name,
                'timestamp': metadata.get('timestamp', file_mtime.isoformat()),
                'size_mb': metadata.get('file_size_mb', round(latest_backup.stat().st_size / (1024*1024), 2)),
                'checksum': metadata.get('checksum', 'unknown')[:16] + '...',
                'age_hours': int(age_hours),
                'is_valid': is_valid,
                'collections': metadata.get('collections', {})
            },
            'backup_count': len(backup_files),
            'retention_limit': BACKUP_LIMIT
        }
    
    def get_all_backups(self, backup_type: str = 'main') -> List[Dict[str, Any]]:
        """Get list of all backups with metadata"""
        backup_files = self.get_backup_files(backup_type)
        backups = []
        
        for backup_file in backup_files:
            meta_path = self.get_metadata_path(backup_file)
            metadata = {}
            
            if meta_path.exists():
                try:
                    with open(meta_path, 'r') as f:
                        metadata = json.load(f)
                except:
                    pass
            
            # Verify integrity
            is_valid, verify_msg = self.verify_backup(backup_file)
            
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            backups.append({
                'backup_id': backup_file.stem,
                'filename': backup_file.name,
                'timestamp': metadata.get('timestamp', file_mtime.isoformat()),
                'size_mb': metadata.get('file_size_mb', round(backup_file.stat().st_size / (1024*1024), 2)),
                'checksum': metadata.get('checksum', 'unknown')[:16] + '...',
                'collections': metadata.get('collections', {}),
                'is_valid': is_valid,
                'verify_message': verify_msg,
                'age_days': (datetime.now() - file_mtime).days
            })
        
        return backups
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall backup system health"""
        main_status = self.get_backup_status('main')
        attendance_status = self.get_backup_status('attendance')
        
        # Check storage
        has_space, free_mb = self.check_storage_space()
        
        # Overall health determination
        health_scores = {
            'healthy': 3,
            'caution': 2,
            'warning': 1,
            'critical': 0
        }
        
        min_health = min(
            health_scores.get(main_status['health'], 0),
            health_scores.get(attendance_status['health'], 0)
        )
        
        overall_health = [k for k, v in health_scores.items() if v == min_health][0]
        
        if not has_space:
            overall_health = 'critical'
        
        return {
            'overall_health': overall_health,
            'main_backup': main_status,
            'attendance_backup': attendance_status,
            'storage': {
                'free_mb': round(free_mb, 2),
                'has_sufficient_space': has_space,
                'minimum_required_mb': MIN_STORAGE_MB
            },
            'configuration': {
                'backup_limit': BACKUP_LIMIT,
                'retention_days': BACKUP_RETENTION_DAYS,
                'backup_directory': str(BACKUP_DIR)
            }
        }


# Standalone functions for backward compatibility
async def create_main_backup():
    """Create main backup - standalone function"""
    manager = BackupManager()
    await manager.connect()
    try:
        success, message, metadata = await manager.create_main_backup()
        return success, message, metadata
    finally:
        manager.close()


async def create_attendance_backup():
    """Create attendance backup - standalone function"""
    manager = BackupManager()
    await manager.connect()
    try:
        success, message, metadata = await manager.create_attendance_backup()
        return success, message, metadata
    finally:
        manager.close()


if __name__ == "__main__":
    import sys
    
    async def main():
        backup_type = sys.argv[1] if len(sys.argv) > 1 else 'both'
        
        manager = BackupManager()
        await manager.connect()
        
        try:
            if backup_type in ['main', 'both']:
                await manager.create_main_backup()
            
            if backup_type in ['attendance', 'both']:
                await manager.create_attendance_backup()
        finally:
            manager.close()
    
    asyncio.run(main())
