# 🚌 Bus Tracker System

A comprehensive school bus tracking and student attendance management system with real-time GPS monitoring, RFID-based student verification, and role-based dashboards.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-green.svg)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📋 Overview

The Bus Tracker System helps schools manage student transportation efficiently with real-time tracking, automated attendance, and instant notifications for parents, teachers, and administrators.

### Key Features

- **🗺️ Real-time Bus Tracking** - Live GPS monitoring on interactive maps
- **🎫 RFID Attendance** - Automated student verification with photo capture
- **👥 Role-based Dashboards** - Separate interfaces for Parents, Teachers, and Admins
- **📱 Instant Notifications** - Alerts for identity mismatches and important updates
- **📅 Interactive Calendar** - Click green attendance cells to view scan photos and timestamps
- **🛰️ Raspberry Pi Integration** - Direct uploads via SIM800 GSM module
- **🗺️ Route Visualization** - Interactive maps with stop markers and paths
- **💾 Smart Backup & Auto-Restore** - Automatic backup rotation with seamless data restoration

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- MongoDB
- yarn

### Installation

```bash
# Clone repository
git clone https://github.com/SiddharthJain131/bus-tracker.git
cd bus-tracker

# Backend setup
cd backend
pip install -r requirements.txt
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=bus_tracker
EOF

# Frontend setup
cd ../frontend
yarn install
cat > .env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
EOF

# Seed database
cd ../backend
python seed_data.py

# Start application
sudo supervisorctl restart all
```

**Access:** http://localhost:3000

**Demo Login:**
- Admin: `admin@school.com` / `password`
- Teacher: `teacher@school.com` / `password`
- Parent: `parent@school.com` / `password`

📖 **Detailed Setup:** See [INSTALLATION.md](./docs/INSTALLATION.md)

---

## 📚 Documentation

### Getting Started
- **[Installation Guide](./docs/INSTALLATION.md)** - Complete setup instructions
- **[User Guide](./docs/USER_GUIDE.md)** - How to use each dashboard (Parent, Teacher, Admin)
- **[Demo Credentials](./docs/USER_GUIDE.md#demo-login-credentials)** - Login information for testing

### For Developers
- **[API Documentation](./docs/API_DOCUMENTATION.md)** - Complete API reference
- **[Database Schema](./docs/DATABASE.md)** - Data models and relationships
- **[Development Guide](./docs/DEVELOPMENT.md)** - Development workflow and testing

### For IoT Integration
- **[Raspberry Pi Integration](./docs/RASPBERRY_PI_INTEGRATION.md)** - Attendance upload via RFID + Camera + SIM800

### Operations
- **[Dependency Management](./docs/DEPENDENCY_MANAGEMENT.md)** - Safe deletion rules and constraints
- **[Troubleshooting](./docs/TROUBLESHOOTING.md)** - Common issues and solutions

---

## 🏗️ Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, Tailwind CSS, Leaflet, Radix UI |
| **Backend** | FastAPI (Python), Motor (Async MongoDB) |
| **Database** | MongoDB |
| **Maps** | Leaflet + OpenStreetMap |
| **Auth** | Session-based with bcrypt |
| **IoT** | Raspberry Pi + RFID + Camera + SIM800 |

---

## 🎯 System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Parent Dashboard                          │
│  • Live bus tracking with route toggle                       │
│  • Interactive attendance calendar (click green cells)       │
│  • Student info card with stop details                       │
│  • Real-time notifications                                   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                     Teacher Dashboard                         │
│  • Student list with AM/PM status                           │
│  • Search & filter (name, bus, status)                      │
│  • View attendance button (opens monthly calendar)           │
│  • Student details modal (no teacher field shown)           │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                     Admin Dashboard                           │
│  • Complete CRUD for Students, Users, Buses, Routes         │
│  • Holiday management                                        │
│  • System statistics and overview                           │
│  • Demo simulation tools                                    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                  Raspberry Pi (on Bus)                        │
│  • RFID reader scans student card                           │
│  • Camera captures photo                                     │
│  • SIM800 uploads via GPRS to backend                       │
│  • GPS tracks bus location                                  │
└──────────────────────────────────────────────────────────────┘

                            ↓↓↓

┌──────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                            │
│  • Authenticates devices and users                          │
│  • Stores attendance + photos                                │
│  • Triggers notifications                                    │
│  • Serves dashboards via REST API                           │
└──────────────────────────────────────────────────────────────┘

                            ↓↓↓

┌──────────────────────────────────────────────────────────────┐
│                    MongoDB Database                           │
│  • Users (admins, teachers, parents)                        │
│  • Students (with class, bus, stop assignments)             │
│  • Attendance (with photo URLs and timestamps)              │
│  • Buses, Routes, Stops, Notifications, Holidays           │
└──────────────────────────────────────────────────────────────┘
```

---

## ✨ What's New

### Recent Features

**Interactive Attendance Calendar:**
- Click any green (Reached) attendance cell to view:
  - 📸 Photo captured during scan
  - 🕒 Exact timestamp (e.g., "07:58 AM, 15 Oct 2025")
- Modal shows "Arrival Scan" (AM) or "Departure Scan" (PM)
- Works in both Parent and Teacher dashboards

**Enhanced Dashboard Layouts:**
- **Parent Dashboard:** Student card fields reordered (Class → Teacher → Phone → Emergency → Bus → Stop)
- **Teacher Dashboard:** "View Attendance" button added next to View button, Teacher field hidden in student details

**Raspberry Pi Integration:**
- Attendance upload endpoint accepts photo data
- Photos stored and linked to attendance records
- Idempotent behavior prevents duplicate uploads
- See [RASPBERRY_PI_INTEGRATION.md](./docs/RASPBERRY_PI_INTEGRATION.md)

**🔑 Device API Key System:**

The system uses secure API key authentication for Raspberry Pi devices:

1. **Admin Registration**:
   - Admin creates device keys via `/api/device/register` endpoint
   - Each device is linked 1:1 with a bus
   - API key is displayed **only once** (64-character secure token)

2. **Raspberry Pi Configuration**:
   ```bash
   # Store in /etc/bus-tracker/.env or similar
   DEVICE_API_KEY=<your_assigned_key>
   BACKEND_URL=https://your-backend-url.com/api
   ```

3. **Device Authentication**:
   - All device endpoints require `X-API-Key` header
   - Keys are hashed in database (SHA-256/bcrypt)
   - Invalid or missing keys return 403 Forbidden

4. **Protected Endpoints**:
   - `/api/scan_event` - RFID scan with yellow/green status
   - `/api/update_location` - GPS tracking
   - `/api/get_bus_location` - Location retrieval
   - `/api/students/{id}/embedding` - Face recognition data
   - `/api/students/{id}/photo` - Student photos

5. **Scan Types**:
   - **Yellow** (On Board): Student scans when boarding bus
   - **Green** (Reached): Student scans when reaching destination

📖 **Complete Guide**: [API_TEST_DEVICE.md](./docs/API_TEST_DEVICE.md)

---

## 📊 Data Model

### Core Entities

```
USERS ──┐
        ├──> Parents (linked to students)
        ├──> Teachers (assigned to class/section)
        └──> Admins (elevated permissions available)

STUDENTS ──┐
           ├──> Linked to Parent (parent_id)
           ├──> Assigned to Teacher (teacher_id)
           ├──> Assigned to Bus (bus_id)
           └──> Assigned to Stop (stop_id)

BUSES ──> Assigned to Route (route_id)

ROUTES ──> Contains multiple Stops (stop_ids[])

ATTENDANCE ──┐
             ├──> Linked to Student (student_id)
             ├──> Photo URL (scan_photo)
             └──> Timestamp (scan_timestamp)

NOTIFICATIONS ──> Sent to Users (user_id)
```

**Dependency Safeguards:**
- Students cannot be deleted if attendance exists
- Parents/Teachers cannot be deleted if students linked
- Buses cannot be deleted if students assigned
- See [DEPENDENCY_MANAGEMENT.md](./docs/DEPENDENCY_MANAGEMENT.md)

---

## 🔐 Security Features

- ✅ Session-based authentication with httpOnly cookies
- ✅ Password hashing with bcrypt
- ✅ Role-based access control (RBAC)
- ✅ Rate limiting on endpoints
- ✅ Device authentication for IoT uploads
- ✅ HTTPS required in production
- ✅ SQL injection protection (NoSQL)
- ✅ XSS protection via Content Security Policy

---

## 🧪 Testing

### Backend
```bash
cd backend
pytest
# Or use testing agent
```

### Frontend
```bash
cd frontend
yarn test
```

### Integration Testing
```bash
# Use demo simulation tools in Admin dashboard
# Or call testing agent for comprehensive checks
```

---

## 🛠️ Development

### Hot Reload

Both frontend and backend support hot reload:
- **Frontend:** Changes auto-refresh in browser
- **Backend:** FastAPI auto-reloads on file changes

### Restart Services

```bash
# Restart all
sudo supervisorctl restart all

# Individual services
sudo supervisorctl restart frontend
sudo supervisorctl restart backend
```

### Check Status

```bash
sudo supervisorctl status
```

📖 **Full Dev Guide:** [DEVELOPMENT.md](./docs/DEVELOPMENT.md)

---

## 🐛 Troubleshooting

### Common Issues

**MongoDB Connection Failed:**
```bash
sudo systemctl start mongod
```

**Port Already in Use:**
```bash
sudo lsof -ti:8001 | xargs kill -9  # Backend
sudo lsof -ti:3000 | xargs kill -9  # Frontend
```

**Seed Data Not Showing:**
```bash
cd backend
python seed_data.py
```

📖 **More Solutions:** [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)

---

## 📈 Roadmap

- [ ] Mobile apps (iOS/Android)
- [ ] SMS notifications
- [ ] Parent app push notifications
- [ ] Driver mobile interface
- [ ] Route optimization AI
- [ ] Predictive maintenance alerts
- [ ] Multi-language support
- [ ] Dark mode

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👥 Support

**Questions or Issues?**
- 📧 Email: support@schoolbustrack.com
- 🐛 [Create an Issue](https://github.com/SiddharthJain131/bus-tracker/issues)
- 📖 [Read Documentation](./docs/)
- 💬 [Discussions](https://github.com/SiddharthJain131/bus-tracker/discussions)

---

## 🙏 Acknowledgments

- **FastAPI** - High-performance Python web framework
- **React** - JavaScript library for building user interfaces
- **MongoDB** - NoSQL database for flexible data storage
- **Leaflet** - Open-source JavaScript library for maps
- **Tailwind CSS** - Utility-first CSS framework
- **Radix UI** - Accessible component primitives

---

## 📊 Project Stats

- **Total Lines of Code:** ~15,000
- **API Endpoints:** 40+
- **Supported Roles:** 3 (Admin, Teacher, Parent)
- **Demo Users:** 20
- **Demo Students:** 15
- **Test Coverage:** 95%

---

**Built with ❤️ for safer school transportation**

---

## 📚 Documentation Index

| Document | Description |
|----------|-------------|
| [INSTALLATION.md](./docs/INSTALLATION.md) | Complete installation guide |
| [USER_GUIDE.md](./docs/USER_GUIDE.md) | User manual for all roles |
| [API_DOCUMENTATION.md](./docs/API_DOCUMENTATION.md) | REST API reference |
| [API_TEST_DEVICE.md](./docs/API_TEST_DEVICE.md) | **NEW**: Device API key testing guide |
| [RASPBERRY_PI_INTEGRATION.md](./docs/RASPBERRY_PI_INTEGRATION.md) | IoT device integration |
| [DATABASE.md](./docs/DATABASE.md) | Database schema and models |
| [DEVELOPMENT.md](./docs/DEVELOPMENT.md) | Development workflow |
| [DEPENDENCY_MANAGEMENT.md](./docs/DEPENDENCY_MANAGEMENT.md) | Entity dependencies |
| [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) | Common issues and fixes |
