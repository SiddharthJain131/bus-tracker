# Universal Photo Restoration System

## Overview
Comprehensive script that restores and relinks photos for ALL entities (students, teachers, parents, admins). Automatically generates realistic placeholder images via thispersondoesnotexist.com when real photos are missing.

## Quick Start

```bash
# Restore all photos (recommended)
python restore_all_photos.py

# Verify only (no changes)
python restore_all_photos.py --verify-only

# Quick fix script
./fix_all_photos.sh
```

## Features
✅ Restores photos for students, teachers, parents, and admins
✅ Generates realistic AI placeholders for missing photos
✅ Updates database photo references automatically
✅ Creates missing directory structures
✅ Safely rerunnable (idempotent)
✅ Verifies and repairs corrupted images
✅ Detailed logging and statistics

## Supported Entities

| Entity | Photo Path | File Location |
|--------|------------|---------------|
| Students | `/api/photos/students/{id}/profile.jpg` | `photos/students/{id}/profile.jpg` |
| Admins | `/api/photos/admins/{id}.jpg` | `photos/admins/{id}.jpg` |
| Teachers | `/api/photos/teachers/{id}.jpg` | `photos/teachers/{id}.jpg` |
| Parents | `/api/photos/parents/{id}.jpg` | `photos/parents/{id}.jpg` |

## Usage Examples

### Daily Verification
```bash
python restore_all_photos.py --verify-only
```

### Fix Unlinked Photos
```bash
python restore_all_photos.py
```

### Restore Without Placeholders
```bash
python restore_all_photos.py --no-placeholders
```

### Use Specific Backup
```bash
python restore_all_photos.py --backup-file /path/to/backup.json
```

## How It Works

1. **Reads Backup**: Loads latest backup from `/app/backend/backups/`
2. **Processes Each Entity**: For students, admins, teachers, and parents:
   - Creates missing directories
   - Verifies existing photos
   - Generates AI placeholders for missing photos
   - Updates database with correct photo paths
3. **Reports Results**: Shows detailed statistics

## Placeholder Generation

When a photo is missing, the script:
- Fetches a realistic AI-generated face from thispersondoesnotexist.com
- Converts to JPEG format (quality 85)
- Saves to correct location
- Updates database reference

## Safety Features

- **Non-Destructive**: Never deletes existing valid photos
- **Idempotent**: Safe to run multiple times
- **Verification Mode**: Check issues without making changes
- **Error Handling**: Gracefully handles API failures
- **Corruption Detection**: Identifies and replaces corrupted images

## Output Example

```
📊 RESTORATION SUMMARY
======================================================================

STUDENTS:
   Processed: 20
   ✅ Photos verified: 18
   🎨 Placeholders generated: 2
   📁 Directories created: 0
   🔄 Database updated: 0

ADMINS:
   Processed: 2
   ✅ Photos verified: 2
   🎨 Placeholders generated: 0

TEACHERS:
   Processed: 3
   ✅ Photos verified: 2
   🎨 Placeholders generated: 1

PARENTS:
   Processed: 12
   ✅ Photos verified: 12
   🎨 Placeholders generated: 0

----------------------------------------------------------------------
TOTAL ACROSS ALL ENTITIES:
   Processed: 37
   ✅ Photos verified: 34
   🎨 Placeholders generated: 3
======================================================================
```

## Common Scenarios

### Photos Become Unlinked
```bash
python restore_all_photos.py
```

### After Database Reseed
```bash
python restore_all_photos.py
```

### Regular Maintenance
```bash
# Add to cron
0 2 * * * cd /app/backend && python restore_all_photos.py --verify-only
```

## Dependencies

- `Pillow` - Image processing
- `requests` - HTTP requests
- `motor` - MongoDB async driver

All dependencies are in `requirements.txt`.

## Troubleshooting

**Q: Placeholder generation fails**  
A: Check internet connection. Script continues without placeholders if API fails.

**Q: Photos still missing after restore**  
A: Check backup file exists and contains photo data.

**Q: Database not updating**  
A: Verify MongoDB connection in `.env` file.
