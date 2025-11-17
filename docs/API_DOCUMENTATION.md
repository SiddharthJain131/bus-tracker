# 📡 API Documentation

Complete API reference for the Bus Tracker System backend.

## Base URL

Use the `BACKEND_BASE_URL` environment variable defined in your backend `.env` file:

**API Endpoint:** `${BACKEND_BASE_URL}/api`

## Authentication

Most endpoints require authentication via session cookies.

### Login

**POST** `/api/auth/login`

Authenticate user and create session.

**Request Body:**
```json
{
  "email": "admin@school.com",
  "password": "password"
}
```

**Response (200 OK):**
```json
{
  "user_id": "uuid",
  "email": "admin@school.com",
  "role": "admin",
  "name": "James Anderson",
  "phone": "+1-555-9001",
  "photo": "/photos/admins/uuid.jpg",
  "student_ids": [],
  "is_elevated_admin": true
}
```

**Sets Cookie:** `session_token` (httpOnly, sameSite=lax, maxAge=24h)

---

### Logout

**POST** `/api/auth/logout`

End user session.

**Response (200 OK):**
```json
{
  "message": "Logged out"
}
```

---

### Get Current User

**GET** `/api/auth/me`

Get currently authenticated user info.

**Response (200 OK):**
```json
{
  "user_id": "uuid",
  "email": "user@school.com",
  "role": "parent",
  "name": "John Parent",
  "phone": "+1-555-1001",
  "photo": "/photos/parents/uuid.jpg",
  "student_ids": ["student-uuid"],
  "address": "123 Main St"
}
```

**Note:** Returns `photo` URL for profile photo display.

---

## Students API

### List Students

**GET** `/api/students`

Get list of students (filtered by role).

**Access:**
- Parents: Only their children
- Teachers: Only assigned students
- Admins: All students

**Response (200 OK):**
```json
[
  {
    "student_id": "uuid",
    "name": "Emma Johnson",
    "roll_number": "G5A-001",
    "class_name": "Grade 5",
    "section": "A",
    "phone": "+1-555-3001",
    "parent_id": "uuid",
    "parent_name": "John Parent",
    "teacher_id": "uuid",
    "teacher_name": "Mary Teacher",
    "bus_id": "uuid",
    "bus_number": "BUS-001",
    "stop_id": "uuid",
    "stop_name": "Main Gate",
    "photo_url": "/photos/students/uuid/profile.jpg",
    "emergency_contact": "+1-555-9001",
    "remarks": "Allergic to peanuts"
  }
]
```

**Note:** Returns `photo_url` for profile photo display.

---

### Get Student Details

**GET** `/api/students/{student_id}`

Get complete student information.

**Response (200 OK):**
```json
{
  "student_id": "uuid",
  "name": "Emma Johnson",
  "roll_number": "G5A-001",
  "class_name": "Grade 5",
  "section": "A",
  "phone": "+1-555-3001",
  "parent_id": "uuid",
  "parent_name": "John Parent",
  "parent_email": "parent@school.com",
  "teacher_id": "uuid",
  "teacher_name": "Mary Teacher",
  "bus_id": "uuid",
  "bus_number": "BUS-001",
  "route_id": "uuid",
  "stop_id": "uuid",
  "stop_name": "Main Gate",
  "photo_url": "/photos/students/uuid/profile.jpg",
  "emergency_contact": "+1-555-9001",
  "remarks": "Allergic to peanuts"
}
```

---

### Create Student

**POST** `/api/students` (Admin only)

Create new student record.

**Request Body:**
```json
{
  "name": "New Student",
  "roll_number": "G5A-006",
  "class_name": "Grade 5",
  "section": "A",
  "phone": "+1-555-1234",
  "parent_id": "uuid",
  "teacher_id": "uuid",
  "bus_id": "uuid",
  "stop_id": "uuid",
  "emergency_contact": "+1-555-9999",
  "remarks": "Optional notes"
}
```

**Response (200 OK):**
```json
{
  "status": "created",
  "student_id": "new-uuid",
  "capacity_warning": "Warning: Bus BUS-001 capacity (40) will be exceeded. Current: 40, After: 41"
}
```

**Note:** Returns capacity_warning if bus is over capacity (doesn't block creation).

---

### Update Student

**PUT** `/api/students/{student_id}` (Admin only)

Update student information.

**Request Body:**
```json
{
  "name": "Updated Name",
  "phone": "+1-555-5678",
  "bus_id": "new-bus-uuid",
  "remarks": "Updated notes"
}
```

**Response (200 OK):**
```json
{
  "status": "updated",
  "capacity_warning": "..." // If bus capacity exceeded
}
```

**Side Effects:**
- Email notification sent to parent
- Attendance records remain unchanged
- Parent reassignment updates parent's student_ids array

---

### Delete Student

**DELETE** `/api/students/{student_id}` (Admin only)

Delete student record.

**Response (200 OK):**
```json
{
  "status": "deleted",
  "student_id": "uuid",
  "cascaded_notifications": 3
}
```

**Response (409 Conflict):**
```json
{
  "detail": "Cannot delete student. 12 attendance record(s) exist. Please delete attendance records first or archive the student."
}
```

**Dependency Rules:**
- ❌ Blocked if attendance records exist
- ✅ Cascades delete notifications

---

## Attendance API

### Get Monthly Attendance

**GET** `/api/get_attendance`

Get attendance grid for a student for specific month.

**Query Parameters:**
- `student_id` (required) - Student UUID
- `month` (required) - Format: YYYY-MM

**Example:** `/api/get_attendance?student_id=uuid&month=2025-01`

**Response (200 OK):**
```json
{
  "grid": [
    {
      "date": "2025-01-01",
      "day": 1,
      "am_status": "green",
      "pm_status": "green",
      "am_confidence": 0.97,
      "pm_confidence": 0.95,
      "am_scan_photo": "/photos/uuid/2025-01-01_AM.jpg",
      "am_scan_timestamp": "2025-01-01T07:58:23.456Z",
      "pm_scan_photo": "/photos/uuid/2025-01-01_PM.jpg",
      "pm_scan_timestamp": "2025-01-01T15:15:10.123Z"
    }
  ],
  "summary": "42 / 60 sessions"
}
```

**Status Values:**
- `"green"` - Reached (clickable in UI)
- `"yellow"` - On board
- `"red"` - Missed
- `"blue"` - Holiday
- `"gray"` - Not scanned

---

### Record Scan Event

**POST** `/api/scan_event`

Record RFID scan event (used by Raspberry Pi). Requires X-API-Key header.

**Request Body:**
```json
{
  "student_id": "uuid",
  "tag_id": "RFID-1234",
  "verified": true,
  "confidence": 0.97,
  "lat": 37.7749,
  "lon": -122.4194,
  "photo_url": "/photos/uuid/2025-01-15_AM.jpg"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "event_id": "event-uuid",
  "attendance_status": "yellow"
}
```

**Behavior:**
- First scan: Creates attendance with status "yellow" (On Board)
- Second scan: Updates to status "green" (Reached)
- Status determined automatically by backend based on time and scan sequence
- Creates identity mismatch notification if verified=false
- Idempotent: Duplicate uploads for same timestamp are ignored

---

## Bus & Route API

### List Buses

**GET** `/api/buses`

Get all buses with route information.

**Response (200 OK):**
```json
[
  {
    "bus_id": "uuid",
    "bus_number": "BUS-001",
    "driver_name": "John Driver",
    "driver_phone": "+1-555-7001",
    "capacity": 40,
    "route_id": "uuid",
    "route_name": "Route A - North District"
  }
]
```

---

### Get Bus Details

**GET** `/api/buses/{bus_id}`

Get complete bus information.

**Response (200 OK):**
```json
{
  "bus_id": "uuid",
  "bus_number": "BUS-001",
  "driver_name": "John Driver",
  "driver_phone": "+1-555-7001",
  "capacity": 40,
  "route_id": "uuid",
  "route_data": {
    "route_name": "Route A",
    "stops": [...],
    "map_path": [...]
  }
}
```

---

### Get Bus Location

**GET** `/api/get_bus_location`

Get current GPS location of bus. Requires X-API-Key header.

**Query Parameters:**
- `bus_number` (required) - Bus number (e.g., "BUS-001")

**Response (200 OK - GPS Available):**
```json
{
  "bus_number": "BUS-001",
  "lat": 37.7749,
  "lon": -122.4194,
  "timestamp": "2025-11-17T14:00:00Z",
  "is_missing": false,
  "is_stale": false
}
```

**Response (200 OK - GPS Unavailable):**
```json
{
  "bus_number": "BUS-001",
  "lat": null,
  "lon": null,
  "timestamp": "2025-11-17T14:00:00Z",
  "is_missing": true,
  "is_stale": false
}
```

**Response Flags:**
- `is_missing`: true if GPS coordinates are null
- `is_stale`: true if location not updated in last 60 seconds

**Frontend Behavior:**
- When `is_missing: true`, displays 🔴❓ indicator
- When `is_stale: true`, shows timestamp warning
- Map keeps bus at last known position when coordinates null

---

### Update Bus Location

**POST** `/api/update_location`

Update bus GPS location (used by tracking device). Requires X-API-Key header.

**Supports GPS Fallback:** Accepts `null` values for `lat`/`lon` when GPS unavailable.

**Request Body (GPS Available):**
```json
{
  "bus_number": "BUS-001",
  "lat": 37.7749,
  "lon": -122.4194,
  "timestamp": "2025-11-17T14:00:00Z"
}
```

**Request Body (GPS Unavailable):**
```json
{
  "bus_number": "BUS-001",
  "lat": null,
  "lon": null,
  "timestamp": "2025-11-17T14:00:00Z"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "bus_number": "BUS-001",
  "timestamp": "2025-11-17T14:00:00Z",
  "location_updated": true
}
```

**Notes:**
- System accepts and stores null coordinates
- Frontend displays GPS unavailable indicator (🔴❓)
- Attendance recording continues normally without GPS
- No errors or failures when GPS unavailable

---

### Get Route Details

**GET** `/api/routes/{route_id}`

Get complete route with stops.

**Response (200 OK):**
```json
{
  "route_id": "uuid",
  "route_name": "Route A - North District",
  "stops": [
    {
      "stop_id": "uuid",
      "stop_name": "Main Gate North",
      "lat": 37.7749,
      "lon": -122.4194,
      "order_index": 0,
      "morning_expected_time": "07:30",
      "evening_expected_time": "15:30"
    }
  ],
  "map_path": [
    {"lat": 37.7749, "lon": -122.4194},
    {"lat": 37.7750, "lon": -122.4195}
  ]
}
```

**Note:** `morning_expected_time` and `evening_expected_time` are optional fields for automated attendance status determination.

---

### Get Bus Stops

**GET** `/api/buses/{bus_id}/stops`

Get all stops for a specific bus (via its route).

**Response (200 OK):**
```json
[
  {
    "stop_id": "uuid",
    "stop_name": "Main Gate North",
    "lat": 37.7749,
    "lon": -122.4194,
    "order_index": 0
  }
]
```

**Response (404 Not Found):**
```json
{
  "detail": "Bus not found"
}
```

---

## Users API

### List Users

**GET** `/api/users` (Admin only)

Get all users in the system.

**Response (200 OK):**
```json
[
  {
    "user_id": "uuid",
    "email": "user@school.com",
    "role": "parent",
    "name": "John Parent",
    "phone": "+1-555-1001",
    "photo_url": "/photos/parents/uuid.jpg",
    "address": "123 Main St",
    "student_ids": ["student-uuid"],
    "is_elevated_admin": false
  }
]
```

**Note:** `password_hash` is excluded from response. Returns `photo_url` for profile photos.

---

### Update User

**PUT** `/api/users/{user_id}` (Admin only)

Update user information.

**Request Body:**
```json
{
  "name": "Updated Name",
  "phone": "+1-555-9999",
  "address": "456 Oak Ave",
  "assigned_class": "Grade 6",
  "assigned_section": "B"
}
```

**Response (200 OK):**
```json
{
  "status": "updated"
}
```

**Restrictions:**
- Non-elevated admins cannot edit elevated admins (403 Forbidden)

---

### Delete User

**DELETE** `/api/users/{user_id}` (Admin only)

Delete user account.

**Response (409 Conflict) - Parent with students:**
```json
{
  "detail": "Cannot delete parent. 2 student(s) are linked to this parent. Please reassign or delete students first."
}
```

**Response (409 Conflict) - Teacher with students:**
```json
{
  "detail": "Cannot delete teacher. 5 student(s) are assigned to this teacher. Please reassign students first."
}
```

---

### Get All Parents

**GET** `/api/parents/all` (Admin only)

Get all parent accounts (for linking multiple children).

**Response (200 OK):**
```json
[
  {
    "user_id": "uuid",
    "name": "John Parent",
    "email": "parent@school.com",
    "phone": "+1-555-1001",
    "student_ids": ["student1-uuid", "student2-uuid"]
  }
]
```

---

### Get Unlinked Parents

**GET** `/api/parents/unlinked` (Admin only)

Get parent accounts with no students linked.

**Response (200 OK):**
```json
[
  {
    "user_id": "uuid",
    "name": "Jane Parent",
    "email": "parent2@school.com",
    "student_ids": []
  }
]
```

---

## Notifications API

### Get Notifications

**GET** `/api/get_notifications`

Get notifications for current user (filtered by user_id).

**Response (200 OK):**
```json
[
  {
    "notification_id": "uuid",
    "user_id": "uuid",
    "title": "Bus Approaching",
    "message": "BUS-001 is approaching your child's stop. Estimated arrival in 5 minutes.",
    "timestamp": "2025-01-15T08:00:00.000Z",
    "type": "update",
    "read": false
  }
]
```

**Types:**
- `"mismatch"` - Identity verification failed
- `"update"` - General updates (bus alerts, system messages)
- `"missed"` - Student missed bus
- `"announcement"` - System announcement

**Permission Model:**
- Each user sees only their own notifications
- Filtered by `user_id` matching authenticated user
- Limited to 50 most recent notifications
- Sorted by timestamp (newest first)

---

### Mark Notification as Read

**POST** `/api/mark_notification_read`

Mark notification as read.

**Query Parameters:**
- `notification_id` (required)

**Response (200 OK):**
```json
{
  "status": "success"
}
```

**Behavior:**
- Only marks notification if it belongs to authenticated user
- Idempotent: Can be called multiple times

---

## Holidays API

### List Holidays

**GET** `/api/admin/holidays` (Admin only)

Get all holidays.

**Response (200 OK):**
```json
[
  {
    "holiday_id": "uuid",
    "name": "New Year's Day",
    "date": "2025-01-01",
    "description": "New Year celebration"
  }
]
```

---

### Create Holiday

**POST** `/api/admin/holidays` (Admin only)

Create new holiday.

**Request Body:**
```json
{
  "name": "Spring Break",
  "date": "2025-03-15",
  "description": "Optional description"
}
```

**Response (200 OK):**
```json
{
  "holiday_id": "new-uuid",
  "name": "Spring Break",
  "date": "2025-03-15"
}
```

---

### Update Holiday

**PUT** `/api/admin/holidays/{holiday_id}` (Admin only)

Update existing holiday.

**Request Body:**
```json
{
  "name": "Updated Holiday Name",
  "date": "2025-03-16",
  "description": "Updated description"
}
```

**Response (200 OK):**
```json
{
  "status": "updated"
}
```

---

### Delete Holiday

**DELETE** `/api/admin/holidays/{holiday_id}` (Admin only)

Delete holiday.

**Response (200 OK):**
```json
{
  "status": "deleted"
}
```

---

## Teacher Endpoints

### Get Teacher's Students

**GET** `/api/teacher/students` (Teacher only)

Get all students assigned to the authenticated teacher.

**Response (200 OK):**
```json
[
  {
    "student_id": "uuid",
    "name": "Emma Johnson",
    "roll_number": "G5A-001",
    "parent_name": "John Parent",
    "bus_number": "BUS-001",
    "am_status": "green",
    "pm_status": "yellow"
  }
]
```

**Note:** Includes today's AM/PM status for quick reference.

---

## Parent Endpoints

### Get Parent's Students

**GET** `/api/parent/students` (Parent only)

Get all children of authenticated parent.

**Response (200 OK):**
```json
[
  {
    "student_id": "uuid",
    "name": "Emma Johnson",
    "class_name": "Grade 5",
    "section": "A",
    "bus_id": "uuid",
    "bus_number": "BUS-001"
  }
]
```

---

## Device Authentication

### Register Device

**POST** `/api/device/register` (Admin only)

Register new Raspberry Pi device and generate API key.

**Request Body:**
```json
{
  "bus_id": "uuid",
  "device_name": "Bus-001-Scanner"
}
```

**Response (200 OK):**
```json
{
  "device_id": "uuid",
  "bus_id": "uuid",
  "bus_number": "BUS-001",
  "device_name": "Bus-001-Scanner",
  "api_key": "34f135326bbc30ff28bd37e14670e034240eefd9ac76c586e6cb17de6736cbac",
  "warning": "Store this API key securely. It cannot be retrieved later."
}
```

**Behavior:**
- Generates 64-character API key using `secrets.token_hex(32)`
- Keys are bcrypt hashed before storage
- One device per bus (1:1 relationship)
- Duplicate registration for same bus returns 400

---

### List Devices

**GET** `/api/device/list` (Admin only)

Get all registered devices.

**Response (200 OK):**
```json
[
  {
    "device_id": "uuid",
    "bus_id": "uuid",
    "bus_number": "BUS-001",
    "device_name": "Bus-001-Scanner",
    "created_at": "2025-01-15T08:00:00.000Z"
  }
]
```

**Note:** `key_hash` excluded from response for security.

---

### Device-Protected Endpoints

The following endpoints require `X-API-Key` header:

- **POST** `/api/scan_event` - Record RFID scan
- **POST** `/api/update_location` - Update bus GPS
- **GET** `/api/get_bus_location` - Get bus location
- **GET** `/api/students/{id}/embedding` - Get face recognition data
- **GET** `/api/students/{id}/photo` - Get student photo

**Authentication:**
```bash
curl -H "X-API-Key: your_64_char_api_key" \
     -X POST https://api.example.com/api/scan_event
```

**Error Response (403 Forbidden):**
```json
{
  "detail": "Invalid or missing API key"
}
```

---

## Demo & Simulation

### Simulate Scan

**POST** `/api/demo/simulate_scan`

Simulate RFID scan for testing.

**Request Body:**
```json
{
  "student_id": "uuid"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "event_id": "uuid",
  "student_name": "Emma Johnson",
  "verified": true
}
```

---

### Simulate Bus Movement

**POST** `/api/demo/simulate_bus_movement`

Simulate bus GPS movement.

**Request Body:**
```json
{
  "bus_id": "uuid"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "bus_id": "uuid",
  "new_location": {
    "lat": 37.7750,
    "lon": -122.4195
  }
}
```

---

## Error Responses

### Common Error Codes

**400 Bad Request:**
```json
{
  "detail": "Invalid request format"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden:**
```json
{
  "detail": "Access denied"
}
```

**404 Not Found:**
```json
{
  "detail": "Resource not found"
}
```

**409 Conflict:**
```json
{
  "detail": "Cannot delete entity. Dependencies exist."
}
```

**422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

**Limits:**
- Authentication: 10 requests/minute
- General API: 100 requests/minute per user
- Scan events: 100 requests/minute per device

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642089600
```

---

## Additional Resources

- **Raspberry Pi Integration:** [RASPBERRY_PI_INTEGRATION.md](./RASPBERRY_PI_INTEGRATION.md)
- **Device API Testing:** [API_TEST_DEVICE.md](./API_TEST_DEVICE.md)
- **Database Schema:** [DATABASE.md](./DATABASE.md)
- **User Guide:** [USER_GUIDE.md](./USER_GUIDE.md)

---

**Interactive API Documentation:** Visit `/docs` when backend is running for Swagger UI.