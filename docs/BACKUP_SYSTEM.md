# 💾 Backup System Documentation

## Overview

The Bus Tracker System implements a **production-ready, robust backup system** with integrity verification, automated scheduling, and frontend monitoring. The system maintains two types of backups: **Main Backups** (static data) and **Attendance Backups** (dynamic data).

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Admin Dashboard)                │
│  • Backup Management UI                                      │
│  • Real-time health monitoring                               │
│  • Manual backup trigger                                     │
│  • Backup history viewer                                     │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    Backend API Endpoints                      │
│  GET  /api/admin/backups/status                             │
│  GET  /api/admin/backups/list                               │
│  GET  /api/admin/backups/health                             │
│  POST /api/admin/backups/trigger                            │
│  POST /api/admin/backups/verify/{backup_id}                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    BackupManager Class                        │
│  • Create backups with checksums                            │
│  • Verify integrity (SHA256)                                │
│  • Rotation & retention policies                            │
│  • Storage validation                                        │
│  • Health monitoring                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    Background Schedulers                      │
│  • Main backup scheduler (1 hour interval)                  │
│  • Attendance backup scheduler (1 hour interval)            │
│  • Non-blocking async execution                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                              │
│  📁 /app/backend/backups/                                   │
│     ├── seed_backup_YYYYMMDD_HHMMSS.json                   │
│     ├── seed_backup_YYYYMMDD_HHMMSS.meta.json              │
│     └── attendance/                                          │
│         ├── attendance_backup_YYYYMMDD_HHMMSS.json         │
│         └── attendance_backup_YYYYMMDD_HHMMSS.meta.json    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 What Gets Backed Up

### Main Backup (Static Data)
Collections that rarely change:
- **users** - User accounts (admins, teachers, parents)
- **students** - Student profiles
- **buses** - Bus information
- **routes** - Route configurations
- **stops** - Bus stop locations
- **holidays** - School holidays
- **device_keys** - Raspberry Pi device authentication keys

### Attendance Backup (Dynamic Data)
Collections that change frequently:
- **attendance** - Daily attendance records
- **events** - Scan events from RFID readers
- **photo_references** - Links to attendance scan photos

---

## ⏰ When Backups Occur

### Automated Schedule
- **Main Backups**: Every 1 hour (configurable via `SEED_INTERVAL_HOURS`)
- **Attendance Backups**: Every 1 hour (configurable via `ATTENDANCE_INTERVAL_HOURS`)
- **Non-blocking**: Backups run in background without affecting user operations

### Manual Triggers
Admins can trigger backups manually through:
- Frontend UI: **Admin Dashboard → Backups Tab → "Run Backup Now"** button
- API: `POST /api/admin/backups/trigger?backup_type=both`

---

## 💿 Where Backups Are Stored

### Storage Locations
```
/app/backend/backups/
├── seed_backup_20251117_150530.json          # Main backup
├── seed_backup_20251117_150530.meta.json     # Metadata with checksum
├── seed_backup_20251117_140015.json
├── seed_backup_20251117_140015.meta.json
└── attendance/
    ├── attendance_backup_20251117_150530.json
    ├── attendance_backup_20251117_150530.meta.json
    ├── attendance_backup_20251117_140015.json
    └── attendance_backup_20251117_140015.meta.json
```

### Naming Convention
- **Main**: `seed_backup_YYYYMMDD_HHMMSS.json`
- **Attendance**: `attendance_backup_YYYYMMDD_HHMMSS.json`
- **Metadata**: `<backup_name>.meta.json`

### Metadata Structure
Each backup has an accompanying metadata file containing:
```json
{
  "backup_id": "seed_backup_20251117_150530",
  "backup_type": "main",
  "filename": "seed_backup_20251117_150530.json",
  "timestamp": "2025-11-17T15:05:30.123456",
  "checksum": "a1b2c3d4e5f6...",
  "checksum_algorithm": "SHA256",
  "file_size_bytes": 1048576,
  "file_size_mb": 1.0,
  "collections": {
    "users": 20,
    "students": 15,
    "buses": 4,
    "routes": 4,
    "stops": 20,
    "holidays": 5,
    "device_keys": 2
  },
  "mongo_url": "localhost:27017",
  "db_name": "bus_tracker",
  "version": "2.0"
}
```

---

## 🔐 Integrity Verification

### SHA256 Checksums
Every backup file has a **SHA256 checksum** calculated and stored in metadata:
- Calculated immediately after backup creation
- Verified before restore operations
- Displayed in frontend with truncated hash (`a1b2c3d4e5f6...`)

### Verification Process
1. Read stored checksum from metadata file
2. Recalculate checksum of backup file
3. Compare values
4. Report status: ✅ Valid or ❌ Corrupted

### How to Verify
**Via Frontend:**
- Navigate to **Admin Dashboard → Backups Tab**
- Check the badge next to each backup (✅ Valid / ❌ Invalid)

**Via API:**
```bash
curl -X POST "http://localhost:8001/api/admin/backups/verify/seed_backup_20251117_150530" \
  --cookie "session_token=..." \
  -H "Content-Type: application/json"
```

---

## 🔄 Retention Policies

### Limits
- **Backup Count Limit**: Keep only 5 most recent backups (configurable via `BACKUP_LIMIT`)
- **Time-based Retention**: Keep backups for 30 days (configurable via `BACKUP_RETENTION_DAYS`)

### Rotation Behavior
When a new backup is created:
1. Create and verify new backup
2. Count existing backups
3. If count > limit, delete oldest backups
4. Delete backups older than retention period

### Example
```
Current backups: 6
Limit: 5
Action: Delete oldest backup (6th one)

Backups after rotation:
1. seed_backup_20251117_150530.json  (newest)
2. seed_backup_20251117_140015.json
3. seed_backup_20251117_130000.json
4. seed_backup_20251117_120000.json
5. seed_backup_20251117_110000.json  (oldest kept)
```

---

## 🖥️ Frontend Display

### Access
Navigate to: **Admin Dashboard → Backups Tab**

### Features

#### 1. Overall Health Card
Displays system-wide backup health:
- **Main Backup Status**: Last backup time, health badge (Healthy/Caution/Warning/Critical)
- **Attendance Backup Status**: Last backup time, health badge
- **Storage Status**: Free space, sufficient space indicator
- **Configuration**: Retention limits, directory location

#### 2. Health Status Badges
- 🟢 **Healthy**: Backup < 24 hours old, integrity verified
- 🟡 **Caution**: Backup 24-48 hours old
- 🟠 **Warning**: Backup > 48 hours old
- 🔴 **Critical**: Backup corrupted or missing

#### 3. Backup History Tabs
- **Main Backups Tab**: Lists all main backups with metadata
- **Attendance Backups Tab**: Lists all attendance backups

#### 4. Backup Cards
Each backup displays:
- Filename and timestamp
- Validity badge (✅ Valid / ❌ Invalid)
- Age in days
- File size in MB
- Checksum (truncated)
- Collection counts (users: 20, students: 15, etc.)

#### 5. Manual Trigger
- **"Run Backup Now"** button triggers immediate backup
- Shows spinner during execution
- Toast notification on success/failure

#### 6. Auto-refresh
- Status refreshes every 30 seconds automatically
- Manual refresh button available

---

## 🔧 Configuration

### Environment Variables
Edit `/app/backend/.env`:

```bash
# Backup configuration
BACKUP_LIMIT=5                      # Number of backups to retain
BACKUP_RETENTION_DAYS=30            # Days to keep backups
MIN_STORAGE_MB=100                  # Minimum free space (MB) required
SEED_INTERVAL_HOURS=1               # Main backup interval (hours)
ATTENDANCE_INTERVAL_HOURS=1         # Attendance backup interval (hours)
```

### Storage Requirements
- **Minimum free space**: 100 MB (configurable)
- **Average backup size**: 0.5-2 MB per backup
- **Total storage needed**: ~50 MB (for 5 main + 5 attendance backups)

---

## 🔄 How to Restore from Backup

### Automated Restore (On Startup)
The system automatically restores from the latest backup on server startup:
```python
# In seed_data.py
if no_data_exists():
    latest_backup = get_latest_backup()
    if latest_backup:
        restore_from_backup(latest_backup)
    else:
        create_default_seed_data()
```

### Manual Restore
**Option 1: Via restore script (recommended)**
```bash
cd /app/backend
python restore_backup.py --backup-file backups/seed_backup_20251117_150530.json
```

**Option 2: Manually using MongoDB**
```bash
# 1. Load backup JSON
cd /app/backend
backup_file="backups/seed_backup_20251117_150530.json"

# 2. Restore collections
mongoimport --db bus_tracker --collection users --file extracted_users.json --jsonArray
mongoimport --db bus_tracker --collection students --file extracted_students.json --jsonArray
# ... repeat for all collections
```

### Restore Verification Steps
1. ✅ Verify backup integrity before restore
2. ✅ Backup current database before restore
3. ✅ Test restore in staging environment first
4. ✅ Verify data after restore
5. ✅ Check application functionality

---

## 📊 API Reference

### Get Backup Status
```http
GET /api/admin/backups/status?backup_type=both
```
**Query Parameters:**
- `backup_type`: `main`, `attendance`, or `both` (default: `both`)

**Response:**
```json
{
  "main": {
    "status": "current",
    "health": "healthy",
    "message": "Latest backup is 2 hours old",
    "last_backup": {
      "filename": "seed_backup_20251117_150530.json",
      "timestamp": "2025-11-17T15:05:30",
      "size_mb": 1.2,
      "checksum": "a1b2c3d4e5f6...",
      "age_hours": 2,
      "is_valid": true,
      "collections": {...}
    },
    "backup_count": 5,
    "retention_limit": 5
  },
  "attendance": {...}
}
```

### List All Backups
```http
GET /api/admin/backups/list?backup_type=both
```
**Response:**
```json
{
  "main": [
    {
      "backup_id": "seed_backup_20251117_150530",
      "filename": "seed_backup_20251117_150530.json",
      "timestamp": "2025-11-17T15:05:30",
      "size_mb": 1.2,
      "checksum": "a1b2c3d4e5f6...",
      "collections": {...},
      "is_valid": true,
      "verify_message": "Integrity verified",
      "age_days": 0
    }
  ],
  "attendance": [...]
}
```

### Get Overall Health
```http
GET /api/admin/backups/health
```
**Response:**
```json
{
  "overall_health": "healthy",
  "main_backup": {...},
  "attendance_backup": {...},
  "storage": {
    "free_mb": 2048.5,
    "has_sufficient_space": true,
    "minimum_required_mb": 100
  },
  "configuration": {
    "backup_limit": 5,
    "retention_days": 30,
    "backup_directory": "/app/backend/backups"
  }
}
```

### Trigger Manual Backup
```http
POST /api/admin/backups/trigger?backup_type=both
```
**Query Parameters:**
- `backup_type`: `main`, `attendance`, or `both` (default: `both`)

**Response:**
```json
{
  "main": {
    "success": true,
    "message": "seed_backup_20251117_160000.json",
    "metadata": {...}
  },
  "attendance": {
    "success": true,
    "message": "attendance_backup_20251117_160000.json",
    "metadata": {...}
  }
}
```

### Verify Backup Integrity
```http
POST /api/admin/backups/verify/{backup_id}
```
**Example:**
```bash
POST /api/admin/backups/verify/seed_backup_20251117_150530
```
**Response:**
```json
{
  "backup_id": "seed_backup_20251117_150530",
  "is_valid": true,
  "message": "Integrity verified"
}
```

---

## 🚨 Error Handling

### Common Issues

#### 1. Insufficient Storage Space
**Symptom:** Backup fails with storage error
**Solution:**
```bash
# Check free space
df -h /app/backend/backups

# Clean old backups manually
cd /app/backend/backups
rm seed_backup_20250101_*.json
rm seed_backup_20250101_*.meta.json
```

#### 2. Corrupted Backup
**Symptom:** Checksum verification fails
**Solution:**
- Frontend shows ❌ Invalid badge
- Don't use this backup for restore
- Trigger new backup immediately
- Investigate disk errors

#### 3. Backup Scheduler Not Running
**Symptom:** No new backups created
**Solution:**
```bash
# Check backend logs
tail -f /var/log/supervisor/backend.out.log

# Restart backend
sudo supervisorctl restart backend
```

#### 4. Backup Taking Too Long
**Symptom:** Backup operation times out
**Solution:**
- Check database size
- Optimize MongoDB indexes
- Increase backup interval
- Consider splitting large collections

---

## 🔍 Monitoring & Alerts

### Health Indicators

#### Frontend Alerts
The system shows visual alerts when:
- ❌ Last backup > 48 hours old
- ❌ Storage space < 100 MB
- ❌ Backup integrity verification fails
- ❌ Backup scheduler errors

### Recommended Monitoring
1. **Check backup health daily** via Admin Dashboard
2. **Monitor storage usage** to prevent disk full
3. **Verify latest backup integrity** after creation
4. **Test restore process** periodically (monthly)

---

## 🔐 Security Considerations

### Backup Storage
- ✅ Stored locally on server (not in public directory)
- ✅ Only accessible to backend process
- ✅ Admin-only API endpoints
- ⚠️ **Recommendation**: Configure external backup storage (S3, NAS)

### Sensitive Data
Backups contain:
- ✅ **Password hashes** (bcrypt, safe)
- ⚠️ **Personal data** (names, emails, phone numbers)
- ⚠️ **Device API keys** (hashed)

**Recommendation**: Encrypt backups at rest if storing off-server

---

## 🧪 Testing Backup System

### Manual Test Procedure
```bash
# 1. Trigger backup via API
curl -X POST "http://localhost:8001/api/admin/backups/trigger?backup_type=main" \
  --cookie "session_token=..."

# 2. Verify backup created
ls -lh /app/backend/backups/

# 3. Check metadata
cat /app/backend/backups/seed_backup_*.meta.json | jq

# 4. Verify integrity
curl -X POST "http://localhost:8001/api/admin/backups/verify/seed_backup_YYYYMMDD_HHMMSS" \
  --cookie "session_token=..."

# 5. Check frontend display
# Navigate to Admin Dashboard → Backups Tab
```

---

## 📝 Changelog

### Version 2.0 (Current)
- ✅ SHA256 integrity verification
- ✅ Metadata files with detailed backup info
- ✅ Non-blocking async backup operations
- ✅ Frontend monitoring UI
- ✅ Manual backup trigger
- ✅ Overall health dashboard
- ✅ Storage space validation
- ✅ Configurable retention policies
- ✅ REST API endpoints for all operations

### Version 1.0 (Legacy)
- Basic JSON export
- Simple rotation (keep 3 backups)
- No integrity checks
- No frontend UI
- Subprocess-based execution

---

## 🆘 Support

For issues or questions:
1. Check **TROUBLESHOOTING.md** for common issues
2. Review backend logs: `tail -f /var/log/supervisor/backend.out.log`
3. Verify configuration in `.env` file
4. Test backup manually: `cd /app/backend && python backup_manager.py both`

---

## 📚 Related Documentation
- [Database Schema](./DATABASE.md)
- [API Documentation](./API_DOCUMENTATION.md)
- [Installation Guide](./INSTALLATION.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
