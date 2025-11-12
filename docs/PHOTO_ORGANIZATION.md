# Photo Organization Structure

## Overview

The Bus Tracker system uses a role-based photo organization structure to efficiently manage profile photos and attendance scan images. All photos are stored under `/app/backend/photos/` with separate directories for each user role.

## Directory Structure

```
backend/photos/
├── students/
│   ├── {student_id}/
│   │   ├── profile.jpg              # Student profile photo
│   │   └── attendance/              # Daily attendance scan photos
│   │       ├── 2025-11-14_AM.jpg   # Morning scan
│   │       ├── 2025-11-14_PM.jpg   # Afternoon scan
│   │       └── ...
│   └── ...
├── parents/
│   ├── {parent_id}.jpg             # Parent profile photo
│   └── ...
├── teachers/
│   ├── {teacher_id}.jpg            # Teacher profile photo
│   └── ...
└── admins/
    ├── {admin_id}.jpg              # Admin profile photo
    └── ...
```

## Student Photo Organization

### Profile Photos
- **Location**: `backend/photos/students/{student_id}/profile.jpg`
- **Purpose**: Primary profile photo displayed in dashboards
- **Format**: JPEG
- **Naming**: Always named `profile.jpg` for consistency

### Attendance Photos
- **Location**: `backend/photos/students/{student_id}/attendance/`
- **Purpose**: Store daily face recognition scan images
- **Format**: JPEG
- **Naming Convention**: `YYYY-MM-DD_{AM|PM}.jpg`
  - Example: `2025-11-14_AM.jpg` (morning scan)
  - Example: `2025-11-14_PM.jpg` (afternoon scan)

### Directory per Student
Each student has their own directory identified by their unique `student_id` (UUID):
- Enables efficient file organization
- Prevents filename conflicts
- Simplifies backup and archival
- Supports future expansion (certificates, documents, etc.)

## Other User Roles

### Parents
- **Location**: `backend/photos/parents/{parent_id}.jpg`
- **Structure**: Flat directory with one photo per parent
- **Naming**: `{parent_id}.jpg`

### Teachers
- **Location**: `backend/photos/teachers/{teacher_id}.jpg`
- **Structure**: Flat directory with one photo per teacher
- **Naming**: `{teacher_id}.jpg`

### Admins
- **Location**: `backend/photos/admins/{admin_id}.jpg`
- **Structure**: Flat directory with one photo per admin
- **Naming**: `{admin_id}.jpg`

## Database Integration

### Student Schema
Each student document includes:
```json
{
  "student_id": "uuid",
  "photo": "backend/photos/students/{student_id}/profile.jpg",
  "photo_path": "backend/photos/students/{student_id}/profile.jpg",
  "attendance_path": "backend/photos/students/{student_id}/attendance"
}
```

### User Schema (Parent/Teacher/Admin)
Each user document includes:
```json
{
  "user_id": "uuid",
  "role": "parent|teacher|admin",
  "photo": "backend/photos/{role}s/{user_id}.jpg",
  "photo_path": "backend/photos/{role}s/{user_id}.jpg"
}
```

## File Naming Conventions

### Profile Photos
- **Format**: `profile.jpg` (students) or `{user_id}.jpg` (others)
- **Case**: Lowercase
- **Extension**: `.jpg` (JPEG format)

### Attendance Scan Photos
- **Format**: `YYYY-MM-DD_{period}.jpg`
- **Date**: ISO 8601 format (YYYY-MM-DD)
- **Period**: `AM` or `PM` (uppercase)
- **Examples**:
  - `2025-11-14_AM.jpg`
  - `2025-11-14_PM.jpg`
  - `2025-12-25_AM.jpg`

## Photo Upload Guidelines

### Image Specifications
- **Format**: JPEG (.jpg)
- **Recommended Size**: 800x800 pixels (square)
- **Maximum Size**: 5MB per file
- **Compression**: 85% quality recommended

### Profile Photo Requirements
- Clear, front-facing image
- Good lighting
- Plain background preferred
- Face should occupy 60-80% of frame

### Attendance Photo Requirements
- Captured during bus boarding/departure
- High enough quality for face recognition
- Automatically timestamped
- Stored chronologically

## Maintenance Scripts

### Organization Script
The system includes an automated organization script:

**Location**: `/app/backend/organize_photos.py`

**Features**:
- Reorganizes photos by role
- Creates student attendance folders
- Updates database backup files
- Creates backups before modifications
- Generates summary reports

**Usage**:
```bash
cd /app/backend
python3 organize_photos.py
```

### Backup Strategy
Before any reorganization:
1. Photos directory backed up to `photos_backup_{timestamp}/`
2. Database backup file copied to `{filename}.bak`
3. Original structure preserved for rollback

## API Endpoints for Photos

### Student Profile Photo
```
GET /api/students/{student_id}/photo
Response: { "student_id", "name", "photo_url", "has_photo" }
```

### Student Face Embedding
```
GET /api/students/{student_id}/embedding
Response: { "student_id", "name", "embedding", "has_embedding" }
```

### Photo Upload (Future)
```
POST /api/upload/student/{student_id}/profile
POST /api/upload/user/{user_id}/profile
Body: multipart/form-data with image file
```

## Storage Considerations

### Disk Space Planning
- **Profile Photos**: ~500KB per photo average
- **Attendance Photos**: ~300KB per photo average
- **Daily Growth**: Approximately 6KB per student (2 scans/day)
- **Monthly Growth**: Approximately 120KB per student

### Example Calculation (500 students)
- Profile photos: 500 × 0.5MB = 250MB
- Monthly attendance: 500 × 0.12MB = 60MB
- Annual attendance: 60MB × 10 months = 600MB
- **Total annual**: ~850MB

### Cleanup Recommendations
- Archive attendance photos older than 1 year
- Compress historical photos (reduce quality to 70%)
- Move archived data to cold storage
- Keep current academic year in hot storage

## Security & Access Control

### File Permissions
- Photos directory: `755` (drwxr-xr-x)
- Photo files: `644` (-rw-r--r-)
- Owned by application user

### Access Control
- Profile photos: Role-based access via API
- Attendance photos: Admin and authorized device access only
- Direct file access: Restricted to application server

### Privacy Considerations
- Face data stored locally (not cloud)
- Attendance photos contain PII - secure storage required
- GDPR/FERPA compliance: Implement data retention policies
- Parental consent required for photo capture

## Migration Guide

### From Old Structure
If migrating from flat structure (STU001.jpg, STU002.jpg):

1. **Run organization script**:
   ```bash
   cd /app/backend
   python3 organize_photos.py
   ```

2. **Verify structure**:
   ```bash
   tree -L 3 backend/photos/
   ```

3. **Update database** (automatic):
   - Script updates latest backup file
   - Adds `photo_path` and `attendance_path` fields
   - Creates `.bak` copy of original

4. **Test application**:
   - Verify student photos display correctly
   - Check API endpoints return new paths
   - Test upload functionality (if implemented)

### Rollback Procedure
If issues occur:
1. Stop application services
2. Restore backup: `cp -r photos_backup_{timestamp} photos/`
3. Restore database backup: `cp seed_backup_*.bak seed_backup_*.json`
4. Restart services

## Troubleshooting

### Photos Not Displaying
1. Check file exists: `ls backend/photos/students/{student_id}/profile.jpg`
2. Verify permissions: `ls -la backend/photos/students/{student_id}/`
3. Check database paths: Query `photo_path` field
4. Review API response: `curl /api/students/{student_id}/photo`

### Attendance Folder Missing
1. Verify structure: `ls backend/photos/students/{student_id}/attendance/`
2. Create manually if needed: `mkdir -p backend/photos/students/{student_id}/attendance`
3. Update database: Set `attendance_path` field

### Disk Space Issues
1. Check usage: `du -sh backend/photos/*`
2. Archive old scans: `tar -czf attendance_archive_2024.tar.gz backend/photos/students/*/attendance/2024*`
3. Remove archived files after backup verification
4. Monitor with cron job

## Future Enhancements

### Planned Features
- [ ] Automatic photo upload via admin dashboard
- [ ] Bulk photo import tool
- [ ] Photo compression on upload
- [ ] Thumbnail generation for faster loading
- [ ] Attendance photo carousel view
- [ ] Photo retention policy automation
- [ ] Cloud backup integration (optional)
- [ ] Face recognition accuracy reports

### API Enhancements
- Photo upload endpoints with validation
- Batch photo processing
- Photo metadata (capture date, device info)
- Photo versioning (update history)

## Related Documentation
- [Database Schema](DATABASE.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Raspberry Pi Integration](RASPBERRY_PI_INTEGRATION.md)
- [Device API Testing](API_TEST_DEVICE.md)

---

**Last Updated**: 2025-11-12  
**Structure Version**: 1.0  
**Maintained By**: Bus Tracker Development Team
