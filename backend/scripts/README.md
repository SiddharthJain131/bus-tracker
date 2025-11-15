# Backend Scripts

This directory contains utility scripts for managing the application.

## Available Scripts

### 1. reorganize_photos.py
**Purpose**: Reorganize photos folder using backup data

**What it does**:
- Reads seed and attendance backup files
- Downloads AI-generated faces from thispersondoesnotexist.com for users with `photo: null`
- Creates proper folder structure for all user types
- Preserves attendance photos
- Backs up old photos before replacing

**Usage**:
```bash
cd /app/backend
python3 scripts/reorganize_photos.py
```

**Requirements**:
- Pillow (PIL)
- requests (already in requirements.txt)

**Backup files used**:
- `/app/backend/backups/seed_backup_20251114_0532.json`
- `/app/backend/backups/attendance/attendance_backup_20251114_0532.json`

**Output**:
- New photos structure in `/app/backend/photos/`
- Old photos backed up to `/app/backend/photos_old_backup/`

---

### 2. verify_photos.py
**Purpose**: Verify photo structure integrity

**What it does**:
- Checks all photos in the photos directory
- Verifies each image can be opened and is not corrupted
- Provides statistics on photo counts by user type
- Reports any corrupted files

**Usage**:
```bash
cd /app/backend
python3 scripts/verify_photos.py
```

**Output**:
- Summary of photo counts
- List of any corrupted files
- Exit code 0 if all photos are valid, 1 if corrupted files found

---

## Photo Structure

The expected photo structure is:

```
photos/
├── admins/
│   └── {user_id}.jpg
├── teachers/
│   └── {user_id}.jpg
├── parents/
│   └── {user_id}.jpg
└── students/
    └── {student_id}/
        ├── profile.jpg
        └── attendance/
            └── {date}_{trip}.jpg
```

## Notes

- All photos are stored as JPEG files
- Photos from thispersondoesnotexist.com are 512x512 pixels
- Quality is set to 85% for optimal size/quality balance
- Old photos are never deleted, always backed up first

## Dependencies

Make sure these are in `requirements.txt`:
- `Pillow==12.0.0`
- `requests` (already present)
