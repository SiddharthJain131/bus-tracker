# 🗄️ Database Schema

Complete MongoDB database schema and data models for the Bus Tracker System.

## Database Overview

**Database Name:** `bus_tracker`

**Collections:**
- `users` - Admin, teacher, and parent accounts
- `students` - Student records
- `buses` - Bus fleet information
- `routes` - Bus routes
- `stops` - Route stops with GPS coordinates
- `attendance` - Daily attendance records
- `events` - RFID scan events
- `notifications` - User notifications
- `holidays` - School holiday dates
- `bus_locations` - Real-time bus GPS data
- `email_logs` - Email notification history
- `device_keys` - Raspberry Pi device authentication keys

---

## Collections

### users

**Purpose:** Store user accounts for admins, teachers, and parents.

**Schema:**
```json
{
  "user_id": "uuid",
  "email": "user@school.com",
  "password_hash": "bcrypt_hash",
  "role": "admin|teacher|parent",
  "name": "John Doe",
  "phone": "+1-555-1234",
  "photo": "/api/photos/{role}s/{user_id}.jpg",
  "address": "123 Main St",
  "assigned_class": "Grade 5",
  "assigned_section": "A",
  "student_ids": ["student-uuid-1", "student-uuid-2"],
  "is_elevated_admin": false
}
```

**Fields:**
- `user_id` (String, UUID) - Unique identifier
- `email` (String, Required, Unique) - Login email
- `password_hash` (String, Required) - Bcrypt hashed password
- `role` (String, Required) - One of: "admin", "teacher", "parent"
- `name` (String, Required) - Full name
- `phone` (String, Optional) - Contact phone number
- `photo` (String, Optional) - Profile photo URL path
- `address` (String, Optional) - Home address
- `assigned_class` (String, Optional) - For teachers only
- `assigned_section` (String, Optional) - For teachers only
- `student_ids` (Array, Optional) - For parents and teachers
- `is_elevated_admin` (Boolean, Default: false) - Admin permissions

**Photo Organization:**
- Parent photos: `/api/photos/parents/{user_id}.jpg`
- Teacher photos: `/api/photos/teachers/{user_id}.jpg`
- Admin photos: `/api/photos/admins/{user_id}.jpg`
- See [PHOTO_ORGANIZATION.md](PHOTO_ORGANIZATION.md) for details

**Indexes:**
- `email` (Unique)
- `role`
- `user_id` (Primary)

---

### students

**Purpose:** Store student information and assignments.

**Schema:**
```json
{
  "student_id": "uuid",
  "name": "Emma Johnson",
  "roll_number": "G5A-001",
  "tag_id": "RFID-1001",
  "phone": "+1-555-3001",
  "photo": "/api/photos/students/{student_id}/profile.jpg",
  "embedding": "base64_encoded_face_embedding",
  "class_name": "5",
  "section": "A",
  "parent_id": "parent-uuid",
  "teacher_id": "teacher-uuid",
  "bus_id": "bus-uuid",
  "stop_id": "stop-uuid",
  "emergency_contact": "+1-555-9001",
  "remarks": "Allergic to peanuts"
}
```

**Fields:**
- `student_id` (String, UUID) - Unique identifier
- `name` (String, Required) - Full name
- `roll_number` (String, Required) - Format: G{class}{section}-{number}
- `tag_id` (String, Required) - RFID tag identifier for Pi scanning (e.g., "RFID-1001")
- `phone` (String, Optional) - Student phone number
- `photo` (String, Optional) - Student photo URL path
- `embedding` (String, Optional) - Base64 encoded face recognition embedding (Facenet 128-dim)
- `class_name` (String, Required) - Grade/Class number
- `section` (String, Required) - Section letter
- `parent_id` (String, Required) - Reference to users collection
- `teacher_id` (String, Optional) - Reference to users collection
- `bus_id` (String, Required) - Reference to buses collection
- `stop_id` (String, Optional) - Reference to stops collection
- `emergency_contact` (String, Optional) - Emergency phone
- `remarks` (String, Optional) - Special notes

**Photo Organization:**
- Profile photos: `/api/photos/students/{student_id}/profile.jpg`
- Attendance scans: `/api/photos/students/{student_id}/attendance/YYYY-MM-DD_{AM|PM}.jpg`
- See [PHOTO_ORGANIZATION.md](PHOTO_ORGANIZATION.md) for details

**tag_id Usage:**
- Required field for Raspberry Pi RFID scanning
- Must be unique across all students
- Format: RFID-#### (e.g., RFID-1001, RFID-1002)
- Used exclusively for device authentication during boarding scans
- Mapped to student_id in Pi scanner configuration

**Indexes:**
- `student_id` (Primary)
- `roll_number`
- `tag_id` (Unique)
- Compound: `(class_name, section, roll_number)` (Unique)
- `parent_id`
- `teacher_id`
- `bus_id`

**Constraints:**
- Unique combination of (class_name, section, roll_number)
- Unique tag_id per student

---

### device_keys

**Purpose:** Store Raspberry Pi device authentication keys.

**Schema:**
```json
{
  "device_id": "uuid",
  "bus_id": "bus-uuid",
  "device_name": "Pi-Bus-001",
  "key_hash": "bcrypt_hashed_api_key",
  "created_at": "2025-01-15T10:30:00.000Z"
}
```

**Fields:**
- `device_id` (String, UUID) - Unique device identifier
- `bus_id` (String, Required) - Reference to buses collection (1:1 relationship)
- `device_name` (String, Required) - Friendly device name
- `key_hash` (String, Required) - Bcrypt hashed 64-character API key
- `created_at` (String, Required) - ISO 8601 timestamp of registration

**Security:**
- API keys are 64-character hex tokens (generated via secrets.token_hex(32))
- Keys are bcrypt hashed before storage (never stored in plaintext)
- API key shown only once during device registration
- One device per bus enforced at database level

**Usage:**
- Raspberry Pi devices use X-API-Key header for authentication
- Keys validated on every device-protected endpoint
- Required for /api/scan_event, /api/update_location, /api/students/{id}/embedding, etc.

**Indexes:**
- `device_id` (Primary)
- `bus_id` (Unique)

---

### buses

**Purpose:** Store bus fleet information.

**Schema:**
```json
{
  "bus_id": "uuid",
  "bus_number": "BUS-001",
  "driver_name": "John Driver",
  "driver_phone": "+1-555-7001",
  "capacity": 40,
  "route_id": "route-uuid",
  "remarks": "Optional notes"
}
```

**Fields:**
- `bus_id` (String, UUID) - Unique identifier
- `bus_number` (String, Required, Unique) - Display name
- `driver_name` (String, Required) - Driver's full name
- `driver_phone` (String, Required) - Driver contact
- `capacity` (Integer, Required) - Maximum passenger count
- `route_id` (String, Required) - Reference to routes collection
- `remarks` (String, Optional) - Additional notes

**Indexes:**
- `bus_id` (Primary)
- `bus_number` (Unique)
- `route_id`

---

### routes

**Purpose:** Define bus routes with stops.

**Schema:**
```json
{
  "route_id": "uuid",
  "route_name": "Route A - North District",
  "stop_ids": ["stop-uuid-1", "stop-uuid-2", "stop-uuid-3"],
  "map_path": [
    {"lat": 37.7749, "lon": -122.4194},
    {"lat": 37.7750, "lon": -122.4195}
  ],
  "remarks": "Optional notes"
}
```

**Fields:**
- `route_id` (String, UUID) - Unique identifier
- `route_name` (String, Required) - Route display name
- `stop_ids` (Array, Required) - Ordered list of stop IDs
- `map_path` (Array, Optional) - GPS coordinates for drawing route
- `remarks` (String, Optional) - Additional notes

**Indexes:**
- `route_id` (Primary)

---

### stops

**Purpose:** Store bus stop locations.

**Schema:**
```json
{
  "stop_id": "uuid",
  "stop_name": "Main Gate North",
  "lat": 37.7749,
  "lon": -122.4194,
  "order_index": 0,
  "morning_expected_time": "07:30",
  "evening_expected_time": "15:30"
}
```

**Fields:**
- `stop_id` (String, UUID) - Unique identifier
- `stop_name` (String, Required) - Stop display name
- `lat` (Float, Required) - Latitude coordinate
- `lon` (Float, Required) - Longitude coordinate
- `order_index` (Integer, Required) - Position in route sequence
- `morning_expected_time` (String, Optional) - HH:MM format for AM trips
- `evening_expected_time` (String, Optional) - HH:MM format for PM trips

**Indexes:**
- `stop_id` (Primary)
- Compound: `(lat, lon)`

---

### attendance

**Purpose:** Record daily student attendance.

**Schema:**
```json
{
  "attendance_id": "uuid",
  "student_id": "student-uuid",
  "date": "2025-01-15",
  "trip": "AM",
  "status": "green",
  "confidence": 0.97,
  "last_update": "2025-01-15T07:58:23.456Z",
  "scan_photo": "/api/photos/students/student-uuid/attendance/2025-01-15_AM.jpg",
  "scan_timestamp": "2025-01-15T07:58:23.456Z"
}
```

**Fields:**
- `attendance_id` (String, UUID) - Unique identifier
- `student_id` (String, Required) - Reference to students
- `date` (String, Required) - Format: YYYY-MM-DD
- `trip` (String, Required) - "AM" or "PM"
- `status` (String, Required) - One of: "gray", "yellow", "green", "red", "blue"
- `confidence` (Float, Optional) - Face verification confidence (0.0-1.0)
- `last_update` (String, Required) - ISO 8601 timestamp
- `scan_photo` (String, Optional) - Photo URL from scan
- `scan_timestamp` (String, Optional) - ISO 8601 timestamp of scan

**Status Values:**
- `gray` - Not scanned yet (default)
- `yellow` - Boarding IN (first scan, on board)
- `green` - Boarding OUT (second scan, reached destination)
- `red` - Missed bus (no scan detected)
- `blue` - Holiday (no school)

**Status Workflow:**
1. First RFID scan → Status changes from gray to yellow (Boarding IN)
2. Second RFID scan → Status changes from yellow to green (Boarding OUT)
3. Backend automatically determines status based on scan sequence and time

**Indexes:**
- `attendance_id` (Primary)
- Compound: `(student_id, date, trip)` (Unique)
- `date`
- `status`

---

### events

**Purpose:** Log all RFID scan events.

**Schema:**
```json
{
  "event_id": "uuid",
  "student_id": "student-uuid",
  "tag_id": "RFID-1001",
  "verified": true,
  "confidence": 0.97,
  "lat": 37.7749,
  "lon": -122.4194,
  "timestamp": "2025-01-15T07:58:23.456Z"
}
```

**Fields:**
- `event_id` (String, UUID) - Unique identifier
- `student_id` (String, Required) - Reference to students
- `tag_id` (String, Required) - RFID tag identifier (matches students.tag_id)
- `verified` (Boolean, Required) - Whether face verification passed
- `confidence` (Float, Required) - Face match confidence (0.0-1.0)
- `lat` (Float, Required) - GPS latitude of scan location
- `lon` (Float, Required) - GPS longitude of scan location
- `timestamp` (String, Required) - ISO 8601 timestamp

**Face Verification:**
- Confidence ≥ 0.6 → verified = true
- Confidence < 0.6 → verified = false (triggers mismatch notification)
- Uses DeepFace with Facenet model (128-dimensional embeddings)
- Cosine similarity comparison between current and stored embeddings

**Indexes:**
- `event_id` (Primary)
- `student_id`
- `timestamp`
- `tag_id`

---

### notifications

**Purpose:** Store user notifications.

**Schema:**
```json
{
  "notification_id": "uuid",
  "user_id": "user-uuid",
  "title": "Boarding Confirmed",
  "message": "Emma has boarded BUS-001",
  "timestamp": "2025-01-15T08:00:00.000Z",
  "type": "update",
  "read": false
}
```

**Fields:**
- `notification_id` (String, UUID) - Unique identifier
- `user_id` (String, Required) - Reference to users
- `title` (String, Required) - Notification title
- `message` (String, Optional) - Notification text
- `timestamp` (String, Required) - ISO 8601 timestamp
- `type` (String, Required) - "mismatch", "update", "missed_boarding", "announcement"
- `read` (Boolean, Default: false) - Read status

**Notification Types:**
- `mismatch` - Face verification failed (confidence < 0.6)
- `update` - General updates (boarding confirmed, bus approaching)
- `missed_boarding` - Student didn't board expected bus
- `announcement` - System-wide announcements

**Distribution:**
- Parents receive notifications for their children only
- Teachers receive notifications for their assigned students
- Admins receive all mismatch and system notifications

**Indexes:**
- `notification_id` (Primary)
- Compound: `(user_id, read, timestamp)`

---

### holidays

**Purpose:** Track school holiday dates.

**Schema:**
```json
{
  "holiday_id": "uuid",
  "name": "New Year's Day",
  "date": "2025-01-01",
  "description": "New Year celebration"
}
```

**Fields:**
- `holiday_id` (String, UUID) - Unique identifier
- `name` (String, Required) - Holiday name
- `date` (String, Required) - Format: YYYY-MM-DD
- `description` (String, Optional) - Additional details

**Indexes:**
- `holiday_id` (Primary)
- `date` (Unique)

---

### bus_locations

**Purpose:** Track real-time bus GPS positions.

**Schema:**
```json
{
  "bus_id": "bus-uuid",
  "lat": 37.7749,
  "lon": -122.4194,
  "timestamp": "2025-01-15T08:30:00.000Z"
}
```

**Fields:**
- `bus_id` (String, Primary) - Reference to buses
- `lat` (Float, Required) - Current latitude
- `lon` (Float, Required) - Current longitude
- `timestamp` (String, Required) - Last update time

**Indexes:**
- `bus_id` (Primary)
- `timestamp`

---

### email_logs

**Purpose:** Log email notifications sent.

**Schema:**
```json
{
  "email_id": "uuid",
  "recipient_email": "parent@school.com",
  "recipient_name": "John Parent",
  "subject": "Student Information Updated",
  "body": "...",
  "timestamp": "2025-01-15T09:00:00.000Z",
  "student_id": "student-uuid",
  "user_id": "user-uuid"
}
```

**Fields:**
- `email_id` (String, UUID) - Unique identifier
- `recipient_email` (String, Required) - To address
- `recipient_name` (String, Required) - Recipient name
- `subject` (String, Required) - Email subject
- `body` (String, Required) - Email content
- `timestamp` (String, Required) - Send time
- `student_id` (String, Optional) - Related student
- `user_id` (String, Optional) - Related user

**Indexes:**
- `email_id` (Primary)
- `timestamp`
- `recipient_email`

---

## Relationships

```
users (parent)
  └──> students (parent_id)
        ├──> attendance (student_id)
        ├──> events (student_id)
        └──> notifications (via parent's user_id)

users (teacher)
  └──> students (teacher_id)
        └──> notifications (via teacher's user_id)

buses
  ├──> students (bus_id)
  ├──> routes (route_id)
  ├──> bus_locations (bus_id)
  └──> device_keys (bus_id) - 1:1 relationship

routes
  └──> stops (stop_ids[])

stops
  └──> students (stop_id)

holidays
  └──> Affects attendance.status (blue for holidays)

students.tag_id
  └──> Used by Raspberry Pi for RFID scanning
        └──> Creates events with matching tag_id
```

---

## Constraints & Rules

### Unique Constraints

1. **students:** (class_name, section, roll_number) must be unique
2. **students:** tag_id must be unique
3. **users:** email must be unique
4. **buses:** bus_number must be unique
5. **holidays:** date must be unique
6. **attendance:** (student_id, date, trip) must be unique
7. **device_keys:** bus_id must be unique (1:1 with buses)

### Foreign Key Rules

1. **students.parent_id** → users.user_id (Required)
2. **students.teacher_id** → users.user_id (Optional)
3. **students.bus_id** → buses.bus_id (Required)
4. **students.stop_id** → stops.stop_id (Optional)
5. **buses.route_id** → routes.route_id (Required)
6. **routes.stop_ids[]** → stops.stop_id (Array)
7. **attendance.student_id** → students.student_id (Required)
8. **device_keys.bus_id** → buses.bus_id (Required, Unique)
9. **events.tag_id** → students.tag_id (For validation)

### Cascade Rules

**On Delete User (Parent):**
- ❌ Block if students exist with parent_id
- ✅ Cascade delete notifications

**On Delete User (Teacher):**
- ❌ Block if students exist with teacher_id
- ✅ Cascade delete notifications

**On Delete Student:**
- ❌ Block if attendance records exist
- ✅ Cascade delete notifications

**On Delete Bus:**
- ❌ Block if students exist with bus_id
- ✅ Cascade delete associated device_key

**On Delete Route:**
- ❌ Block if buses exist with route_id

**On Delete Stop:**
- ❌ Block if students exist with stop_id
- ❌ Block if routes contain stop_id

---

## Data Validation

### Email Format
- Pattern: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`

### Phone Format
- Pattern: `^\+?1?\d{10,14}$`
- Example: `+1-555-1234` or `5551234567`

### Roll Number Format
- Pattern: `^G\d+[A-Z]-\d{3}$`
- Example: `G5A-001`, `G10B-025`

### tag_id Format
- Pattern: `^RFID-\d{4}$`
- Example: `RFID-1001`, `RFID-1020`
- Must be unique across all students

### Date Format
- ISO 8601: `YYYY-MM-DD`
- Example: `2025-01-15`

### Timestamp Format
- ISO 8601 with timezone: `YYYY-MM-DDTHH:MM:SS.sssZ`
- Example: `2025-01-15T07:58:23.456Z`

### GPS Coordinates
- Latitude: -90.0 to 90.0
- Longitude: -180.0 to 180.0

---

## Query Patterns

### Get Parent's Children
```javascript
db.students.find({
  parent_id: "parent-uuid"
})
```

### Get Teacher's Students
```javascript
db.students.find({
  teacher_id: "teacher-uuid"
})
```

### Get Student by RFID Tag
```javascript
db.students.findOne({
  tag_id: "RFID-1001"
})
```

### Get Student Attendance for Month
```javascript
db.attendance.find({
  student_id: "student-uuid",
  date: {
    $gte: "2025-01-01",
    $lte: "2025-01-31"
  }
})
```

### Get Device by API Key
```javascript
// Hash the provided key first, then:
db.device_keys.find({}).forEach(device => {
  if (bcrypt.checkpw(providedKey, device.key_hash)) {
    return device;
  }
});
```

### Get Bus Route with Stops
```javascript
// 1. Get bus
const bus = db.buses.findOne({bus_id: "bus-uuid"})

// 2. Get route
const route = db.routes.findOne({route_id: bus.route_id})

// 3. Get stops
const stops = db.stops.find({
  stop_id: {$in: route.stop_ids}
}).sort({order_index: 1})
```

### Check Bus Capacity
```javascript
// Count students on bus
const count = db.students.countDocuments({
  bus_id: "bus-uuid"
})

// Compare with bus capacity
const bus = db.buses.findOne({bus_id: "bus-uuid"})
if (count >= bus.capacity) {
  // Bus is full
}
```

---

## Backup & Maintenance

### Backup Command
```bash
mongodump --db bus_tracker --out /backup/$(date +%Y%m%d)
```

### Restore Command
```bash
mongorestore --db bus_tracker /backup/20250115/bus_tracker
```

### Cleanup Old Data
```javascript
// Delete attendance older than 90 days
db.attendance.deleteMany({
  date: {$lt: "2024-10-15"}
})

// Delete old events (keep 30 days)
const cutoffDate = new Date();
cutoffDate.setDate(cutoffDate.getDate() - 30);
db.events.deleteMany({
  timestamp: {$lt: cutoffDate.toISOString()}
})
```

---

## Performance Optimization

### Indexes

All critical indexes are created automatically on server startup.

**Most Important:**
- `attendance`: Compound index on (student_id, date, trip)
- `students`: Compound index on (class_name, section, roll_number)
- `students`: Index on tag_id (unique)
- `events`: Index on timestamp for fast recent lookups
- `events`: Index on tag_id for RFID validation
- `notifications`: Compound index on (user_id, read, timestamp)
- `device_keys`: Index on bus_id (unique)

### Query Optimization Tips

1. **Always use indexes** - Include indexed fields in queries
2. **Limit results** - Use `.limit()` for list endpoints
3. **Project fields** - Only fetch needed fields with projection
4. **Use aggregation** - For complex queries with grouping
5. **Cache route data** - Routes don't change frequently
6. **Cache device keys** - Validate API keys with in-memory cache

---

## Additional Resources

- **API Documentation:** [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Raspberry Pi Integration:** [RASPBERRY_PI_INTEGRATION.md](./RASPBERRY_PI_INTEGRATION.md)
- **User Guide:** [USER_GUIDE.md](./USER_GUIDE.md)
