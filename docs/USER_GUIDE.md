# 👥 User Guide

Complete guide for using the Bus Tracker System across all three user roles.

## 🔐 Demo Login Credentials

### Admin Accounts

| Email | Password | Name | Permissions |
|-------|----------|------|-------------|
| admin@school.com | password | James Anderson | Primary Administrator (Elevated) |
| admin2@school.com | password | Patricia Williams | Secondary Administrator |

**Note:** Only elevated admins can edit other admin accounts.

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

---

## 👨‍👩‍👧 Parent Dashboard

**Access:** Login with any parent account → Auto-redirects to `/parent`

### Features Overview

#### 1. Student Information Card
- Student photo and name
- **Information displayed (in order):**
  1. Class & Section
  2. Teacher Name
  3. Phone Number
  4. Emergency Contact (highlighted)
  5. Bus Number
  6. Stop Name

#### 2. Live Bus Tracking
- Real-time GPS location of your child's bus
- Interactive map with bus icon
- Toggle route visualization:
  - Click "Show Route" to see complete bus route
  - Click "Hide Route" to show only bus location
- Route displays all stops with numbered markers
- Map auto-fits to show both bus and route

**GPS Status Indicators:**
- **Normal Location** (blue/purple bus icon)
  - GPS signal available
  - Location updating in real-time
  - Popup shows "Live Location"
- **GPS Unavailable** (gray bus icon with 🔴❓)
  - GPS signal temporarily unavailable
  - Bus marker stays at last known position
  - Popup shows "GPS Unavailable"
  - System continues working - attendance still recorded
- **Stale Location** (older timestamp)
  - Location not updated recently (>60 seconds)
  - May indicate connectivity issues
  - Check with school if persists

#### 3. Monthly Attendance Calendar
- Color-coded AM/PM attendance grid
- **Interactive Green Cells:**
  - Click any green (Reached) cell to view:
    - Captured photo from scan time
    - Exact timestamp of boarding/deboarding
  - Modal shows "Arrival Scan" (AM) or "Departure Scan" (PM)

**Status Colors:**
- 🔵 **Blue** - Holiday (school closed)
- 🟢 **Green** - Reached destination (clickable for details)
- 🟡 **Yellow** - On board (scanned but not reached)
- 🔴 **Red** - Missed bus
- ⚪ **Gray** - Not scanned yet

#### 4. Unified Notifications Panel
- Real-time alerts with purple-pink gradient design
- Click notifications to view full details in modal
- Automatically marks as read when clicked
- Shows relative timestamps ("5m ago", "2h ago")
- "New" badge for unread notifications
- Displays up to 5 most recent notifications
- **Sample notifications:**
  - Bus approaching alerts
  - Student boarding confirmations
  - Arrival notifications
  - Identity mismatch warnings

### Common Parent Tasks

**View Child's Attendance History:**
1. Scroll to Attendance section
2. Use ← → arrows to navigate months
3. Click any green cell to see scan photo and time

**Track Bus Location:**
1. View the map section
2. Click "Show Route" to see complete path
3. Bus location updates in real-time

**Check Notifications:**
1. Scroll to Notifications panel on right
2. Unread notifications appear at top with "New" badge
3. Click notification to view details and mark as read

---

## 👨‍🏫 Teacher Dashboard

**Access:** Login with teacher account → Auto-redirects to `/teacher`

### Features Overview

#### 1. Teacher Profile Card
- Your photo, name, contact information
- Assigned class and section
- Quick overview statistics

#### 2. Summary Statistics
- **Total Students** - Number of students in your class
- **Avg Monthly Attendance** - Percentage for current month
- **Today's Absences** - Students marked red (missed bus)

#### 3. Student List Table
**Columns:**
- Name
- Roll Number
- Parent Name
- Bus Number
- AM Status (color badge)
- PM Status (color badge)
- Actions (View & View Attendance buttons)

**Search & Filter Options:**
- Search by student or parent name
- Filter by bus number
- Filter by AM status
- Filter by PM status

#### 4. Student Details Modal
Opens when clicking 👁️ View button:
- Complete student profile
- Contact information
- Parent details with emergency contact
- Bus and stop assignment
- View Route button for bus route map

#### 5. Monthly Attendance Modal
Opens when clicking 📅 View Attendance button:
- Full monthly attendance grid
- Same 5-color status system
- Interactive green cells (click to see photo & timestamp)
- Month navigation
- Attendance summary

#### 6. Unified Notifications Panel
- System events for your students with purple-pink gradient design
- Click notifications to view full details in modal
- Automatically marks as read when clicked
- Shows relative timestamps
- "New" badge for unread notifications
- **Sample notifications:**
  - Class schedule updates
  - Parent meeting reminders
  - Attendance alerts
  - Administrative announcements

### Common Teacher Tasks

**View Student Attendance:**
1. Find student in table
2. Click 📅 View Attendance button
3. Navigate months with arrows
4. Click green cells to see scan details

**Check Today's Status:**
1. Review AM/PM status columns
2. Red badges indicate absences
3. Yellow/Green show attendance

**View Student Details:**
1. Click 👁️ View button in Actions column
2. Review student information
3. Click "View Route on Map" for bus route

**Check Notifications:**
1. View Notifications panel on right sidebar
2. Unread notifications appear at top with "New" badge
3. Click notification to view details and mark as read

---

## 👨‍💼 Admin Dashboard

**Access:** Login with admin account → Auto-redirects to `/admin`

### Features Overview

#### Dashboard Tabs:
1. **Overview** - System statistics and quick actions
2. **Students** - Complete student management
3. **Users** - Manage parents, teachers, admins
4. **Buses & Routes** - Transportation management

### 1. Overview Tab

**System Statistics Cards:**
- Total Students count
- Total Teachers count
- Total Buses count

**Upcoming Holidays Section:**
- List of upcoming school holidays
- "Edit Holidays" button for management
- Shows past holidays in gray
- Visual indicators (🌟 for upcoming)

**Unified Notifications Panel:**
- System-wide notifications with purple-pink gradient design
- Click notifications to view full details in modal
- Automatically marks as read when clicked
- Shows relative timestamps
- "New" badge for unread notifications
- **Sample notifications:**
  - System updates
  - Device registrations
  - Attendance summaries
  - Holiday reminders

### 2. Students Tab

**Student Table Columns:**
- Name
- Phone
- Parent
- Class
- Section
- Bus
- View | Edit buttons

**Operations:**

**Add New Student:**
1. Click "Add Student" button
2. **Step 1 - Student Information:**
   - Name, Roll Number (e.g., G5A-001)
   - Class & Section (merged input)
   - Phone, Emergency Contact
   - Bus selection
   - Stop selection (dynamic based on bus)
3. **Step 2 - Parent Information:**
   - Radio: Create New Parent or Select Existing
   - If new: Enter parent details
   - If existing: Choose from dropdown
4. **Step 3 - Teacher Assignment:**
   - Auto-assigned based on class/section
   - Manual override available

**Edit Student:**
1. Click ✏️ Edit button
2. Update any field
3. Change bus (capacity warning if exceeded)
4. Change parent (supports multiple children)
5. Save changes (triggers email to parent)

**View Student:**
1. Click 👁️ View button
2. See complete student profile
3. View monthly attendance
4. Access route visualization

**Delete Student:**
- ❌ Blocked if attendance records exist
- Must delete attendance first or archive
- Notifications cascade delete automatically

### 3. Users Tab

**Sub-tabs:** Parents | Teachers | Admins

**Operations for Each Role:**

**Add New User:**
1. Click "Add User" button
2. Select role (Parent/Teacher/Admin)
3. Enter name, email, password
4. Phone and address (optional)
5. For teachers: Assign class & section
6. For admins: Set elevated permissions

**Edit User:**
1. Click ✏️ Edit in user row
2. Update contact information
3. Change role assignments
4. Modify permissions
5. **Restriction:** Non-elevated admins cannot edit elevated admins

**View User:**
1. Click 👁️ View button
2. For parents: See linked students
3. For teachers: See assigned students
4. For admins: See permission level

**Delete User:**
- **Parents:** Blocked if students linked (reassign first)
- **Teachers:** Blocked if students assigned (reassign first)
- **Admins:** Can only be deleted by elevated admin
- Notifications cascade delete automatically

### 4. Buses & Routes Tab

**Sub-tabs:** Buses | Routes

**Bus Operations:**

**Add Bus:**
1. Click "Add Bus"
2. Enter bus number (e.g., BUS-001)
3. Driver name and phone
4. Capacity
5. Assign to route

**Edit Bus:**
1. Update bus details
2. Change route assignment
3. Modify capacity

**Delete Bus:**
- ❌ Blocked if students assigned
- Reassign students first

**Route Operations:**

**Add Route:**
1. Click "Add Route"
2. Enter route name
3. Add stops (multiple):
   - Stop name
   - GPS coordinates (lat/lon)
   - Order in sequence
4. Define map path

**View Route:**
1. Opens interactive map
2. Shows all stops with markers
3. Displays route polyline
4. Flowchart of stops in order

**Edit Route:**
1. Modify route name
2. Add/remove stops
3. Reorder stops
4. Update map path

**Delete Route:**
- ❌ Blocked if buses use it
- Reassign buses first
- Unused stops cascade delete

### 5. Holiday Management

**Access:** Click "Edit Holidays" in Overview tab

**Add Holiday:**
1. Click "Add Holiday"
2. Enter title
3. Select date
4. Add description (optional)

**Edit Holiday:**
1. Click ✏️ Edit button
2. Modify title, date, or description

**Delete Holiday:**
- No dependencies - safe to delete
- Affects attendance calendar immediately

**Holiday Display:**
- Chronological sorting (upcoming first)
- Visual indicators:
  - 🌟 **Upcoming** - Future dates
  - **Past** - Gray, reduced opacity
- Search functionality

### 6. Demo Tools Tab

**For Testing & Demonstration:**

**Simulate RFID Scan:**
1. Select student
2. Set verification status
3. Trigger scan event
4. Generates attendance record

**Simulate Bus Movement:**
1. Select bus
2. Updates GPS coordinates
3. Visible on parent maps

**Continuous Simulation:**
- Auto-generates events
- Useful for demonstrations

---

## 📊 Understanding Attendance Status

### Status Colors Explained

| Color | Status | Meaning | Actions |
|-------|--------|---------|---------|  
| 🟢 Green | Reached | Student scanned and reached destination | Click to view photo & timestamp |
| 🟡 Yellow | On Board | Student scanned but bus still traveling | Non-clickable |
| 🔴 Red | Missed | Student did not board the bus | Non-clickable |
| ⚪ Gray | Not Scanned | No scan data for this session | Non-clickable |
| 🔵 Blue | Holiday | School holiday (no bus service) | Non-clickable |

### Attendance Sessions

- **AM Session** - Morning pickup (boarding)
- **PM Session** - Afternoon dropoff (deboarding)

Each day has 2 sessions, making 60 sessions per month (30 days × 2).

---

## 🚨 Notifications System

### Unified Notification Panel

All three dashboards (Parent, Teacher, Admin) now use a consistent notification system:

**Design Features:**
- Purple-pink gradient background
- White bell icon in circular badge
- Click to view full notification details in modal
- Automatically marks as read when clicked
- Relative timestamps ("Just now", "5m ago", "2h ago", "3d ago")
- "New" badge for unread notifications
- Displays up to 5 most recent notifications
- Hover effect with shadow transition

### Notification Types

**For Parents:**
- **Bus Approaching** - Bus arrival alerts
- **Student Boarded** - Boarding confirmations
- **Reached School/Home** - Arrival confirmations
- **Identity Mismatch** - RFID verification failures
- **Route Changes** - Bus reassignments

**For Teachers:**
- **Class Schedule Updates** - Assembly or class changes
- **Parent Meeting Reminders** - Scheduled meetings
- **Attendance Alerts** - Absence reports
- **Administrative Announcements** - System messages

**For Admins:**
- **System Updates** - Feature releases
- **Device Registrations** - New Raspberry Pi devices
- **Attendance Summaries** - Daily reports
- **Holiday Reminders** - Upcoming holidays
- **Backup Status** - Database backup confirmations

### Managing Notifications

**View Notification Details:**
1. Click on notification card
2. Modal opens with full details
3. Automatically marked as read

**Notification Priority:**
- Unread appear first with "New" badge
- Most recent at top
- Consistent purple-pink design across all roles

---

## 🔄 Role-Based Data Access

### What Each Role Can See

**Parents:**
- ✅ Own children only
- ✅ Own children's attendance
- ✅ Own children's bus locations
- ✅ Own notifications (filtered by user_id)
- ❌ Other students' data
- ❌ System-wide information

**Teachers:**
- ✅ Assigned class students
- ✅ Student details for their class
- ✅ Attendance for their students
- ✅ Parent contact information
- ✅ Own notifications (filtered by user_id)
- ❌ Students from other classes
- ❌ System administration

**Admins:**
- ✅ All students (system-wide)
- ✅ All users (all roles)
- ✅ All buses and routes
- ✅ System configuration
- ✅ Full CRUD operations
- ✅ Demo and simulation tools
- ✅ All admin notifications (filtered by user_id)

---

## 💡 Tips & Best Practices

### For Parents

1. **Check attendance daily** to ensure your child is tracked properly
2. **Enable notifications** for real-time alerts
3. **Use route toggle** to understand bus path and timing
4. **Click green cells** to verify your child's actual scan photos
5. **Click notifications** to view full details and mark them as read
6. **Contact admin** if you notice discrepancies

### For Teachers

1. **Review AM status** at start of day to identify absences
2. **Use filters** to quickly find students by bus or status
3. **Check attendance patterns** for students with frequent issues
4. **Verify parent contact info** is up to date
5. **Monitor notifications panel** for class-related alerts
6. **Report systematic issues** to administration

### For Admins

1. **Regular data audits** - Check for orphaned records
2. **Student capacity monitoring** - Watch for overcrowded buses
3. **Route optimization** - Review route efficiency periodically
4. **Backup critical data** - Especially attendance records
5. **Test before holidays** - Ensure holiday dates are marked
6. **User account hygiene** - Remove inactive accounts
7. **Dependency checks** - Understand deletion restrictions
8. **Monitor system notifications** - Stay informed of system events

---

## 🆘 Getting Help

**Technical Issues:**
- See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

**Feature Questions:**
- See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

**Development:**
- See [DEVELOPMENT.md](./DEVELOPMENT.md)

**Contact Support:**
- Email: support@schoolbustrack.com
- Create issue on GitHub
- Check FAQ in troubleshooting guide

---

**Remember:** All demo accounts use password `password` - Change these in production!