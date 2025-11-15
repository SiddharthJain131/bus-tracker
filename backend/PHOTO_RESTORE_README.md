# Student Photo Restoration System

## Overview

This system provides permanent scripts to rebuild and relink student photos that frequently become unlinked or missing. The scripts ensure every student record has its correct associated photo restored from backup sources.

## Scripts

### 1. `restore_student_photos.py`

**Primary restoration script** - Rebuilds photo directory structure and relinks photos to students based on the backup file.

#### Features:
- Reads student data from the latest backup JSON file
- Creates missing photo directories for each student
- Creates attendance subdirectories
- Verifies photo file existence
- Updates database with correct photo paths
- Safe to run multiple times (idempotent)
- Provides detailed logging and statistics

#### Usage:

```bash
# Run full restoration with latest backup
python restore_student_photos.py

# Run restoration with specific backup file
python restore_student_photos.py --backup-file /path/to/backup.json

# Verify photos only (no changes)
python restore_student_photos.py --verify-only
```

#### What It Does:

1. **Finds Latest Backup**: Locates the most recent `seed_backup_*.json` file in `/app/backend/backups/`
2. **Reads Student Data**: Extracts all student records from the backup
3. **Creates Directories**: For each student:
   - Creates `/photos/students/{student_id}/`
   - Creates `/photos/students/{student_id}/attendance/`
4. **Verifies Photos**: Checks if `profile.jpg` exists for each student
5. **Updates Database**: Ensures each student's photo field has the correct path: `/api/photos/students/{student_id}/profile.jpg`
6. **Reports Results**: Shows statistics on directories created, photos verified, and any issues

#### Output Example:

```
======================================================================
🔄 STUDENT PHOTO RESTORATION & RELINK
======================================================================
⏰ Started at: 2025-11-15 06:04:30

📦 Loading backup from: seed_backup_20251115_0537.json
📚 Found 20 students in backup

🔍 Processing students...

[1/20] Emma Johnson (770f57ab-da26-4830-9615-a22451c61808)
   📁 Created directory: 770f57ab-da26-4830-9615-a22451c61808/
   📁 Created subdirectory: 770f57ab-da26-4830-9615-a22451c61808/attendance/
   ✅ Photos verified

======================================================================
📊 RESTORATION SUMMARY
======================================================================
✅ Directories created: 20
✅ Photos verified: 20
⚠️  Photos missing: 0
✅ Database records updated: 0
======================================================================
```

---

### 2. `migrate_orphaned_photos.py`

**Helper script** - Manages orphaned photo directories from previous database seeds where student_ids have changed.

#### Features:
- Identifies orphaned photo directories (not linked to current students)
- Migrates photos from old directories to new ones
- Matches photos by index/order
- Preserves attendance photos
- Can clean up orphaned directories

#### Usage:

```bash
# List all orphaned photo directories
python migrate_orphaned_photos.py --list

# Migrate orphaned photos to current students
python migrate_orphaned_photos.py --migrate

# Clean orphaned directories (dry run)
python migrate_orphaned_photos.py --clean

# Clean orphaned directories (actual deletion - be careful!)
python migrate_orphaned_photos.py --clean --confirm
```

#### What It Does:

**--list**: Lists all photo directories that don't correspond to any current student in the database, showing:
- Directory name (old student_id)
- Whether profile photo exists
- Count of attendance photos

**--migrate**: Copies photos from orphaned directories to current student directories:
1. Gets list of current students (sorted alphabetically)
2. Gets list of orphaned directories with photos (sorted)
3. Maps old directories to new student_ids by index
4. Copies `profile.jpg` and all attendance photos
5. Creates proper directory structure for each student

**--clean**: Removes orphaned directories (use with caution!)

#### Output Example:

```
======================================================================
🔍 ORPHANED PHOTO DIRECTORIES
======================================================================
⚠️  Found 20 orphaned directories:

[1] d61d7051-16f3-4c80-a28b-55a3d475757c
    ✅ Has profile.jpg
    📸 12 attendance photo(s)

======================================================================
```

---

## Directory Structure

```
/app/backend/
├── photos/
│   └── students/
│       ├── {student_id_1}/
│       │   ├── profile.jpg           # Main profile photo
│       │   └── attendance/           # Attendance photos
│       │       ├── 2025-11-15_AM.jpg
│       │       └── 2025-11-15_PM.jpg
│       └── {student_id_2}/
│           ├── profile.jpg
│           └── attendance/
├── backups/
│   └── seed_backup_20251115_0537.json  # Backup with student data
├── restore_student_photos.py           # Main restoration script
└── migrate_orphaned_photos.py          # Orphaned photo migration
```

---

## Photo Path Convention

### Database Field:
Students have a `photo` field that stores the API path:
```
/api/photos/students/{student_id}/profile.jpg
```

### Actual File Location:
Physical file on the filesystem:
```
/app/backend/photos/students/{student_id}/profile.jpg
```

### Server Configuration:
The FastAPI server mounts the photos directory and serves it at `/api/photos`:
```python
app.mount("/api/photos", StaticFiles(directory=PHOTO_DIR), name="photos")
```

---

## Common Scenarios

### Scenario 1: Photos Become Unlinked

**Problem**: Student records exist but photos are missing or unlinked.

**Solution**:
```bash
# First, verify the issue
python restore_student_photos.py --verify-only

# Run restoration
python restore_student_photos.py
```

### Scenario 2: Database Was Reseeded with New UUIDs

**Problem**: Database has new student_ids but old photo directories still exist with old IDs.

**Solution**:
```bash
# Step 1: Check for orphaned photos
python migrate_orphaned_photos.py --list

# Step 2: Migrate photos from old directories to new ones
python migrate_orphaned_photos.py --migrate

# Step 3: Verify everything is linked correctly
python restore_student_photos.py --verify-only

# Step 4 (Optional): Clean up old directories
python migrate_orphaned_photos.py --clean --confirm
```

### Scenario 3: New Students Added

**Problem**: New students added to database but photo directories don't exist.

**Solution**:
```bash
# Run restoration to create missing directories
python restore_student_photos.py
```

### Scenario 4: Regular Maintenance

**Best Practice**: Run verification regularly to ensure photos stay linked.

```bash
# Add to cron or run periodically
python restore_student_photos.py --verify-only
```

---

## Integration with Backup System

The restoration scripts automatically integrate with the existing backup system at `/app/backend/backups/`.

### Backup Files:
- Location: `/app/backend/backups/seed_backup_*.json`
- Format: JSON with timestamp
- Contains: All student records with photo paths

### How It Works:
1. Backup system creates timestamped backups: `seed_backup_20251115_0537.json`
2. Restoration script automatically finds the latest backup
3. Student data is read from the backup
4. Photo paths are extracted and used to create/verify directory structure

---

## Error Handling

The scripts handle various error scenarios gracefully:

### Missing Backup File:
```
❌ No backup file found!
```
**Solution**: Ensure backup files exist in `/app/backend/backups/`

### Missing Photos:
```
⚠️  Missing photo file: Emma Johnson (770f57ab...)
```
**Solution**: Photos will need to be re-uploaded or restored from another source

### Database Connection Issues:
```
❌ Failed to connect to database
```
**Solution**: Check MongoDB connection and `.env` configuration

### Permission Issues:
```
❌ Failed to create directory: Permission denied
```
**Solution**: Ensure proper file permissions on `/app/backend/photos/`

---

## Safety Features

Both scripts are designed to be safe:

1. **Idempotent**: Can be run multiple times without causing issues
2. **Non-Destructive**: Won't delete existing photos (except `--clean --confirm`)
3. **Detailed Logging**: Shows exactly what's being changed
4. **Dry Run Options**: Verification mode available
5. **Error Reporting**: Tracks and reports all errors
6. **Statistics**: Provides summary of all operations

---

## Maintenance Tips

1. **Run Verification Regularly**:
   ```bash
   python restore_student_photos.py --verify-only
   ```

2. **After Database Reseeding**:
   ```bash
   python migrate_orphaned_photos.py --migrate
   python restore_student_photos.py
   ```

3. **Before System Backup**:
   Ensure all photos are properly linked

4. **Monitor Disk Space**:
   Old orphaned directories can accumulate over time

5. **Backup Photo Files**:
   The JSON backup only contains paths, not actual photo files

---

## Technical Details

### Database Connection:
- Uses Motor (async MongoDB driver)
- Reads connection from `.env`: `MONGO_URL`
- Database name from `.env`: `DB_NAME`

### Photo Storage:
- Base directory: `/app/backend/photos/`
- Student photos: `/app/backend/photos/students/`
- Supports subdirectories for attendance photos

### Student Schema:
```python
{
    "student_id": "uuid-string",
    "name": "Student Name",
    "photo": "/api/photos/students/{student_id}/profile.jpg",
    ...
}
```

---

## Troubleshooting

### Q: Script says photos are missing but they exist
**A**: Check if student_ids in database match directory names. Use `--list` to see orphaned directories.

### Q: Photos migrated but still showing as missing
**A**: Run `restore_student_photos.py` to update database paths.

### Q: Some students have photos, others don't
**A**: Run full restoration flow: migrate → restore → verify

### Q: Old directories taking up space
**A**: After successful migration, use `--clean --confirm` to remove orphaned directories.

### Q: Database paths are wrong
**A**: Run `restore_student_photos.py` - it will update all photo paths to correct format.

---

## Quick Reference

```bash
# Daily verification
python restore_student_photos.py --verify-only

# Fix missing/unlinked photos
python restore_student_photos.py

# After database reseed
python migrate_orphaned_photos.py --migrate && \
python restore_student_photos.py

# Clean up old files
python migrate_orphaned_photos.py --clean --confirm
```

---

## Support

For issues or questions:
1. Check error messages in script output
2. Verify backup files exist and are valid JSON
3. Check MongoDB connection
4. Ensure proper file permissions
5. Review this documentation

The scripts are designed to be self-explanatory with detailed output and error messages.
