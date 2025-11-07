# 🚌 Bus Tracker System

A comprehensive school bus tracking and student attendance management system with real-time GPS monitoring, RFID-based student verification, and role-based dashboards.

## 📋 Project Overview

The Bus Tracker System is a full-stack application designed to help schools manage student transportation efficiently. It provides real-time bus tracking, automated attendance recording, and instant notifications for parents, teachers, and administrators.

### Key Features

- **Real-time Bus Tracking**: Live GPS tracking of all school buses on interactive maps
- **RFID-based Attendance**: Automated student attendance using RFID card scanning
- **Role-based Dashboards**: Separate interfaces for Parents, Teachers, and Admins
- **Instant Notifications**: Alerts for identity mismatches, route changes, and important updates
- **Route Visualization**: Interactive maps showing bus routes with stop markers
- **Monthly Attendance**: Color-coded attendance grids with AM/PM tracking
- **Demo Simulation**: Built-in tools for testing and demonstration

## 🏗️ Technology Stack

### Frontend
- **React** (v18+) - Modern UI framework
- **Tailwind CSS** - Utility-first styling
- **Leaflet** - Interactive maps and GPS visualization
- **Radix UI** - Accessible component primitives
- **Lucide React** - Beautiful icon library

### Backend
- **FastAPI** - High-performance Python API framework
- **Motor** - Async MongoDB driver for Python
- **bcrypt** - Secure password hashing
- **uvicorn** - ASGI server

### Database
- **MongoDB** - NoSQL database for flexible data storage

## 📦 Installation

### Prerequisites

- Python 3.9+
- Node.js 16+
- MongoDB (local or cloud instance)
- yarn package manager

### Step 1: Clone the Repository

```bash
git clone https://github.com/SiddharthJain131/bus-tracker.git
cd bus-tracker
```

### Step 2: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=bus_tracker
EOF
```

### Step 3: Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
yarn install

# Create .env file
cat > .env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
EOF
```

### Step 4: Seed the Database

```bash
# From the backend directory
cd ../backend
python seed_data.py
```

This will populate the database with demo data including:
- 2 Admin accounts
- 3 Teacher accounts (for different classes)
- 15 Parent accounts
- 15 Students with roll numbers
- 4 Buses with routes
- 4 Routes with 20 stops
- Sample attendance records
- Holiday dates

### Step 5: Start the Application

**Option 1: Using Supervisor (Recommended for production)**

```bash
# From the project root
sudo supervisorctl restart all
```

**Option 2: Manual Start (Development)**

```bash
# Terminal 1 - Start Backend
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 - Start Frontend
cd frontend
yarn start
```

The application will be available at:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8001`

## 🔐 Demo Login Credentials

### Admin Accounts

| Email | Password | Name | Role |
|-------|----------|------|------|
| admin@school.com | password | James Anderson | Primary Administrator |
| admin2@school.com | password | Patricia Williams | Secondary Administrator |

### Teacher Accounts

| Email | Password | Name | Class/Section | Students |
|-------|----------|------|---------------|----------|
| teacher@school.com | password | Mary Johnson | Grade 5 - A | 5 students |
| teacher2@school.com | password | Robert Smith | Grade 6 - B | 5 students |
| teacher3@school.com | password | Sarah Wilson | Grade 4 - A | 5 students |

### Parent Accounts

| Email | Password | Name | Child |
|-------|----------|------|-------|
| parent@school.com | password | John Parent | Emma Johnson (Grade 5-A) |
| parent2@school.com | password | Sarah Smith | Liam Smith (Grade 5-A) |
| parent3@school.com | password | Michael Brown | Sophia Brown (Grade 5-A) |
| parent4@school.com | password | Emily Davis | Noah Davis (Grade 5-A) |
| parent5@school.com | password | David Martinez | Olivia Martinez (Grade 5-A) |
| parent6@school.com | password | Jennifer Wilson | Ethan Wilson (Grade 6-B) |
| parent7@school.com | password | Christopher Taylor | Ava Taylor (Grade 6-B) |
| parent8@school.com | password | Amanda Garcia | Mason Garcia (Grade 6-B) |
| parent9@school.com | password | Matthew Rodriguez | Isabella Rodriguez (Grade 6-B) |
| parent10@school.com | password | Jessica Lee | Lucas Lee (Grade 6-B) |
| parent11@school.com | password | Daniel Harris | Mia Harris (Grade 4-A) |
| parent12@school.com | password | Lisa Clark | Benjamin Clark (Grade 4-A) |
| parent13@school.com | password | Kevin Lewis | Charlotte Lewis (Grade 4-A) |
| parent14@school.com | password | Nancy Walker | James Walker (Grade 4-A) |
| parent15@school.com | password | Steven Hall | Amelia Hall (Grade 4-A) |

## 📊 Data Model Overview

### Core Entities and Relationships

```
USERS (roles: admin, teacher, parent)
  ├── Admins → Full system access
  ├── Teachers → Assigned to class/section → View assigned students
  └── Parents → Linked to student_ids → View own children

STUDENTS
  ├── student_id (UUID)
  ├── roll_number (e.g., "G5A-001")
  ├── class_name & section
  ├── parent_id → USERS (parent)
  ├── teacher_id → USERS (teacher)
  ├── bus_id → BUSES
  └── stop_id → STOPS

BUSES
  ├── bus_id (UUID)
  ├── bus_number (e.g., "BUS-001")
  ├── driver_name & driver_phone
  └── route_id → ROUTES

ROUTES
  ├── route_id (UUID)
  ├── route_name
  ├── stop_ids[] → STOPS
  └── map_path[] (lat/lon coordinates)

STOPS
  ├── stop_id (UUID)
  ├── stop_name
  ├── lat & lon (GPS coordinates)
  └── order_index

ATTENDANCE
  ├── attendance_id (UUID)
  ├── student_id → STUDENTS
  ├── date & trip (AM/PM)
  ├── status (green/yellow/red/blue)
  └── confidence score

NOTIFICATIONS
  ├── notification_id (UUID)
  ├── user_id → USERS
  ├── message & event_type
  └── read status
```

## 🚀 Accessing Dashboards

### Parent Dashboard (`/parent`)

**Features:**
- View all your children's information
- Live bus tracking on interactive map
- Toggle route visualization
- Monthly attendance calendar (AM/PM)
- Student details and bus information
- Real-time notifications

**Access:** Login with any parent account and you'll be automatically redirected to the parent dashboard.

### Teacher Dashboard (`/teacher`)

**Features:**
- View all assigned students (based on class/section)
- Student list with parent info and bus numbers
- Today's AM/PM attendance status
- Search and filter students
- View student details with monthly attendance
- Route visualization for student buses
- Notifications for your students

**Access:** Login with any teacher account. Teachers only see students from their assigned class and section.

### Admin Dashboard (`/admin`)

**Features:**
- Complete system overview
- Manage students (CRUD operations)
- Manage users (teachers, parents, admins)
- Manage buses and routes
- View and edit holidays
- System statistics
- Demo simulation tools

**Access:** Login with admin credentials. Admins have full access to all system features.

## 🧪 How to Run Seeding

### First Time Setup

```bash
cd backend
python seed_data.py
```

### Reset Database and Reseed

```bash
# The seed script automatically clears existing data
# Just run it again to reset
python seed_data.py
```

### Verify Seeded Data

```bash
# Check MongoDB collections
mongosh
use bus_tracker
db.users.countDocuments()      # Should show 20 users
db.students.countDocuments()   # Should show 15 students
db.buses.countDocuments()      # Should show 4 buses
db.routes.countDocuments()     # Should show 4 routes
```

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user info

### Students
- `GET /api/students` - List students (role-based filtering)
- `GET /api/students/{id}` - Get student details
- `POST /api/students` - Create student (admin only)
- `PUT /api/students/{id}` - Update student (admin only)
- `DELETE /api/students/{id}` - Delete student (admin only)

### Attendance
- `GET /api/get_attendance` - Get monthly attendance grid
- `POST /api/scan_event` - Record RFID scan event

### Buses & Routes
- `GET /api/buses` - List all buses
- `GET /api/buses/{id}` - Get bus details
- `GET /api/routes/{id}` - Get route with stops
- `GET /api/get_bus_location` - Get current bus location
- `POST /api/update_location` - Update bus GPS location

### Users
- `GET /api/users` - List users (admin only)
- `PUT /api/users/{id}` - Update user (admin only)

### Notifications
- `GET /api/get_notifications` - Get user notifications
- `PUT /api/mark_notification_read/{id}` - Mark as read

### Holidays
- `GET /api/admin/holidays` - List holidays (admin only)
- `POST /api/admin/holidays` - Create holiday (admin only)

### Demo Tools
- `POST /api/simulate_scan` - Simulate RFID scan
- `POST /api/simulate_bus_movement` - Simulate bus movement

## 🛠️ Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
yarn test
```

### Hot Reload

Both frontend and backend support hot reload during development:
- Frontend: Changes auto-refresh in browser
- Backend: FastAPI auto-reloads on file changes

### Restart Services

```bash
# Restart all services
sudo supervisorctl restart all

# Restart individual services
sudo supervisorctl restart frontend
sudo supervisorctl restart backend
```

## 📝 Common Tasks

### Add a New Student

1. Login as admin
2. Go to Students tab
3. Click "Add Student"
4. Fill in details (roll number, class, section)
5. Select parent (auto-creates parent account if needed)
6. Assign teacher (auto-links based on class/section)
7. Assign bus and stop

### Create a New Route

1. Login as admin
2. Go to Buses & Routes tab
3. Click "Add Route"
4. Add multiple stops with GPS coordinates
5. Save route
6. Assign buses to the route

### Simulate Bus Movement (for Demo)

1. Login as admin
2. Go to Demo tab
3. Click "Simulate Bus Movement"
4. Bus location updates on parent dashboard maps

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Start MongoDB
sudo systemctl start mongod
```

### Port Already in Use

```bash
# Kill process on port 8001 (backend)
sudo lsof -ti:8001 | xargs kill -9

# Kill process on port 3000 (frontend)
sudo lsof -ti:3000 | xargs kill -9
```

### Seed Data Not Showing

```bash
# Verify environment variables
cd backend
cat .env

# Check if data was inserted
mongosh
use bus_tracker
db.students.find().pretty()
```

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/
- **Leaflet Docs**: https://leafletjs.com/
- **MongoDB Docs**: https://www.mongodb.com/docs/

## 🔐 Dependencies and Safe Deletion Rules

### Entity Dependency Map

The Bus Tracker system implements strict dependency checks to prevent orphaned records and maintain data integrity. Below is a comprehensive dependency map:

```
┌─────────────────────────────────────────────────────────────────┐
│                     ENTITY DEPENDENCIES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  USERS (Parent/Teacher/Admin)                                   │
│    ├──> STUDENTS (via parent_id or teacher_id)                 │
│    └──> NOTIFICATIONS (cascade delete allowed)                  │
│                                                                  │
│  STUDENTS                                                        │
│    ├──> ATTENDANCE (blocks deletion)                           │
│    ├──> NOTIFICATIONS (cascade delete allowed)                  │
│    ├──< USERS (parent_id - required dependency)                │
│    ├──< USERS (teacher_id - optional dependency)               │
│    ├──< BUSES (bus_id - optional dependency)                   │
│    └──< STOPS (stop_id - optional dependency)                  │
│                                                                  │
│  BUSES                                                           │
│    ├──> STUDENTS (via bus_id)                                  │
│    └──< ROUTES (route_id - required dependency)                │
│                                                                  │
│  ROUTES                                                          │
│    ├──> BUSES (via route_id)                                   │
│    └──> STOPS (via stop_ids[] - cascade if unused)             │
│                                                                  │
│  STOPS                                                           │
│    ├──> STUDENTS (via stop_id)                                 │
│    └──> ROUTES (via stop_ids[])                                │
│                                                                  │
│  ATTENDANCE                                                      │
│    └──< STUDENTS (student_id - required dependency)            │
│                                                                  │
│  NOTIFICATIONS                                                   │
│    └──< USERS (user_id - required dependency)                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Legend: 
  ──> Points to (this entity is referenced by)
  ──< Points from (this entity references)
```

### Deletion Rules and Safeguards

#### 🚫 Blocked Deletions (Status 409 - Conflict)

These deletion operations are **BLOCKED** if dependencies exist:

1. **Delete Student**
   - ❌ Blocked if: Attendance records exist
   - Error: `"Cannot delete student. {count} attendance record(s) exist. Please delete attendance records first or archive the student."`
   - ✅ Cascade: Notifications are automatically deleted

2. **Delete User (Parent)**
   - ❌ Blocked if: Students are linked to this parent
   - Error: `"Cannot delete parent. {count} student(s) are linked to this parent. Please reassign or delete students first."`
   - ✅ Cascade: Notifications are automatically deleted

3. **Delete User (Teacher)**
   - ❌ Blocked if: Students are assigned to this teacher
   - Error: `"Cannot delete teacher. {count} student(s) are assigned to this teacher. Please reassign students first."`
   - ✅ Cascade: Notifications are automatically deleted

4. **Delete Bus**
   - ❌ Blocked if: Students are assigned to this bus
   - Error: `"Cannot delete bus. {count} student(s) are assigned to this bus. Please reassign students first."`

5. **Delete Route**
   - ❌ Blocked if: Buses are using this route
   - Error: `"Cannot delete route. {count} bus(es) are using this route. Please reassign buses first."`
   - ✅ Cascade: Unused stops (not in other routes or assigned to students) are automatically deleted

6. **Delete Stop**
   - ❌ Blocked if: Students are assigned to this stop
   - Error: `"Cannot delete stop. {count} student(s) are assigned to this stop. Please reassign students first."`
   - ❌ Blocked if: Routes include this stop
   - Error: `"Cannot delete stop. {count} route(s) include this stop. Please remove stop from routes first."`

#### ✅ Safe Deletion Paths

To safely delete entities with dependencies, follow these sequences:

**To delete a Parent User:**
```
1. Reassign or delete all students linked to this parent
2. Delete parent user (notifications cascade automatically)
```

**To delete a Teacher User:**
```
1. Reassign all students to another teacher or set teacher_id to null
2. Delete teacher user (notifications cascade automatically)
```

**To delete a Student:**
```
1. Delete all attendance records for this student
2. Delete student (notifications cascade automatically)
```

**To delete a Bus:**
```
1. Reassign all students to another bus or set bus_id to null
2. Delete bus
```

**To delete a Route:**
```
1. Reassign all buses to another route or set route_id to null
2. Delete route (unused stops cascade automatically)
```

**To delete a Stop:**
```
1. Reassign all students to another stop or set stop_id to null
2. Remove stop from all routes (update route stop_ids[])
3. Delete stop
```

### Update Operations

All update operations are **safe** and maintain referential integrity:

✅ **Update Parent Contact Info** - Students automatically reflect updated parent data  
✅ **Update Student Bus Assignment** - Can reassign student to different bus  
✅ **Update Student Teacher Assignment** - Can reassign student to different teacher  
✅ **Update Bus Route Assignment** - Can reassign bus to different route  
✅ **Update Route Stops** - Can modify stop_ids[] array  

### API Response Examples

**Successful Deletion:**
```json
{
  "status": "deleted",
  "student_id": "22a473e7-4f4f-4960-ba55-6d7196168dbd",
  "cascaded_notifications": 3
}
```

**Blocked Deletion (Conflict):**
```json
{
  "status_code": 409,
  "detail": "Cannot delete student. 12 attendance record(s) exist. Please delete attendance records first or archive the student."
}
```

### Testing Dependency Safeguards

To verify dependency safeguards are working:

```bash
# Test blocked deletion
curl -X DELETE http://localhost:8001/api/students/{id} \
  -H "Cookie: session_token=YOUR_TOKEN"

# Expected: 409 Conflict with clear error message

# Test safe update
curl -X PUT http://localhost:8001/api/students/{id} \
  -H "Cookie: session_token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bus_id": "new-bus-id"}'

# Expected: 200 OK with updated student
```

### Comprehensive Test Results

All dependency safeguards have been tested and verified:

| Test Scenario | Status | Result |
|--------------|--------|--------|
| Delete Student with Attendance | ✅ PASSED | Blocked (409) with 12 attendance records |
| Delete Parent with Linked Students | ✅ PASSED | Blocked (409) with 1 student |
| Delete Teacher with Assigned Students | ✅ PASSED | Blocked (409) with 5 students |
| Delete Bus with Assigned Students | ✅ PASSED | Blocked (409) with 4 students |
| Delete Route with Buses Using It | ✅ PASSED | Blocked (409) with 1 bus |
| Delete Stop with Students Assigned | ✅ PASSED | Blocked (409) with 1 student |
| Delete Stop in Routes | ✅ PASSED | Blocked (409) with 1 route |
| Update Parent Contact | ✅ PASSED | Successfully updated |
| Update Student Bus Assignment | ✅ PASSED | Successfully reassigned |
| Update Student Teacher Assignment | ✅ PASSED | Successfully reassigned |

**Test Coverage: 18/18 tests passed (100% success rate)**

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Support

For issues, questions, or suggestions:
- Create an issue on GitHub
- Contact: support@schoolbustrack.com

---

**Built with ❤️ for safer school transportation**
