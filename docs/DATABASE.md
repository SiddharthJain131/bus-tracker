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
  "photo": "/photos/user123.jpg",
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
- `photo` (String, Optional) - Profile photo URL
- `address` (String, Optional) - Home address
- `assigned_class` (String, Optional) - For teachers only
- `assigned_section` (String, Optional) - For teachers only
- `student_ids` (Array, Optional) - For parents and teachers
- `is_elevated_admin` (Boolean, Default: false) - Admin permissions

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
  "phone": "+1-555-3001",
  "photo": "backend/photos/students/{student_id}/profile.jpg",
  "photo_path": "backend/photos/students/{student_id}/profile.jpg",
  "attendance_path": "backend/photos/students/{student_id}/attendance",
  "class_name": "Grade 5",
  "section": "A",
  "parent_id": "parent-uuid",
  "teacher_id": "teacher-uuid",
  "bus_id": "bus-uuid",
  "stop_id": "stop-uuid",
  "emergency_contact": "+1-555-9001",
  "remarks": "Allergic to peanuts",
  "embedding": null
}
```

**Fields:**
- `student_id` (String, UUID) - Unique identifier
- `name` (String, Required) - Full name
- `roll_number` (String, Required) - Format: G{class}{section}-{number}
- `phone` (String, Optional) - Student phone number
- `photo` (String, Optional) - Student photo URL (legacy field)
- `photo_path` (String, Optional) - Organized path to profile photo
- `attendance_path` (String, Optional) - Path to attendance scan folder
- `class_name` (String, Required) - Grade/Class
- `section` (String, Required) - Section letter
- `parent_id` (String, Required) - Reference to users collection
- `teacher_id` (String, Optional) - Reference to users collection
- `bus_id` (String, Required) - Reference to buses collection
- `stop_id` (String, Optional) - Reference to stops collection
- `emergency_contact` (String, Optional) - Emergency phone
- `remarks` (String, Optional) - Special notes
- `embedding` (String, Optional) - Face recognition embedding data

**Photo Organization:**
- Profile photos stored in: `backend/photos/students/{student_id}/profile.jpg`
- Attendance scans stored in: `backend/photos/students/{student_id}/attendance/`
- Attendance scan naming: `YYYY-MM-DD_{AM|PM}.jpg`
- See [PHOTO_ORGANIZATION.md](PHOTO_ORGANIZATION.md) for details

**Indexes:**
- `student_id` (Primary)
- `roll_number`
- Compound: `(class_name, section, roll_number)` (Unique)
- `parent_id`
- `teacher_id`
- `bus_id`

**Constraints:**
- Unique combination of (class_name, section, roll_number)

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
  "route_id": "route-uuid"
}
```

**Fields:**
- `bus_id` (String, UUID) - Unique identifier
- `bus_number` (String, Required, Unique) - Display name
- `driver_name` (String, Required) - Driver's full name
- `driver_phone` (String, Required) - Driver contact
- `capacity` (Integer, Required) - Maximum passenger count
- `route_id` (String, Required) - Reference to routes collection

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
  ]
}
```

**Fields:**
- `route_id` (String, UUID) - Unique identifier
- `route_name` (String, Required) - Route display name
- `stop_ids` (Array, Required) - Ordered list of stop IDs
- `map_path` (Array, Optional) - GPS coordinates for drawing route

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
  "order_index": 0
}
```

**Fields:**
- `stop_id` (String, UUID) - Unique identifier
- `stop_name` (String, Required) - Stop display name
- `lat` (Float, Required) - Latitude coordinate
- `lon` (Float, Required) - Longitude coordinate
- `order_index` (Integer, Required) - Position in route sequence

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
  "scan_photo": "/photos/student-uuid/2025-01-15_AM.jpg",
  "scan_timestamp": "2025-01-15T07:58:23.456Z"
}
```

**Fields:**
- `attendance_id` (String, UUID) - Unique identifier
- `student_id` (String, Required) - Reference to students
- `date` (String, Required) - Format: YYYY-MM-DD
- `trip` (String, Required) - "AM" or "PM"
- `status` (String, Required) - One of: "gray", "yellow", "green", "red", "blue"
- `confidence` (Float, Optional) - RFID match confidence (0.0-1.0)
- `last_update` (String, Required) - ISO 8601 timestamp
- `scan_photo` (String, Optional) - Photo URL from scan
- `scan_timestamp` (String, Optional) - ISO 8601 timestamp of scan

**Status Values:**
- `gray` - Not scanned yet
- `yellow` - On board (scanned but not reached)
- `green` - Reached destination
- `red` - Missed bus
- `blue` - Holiday

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
  "tag_id": "RFID-1234",
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
- `tag_id` (String, Required) - RFID tag identifier
- `verified` (Boolean, Required) - Whether scan matched student
- `confidence` (Float, Required) - Match confidence (0.0-1.0)
- `lat` (Float, Required) - GPS latitude
- `lon` (Float, Required) - GPS longitude
- `timestamp` (String, Required) - ISO 8601 timestamp

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
  "message": "Identity mismatch detected",
  "timestamp": "2025-01-15T08:00:00.000Z",
  "type": "mismatch",
  "read": false,
  "student_id": "student-uuid"
}
```

**Fields:**
- `notification_id` (String, UUID) - Unique identifier
- `user_id` (String, Required) - Reference to users
- `message` (String, Required) - Notification text
- `timestamp` (String, Required) - ISO 8601 timestamp
- `type` (String, Required) - "mismatch", "update", "missed", "announcement"
- `read` (Boolean, Default: false) - Read status
- `student_id` (String, Optional) - Related student

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
        └──> notifications (student_id)

users (teacher)
  └──> students (teacher_id)

buses
  ├──> students (bus_id)
  ├──> routes (route_id)
  └──> bus_locations (bus_id)

routes
  └──> stops (stop_ids[])

stops
  └──> students (stop_id)

holidays
  └──> Affects attendance.status
```

---

## Constraints & Rules

### Unique Constraints

1. **students:** (class_name, section, roll_number) must be unique
2. **users:** email must be unique
3. **buses:** bus_number must be unique
4. **holidays:** date must be unique
5. **attendance:** (student_id, date, trip) must be unique

### Foreign Key Rules

1. **students.parent_id** → users.user_id (Required)
2. **students.teacher_id** → users.user_id (Optional)
3. **students.bus_id** → buses.bus_id (Required)
4. **students.stop_id** → stops.stop_id (Optional)
5. **buses.route_id** → routes.route_id (Required)
6. **routes.stop_ids[]** → stops.stop_id (Array)
7. **attendance.student_id** → students.student_id (Required)

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

**On Delete Route:**
- ❌ Block if buses exist with route_id
- ✅ Cascade delete unused stops

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

// Archive old photos
// (Separate script to move photos to archive storage)
```

---

## Performance Optimization

### Indexes

All critical indexes are created automatically on server startup.

**Most Important:**
- `attendance`: Compound index on (student_id, date, trip)
- `students`: Compound index on (class_name, section, roll_number)
- `events`: Index on timestamp for fast recent lookups
- `notifications`: Compound index on (user_id, read, timestamp)

### Query Optimization Tips

1. **Always use indexes** - Include indexed fields in queries
2. **Limit results** - Use `.limit()` for list endpoints
3. **Project fields** - Only fetch needed fields with projection
4. **Use aggregation** - For complex queries with grouping
5. **Cache route data** - Routes don't change frequently

---

## Additional Resources

- **API Documentation:** [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Dependency Rules:** [DEPENDENCY_MANAGEMENT.md](./DEPENDENCY_MANAGEMENT.md)
- **User Guide:** [USER_GUIDE.md](./USER_GUIDE.md)
