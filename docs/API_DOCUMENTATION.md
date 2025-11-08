# 📡 API Documentation

Complete API reference for the Bus Tracker System backend.

## Base URL

**Development:** `http://localhost:8001/api`  
**Production:** `https://your-domain.com/api`

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
  "student_ids": ["student-uuid"],
  "address": "123 Main St"
}
```

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
    "emergency_contact": "+1-555-9001",
    "remarks": "Allergic to peanuts"
  }
]
```

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

Record RFID scan event (used by Raspberry Pi).

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
  "event_id": "event-uuid"
}
```

**Behavior:**
- Creates attendance record with status "yellow" if verified=true
- Creates identity mismatch notification if verified=false
- Idempotent: Duplicate uploads for same timestamp are ignored
- See [RASPBERRY_PI_INTEGRATION.md](./RASPBERRY_PI_INTEGRATION.md) for details

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

Get current GPS location of bus.

**Query Parameters:**
- `bus_id` (required)

**Response (200 OK):**
```json
{
  "bus_id": "uuid",
  "lat": 37.7749,
  "lon": -122.4194,
  "timestamp": "2025-01-15T08:30:00.000Z"
}
```

---

### Update Bus Location

**POST** `/api/update_location`

Update bus GPS location (used by tracking device).

**Request Body:**
```json
{
  "bus_id": "uuid",
  "lat": 37.7749,
  "lon": -122.4194
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "timestamp": "2025-01-15T08:30:00.000Z"
}
```

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
      "order_index": 0
    }
  ],
  "map_path": [
    {"lat": 37.7749, "lon": -122.4194},
    {"lat": 37.7750, "lon": -122.4195}
  ]
}
```

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
    "address": "123 Main St",
    "student_ids": ["student-uuid"],
    "is_elevated_admin": false
  }
]
```

**Note:** `password_hash` is excluded from response.

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

Get notifications for current user.

**Response (200 OK):**
```json
[
  {
    "notification_id": "uuid",
    "user_id": "uuid",
    "message": "Identity mismatch detected for Emma Johnson",
    "timestamp": "2025-01-15T08:00:00.000Z",
    "type": "mismatch",
    "read": false,
    "student_id": "uuid"
  }
]
```

**Types:**
- `"mismatch"` - Identity verification failed
- `"update"` - Student information updated
- `"missed"` - Student missed bus
- `"announcement"` - System announcement

---

### Mark Notification as Read

**PUT** `/api/mark_notification_read/{notification_id}`

Mark notification as read.

**Response (200 OK):**
```json
{
  "status": "updated"
}
```

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
- **Database Schema:** [DATABASE.md](./DATABASE.md)
- **User Guide:** [USER_GUIDE.md](./USER_GUIDE.md)

---

**Interactive API Documentation:** Visit `/docs` when backend is running for Swagger UI.
