# 🔐 Demo Login Credentials

This file contains all demo login credentials for the Bus Tracker System.

**Default Password for All Accounts:** `password`

---

## 🔧 Admin Accounts

Admin accounts have full system access including user management, student management, bus/route management, and system configuration.

| Email | Password | Name | Description |
|-------|----------|------|-------------|
| `admin@school.com` | `password` | James Anderson | Primary Administrator |
| `admin2@school.com` | `password` | Patricia Williams | Secondary Administrator |

### Admin Dashboard Access
- URL: `/admin`
- Features: Full CRUD operations, system stats, demo tools

---

## 👨‍🏫 Teacher Accounts

Teacher accounts can view and manage students in their assigned class and section.

| Email | Password | Name | Class | Section | Students Count |
|-------|----------|------|-------|---------|----------------|
| `teacher1@school.com` | `password` | Mary Johnson | Grade 5 | A | 5 |
| `teacher2@school.com` | `password` | Robert Smith | Grade 6 | B | 5 |
| `teacher3@school.com` | `password` | Sarah Wilson | Grade 4 | A | 5 |

### Assigned Students

**Teacher 1 (Mary Johnson - Grade 5-A):**
- Emma Johnson (G5A-001)
- Liam Smith (G5A-002)
- Sophia Brown (G5A-003)
- Noah Davis (G5A-004)
- Olivia Martinez (G5A-005)

**Teacher 2 (Robert Smith - Grade 6-B):**
- Ethan Wilson (G6B-001)
- Ava Taylor (G6B-002)
- Mason Garcia (G6B-003)
- Isabella Rodriguez (G6B-004)
- Lucas Lee (G6B-005)

**Teacher 3 (Sarah Wilson - Grade 4-A):**
- Mia Harris (G4A-001)
- Benjamin Clark (G4A-002)
- Charlotte Lewis (G4A-003)
- James Walker (G4A-004)
- Amelia Hall (G4A-005)

### Teacher Dashboard Access
- URL: `/teacher`
- Features: View assigned students, attendance tracking, route visualization

---

## 👪 Parent Accounts

Parent accounts can view their child's information, bus location, attendance, and receive notifications.

| Email | Password | Name | Child Name | Class | Roll Number |
|-------|----------|------|------------|-------|-------------|
| `parent1@school.com` | `password` | John Parent | Emma Johnson | Grade 5-A | G5A-001 |
| `parent2@school.com` | `password` | Sarah Smith | Liam Smith | Grade 5-A | G5A-002 |
| `parent3@school.com` | `password` | Michael Brown | Sophia Brown | Grade 5-A | G5A-003 |
| `parent4@school.com` | `password` | Emily Davis | Noah Davis | Grade 5-A | G5A-004 |
| `parent5@school.com` | `password` | David Martinez | Olivia Martinez | Grade 5-A | G5A-005 |
| `parent6@school.com` | `password` | Jennifer Wilson | Ethan Wilson | Grade 6-B | G6B-001 |
| `parent7@school.com` | `password` | Christopher Taylor | Ava Taylor | Grade 6-B | G6B-002 |
| `parent8@school.com` | `password` | Amanda Garcia | Mason Garcia | Grade 6-B | G6B-003 |
| `parent9@school.com` | `password` | Matthew Rodriguez | Isabella Rodriguez | Grade 6-B | G6B-004 |
| `parent10@school.com` | `password` | Jessica Lee | Lucas Lee | Grade 6-B | G6B-005 |
| `parent11@school.com` | `password` | Daniel Harris | Mia Harris | Grade 4-A | G4A-001 |
| `parent12@school.com` | `password` | Lisa Clark | Benjamin Clark | Grade 4-A | G4A-002 |
| `parent13@school.com` | `password` | Kevin Lewis | Charlotte Lewis | Grade 4-A | G4A-003 |
| `parent14@school.com` | `password` | Nancy Walker | James Walker | Grade 4-A | G4A-004 |
| `parent15@school.com` | `password` | Steven Hall | Amelia Hall | Grade 4-A | G4A-005 |

### Parent Dashboard Access
- URL: `/parent`
- Features: Live bus tracking, route toggle, monthly attendance, student details

---

## 🚌 Bus & Route Information

### Buses

| Bus Number | Driver Name | Driver Phone | Route | Capacity |
|------------|-------------|--------------|-------|----------|
| BUS-001 | Robert Johnson | +1-555-0101 | Route A - North District | 40 |
| BUS-002 | Sarah Martinez | +1-555-0102 | Route B - South District | 35 |
| BUS-003 | Michael Chen | +1-555-0103 | Route C - East District | 45 |
| BUS-004 | Lisa Anderson | +1-555-0104 | Route D - West District | 38 |

### Routes

**Route A - North District (5 stops)**
1. Main Gate North
2. Park Avenue
3. Market Street
4. Oak Boulevard
5. School North Entrance

**Route B - South District (4 stops)**
1. South Gate
2. Elm Street
3. Maple Avenue
4. Pine Road

**Route C - East District (5 stops)**
1. East Gate
2. Cedar Lane
3. Birch Street
4. Walnut Drive
5. School East Entrance

**Route D - West District (6 stops)**
1. West Gate
2. Sunset Boulevard
3. Ocean Avenue
4. Beach Street
5. Harbor Road
6. School West Entrance

---

## 📊 Student Distribution

### By Class and Section

- **Grade 5 - Section A**: 5 students (Teacher: Mary Johnson)
- **Grade 6 - Section B**: 5 students (Teacher: Robert Smith)
- **Grade 4 - Section A**: 5 students (Teacher: Sarah Wilson)

### By Bus

- **BUS-001**: 4 students (Route A - North)
- **BUS-002**: 4 students (Route B - South)
- **BUS-003**: 3 students (Route C - East)
- **BUS-004**: 4 students (Route D - West)

---

## 🧪 Testing Scenarios

### Scenario 1: Parent View
1. Login as `parent1@school.com` / `password`
2. View Emma Johnson's dashboard
3. Check live bus location (BUS-001)
4. Toggle route visualization
5. View monthly attendance

### Scenario 2: Teacher View
1. Login as `teacher1@school.com` / `password`
2. View all Grade 5-A students (5 students)
3. Check today's attendance
4. View individual student details
5. See route for student's bus

### Scenario 3: Admin Operations
1. Login as `admin@school.com` / `password`
2. View system overview
3. Manage students (add/edit/delete)
4. Manage users and buses
5. Run demo simulations

---

## 🔄 How to Reset Data

If you need to reset the database and reseed:

```bash
# Option 1: Run seed script directly
cd backend
python seed_data.py

# Option 2: Use npm/yarn script
npm run seed
# or
yarn seed

# Option 3: Use shell script
./scripts/seed.sh
```

---

## 📝 Notes

- All passwords are set to `password` for demo purposes
- In production, use strong passwords and proper authentication
- Student roll numbers follow format: `{Grade}{Section}-{Number}` (e.g., G5A-001)
- Each parent account is linked to exactly one student
- Each teacher account is assigned to one class/section
- Each student is linked to one parent, one teacher, and one bus

---

**Last Updated:** January 2025
**Seed Script Version:** 1.0
