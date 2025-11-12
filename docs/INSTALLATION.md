# 📦 Installation Guide

Complete guide for setting up the Bus Tracker System on your local or production environment.

## Prerequisites

- **Python 3.9+** - Backend runtime
- **Node.js 16+** - Frontend runtime  
- **MongoDB** - Database (local or cloud instance)
- **yarn** - Package manager for frontend

## Step 1: Clone the Repository

```bash
git clone https://github.com/SiddharthJain131/bus-tracker.git
cd bus-tracker
```

## Step 2: Backend Setup

### Install Python Dependencies

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Backend Environment

Create a `.env` file in the `backend` directory:

```bash
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=bus_tracker
BACKEND_BASE_URL=${BACKEND_BASE_URL}
CORS_ORIGINS=*
EOF
```

**Environment Variables:**
- `MONGO_URL` - MongoDB connection string (internal, typically localhost)
- `DB_NAME` - Database name to use
- `BACKEND_BASE_URL` - External base URL for backend API (e.g., https://your-domain.com)
- `CORS_ORIGINS` - Allowed CORS origins, comma-separated (use * for all origins)

## Step 3: Frontend Setup

### Install Node Dependencies

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies using yarn
yarn install
```

### Configure Frontend Environment

Create a `.env` file in the `frontend` directory:

```bash
cat > .env << EOF
REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}
EOF
```

**Environment Variables:**
- `REACT_APP_BACKEND_URL` - Backend API endpoint URL (e.g., https://your-domain.com for production or http://localhost:8001 for local development)

## Step 4: Seed the Database

The application includes demo data for testing and demonstration:

```bash
# From the backend directory
cd ../backend
python seed_data.py
```

### What Gets Seeded:

| Entity | Count | Details |
|--------|-------|---------|
| Admin Accounts | 2 | Primary and secondary administrators |
| Teacher Accounts | 3 | Assigned to different classes/sections |
| Parent Accounts | 15 | One per student |
| Students | 15 | Across 3 classes with roll numbers |
| Buses | 4 | With driver information |
| Routes | 4 | With multiple stops each |
| Stops | 20 | GPS-tagged locations |
| Attendance Records | Sample | For demonstration |
| Holiday Dates | Multiple | School holidays |

### Auto-Seeding on Startup

The backend automatically runs the seed script on server startup when the database is empty. You'll see console logs:
- `🪴 Auto-seeding database...` - When seeding starts
- `✅ Auto-seeding completed successfully!` - When complete
- `✅ Database already populated, skipping seeding` - When data exists

### Smart Backup & Auto-Restore System

The Bus Tracker includes an intelligent backup rotation and auto-restore system that preserves your data across seeding cycles.

**How It Works:**

1. **Automatic Backup Rotation**
   - Backups are stored in `/backend/backups/` with timestamp format: `seed_backup_YYYYMMDD_HHMM.json`
   - Only the **3 most recent backups** are kept automatically
   - Older backups are deleted when the limit is exceeded

2. **Auto-Restore from Latest Backup**
   - When seeding runs, the system checks for the latest backup file
   - If found, data is restored from the backup instead of using default seed data
   - **Dynamic data is excluded**: attendance, logs, and notifications are NOT restored
   - If no backup exists, default seed data is used

3. **Scheduled Backup & Seed Cycles**
   - The system can run automatic backup + restore cycles at configurable intervals
   - Default: Every 24 hours
   - Prevents data loss during regular maintenance or reseeding

**Environment Variables:**

Add these to `backend/.env`:

```bash
# Enable automatic scheduled seeding (default: false)
AUTO_SEED_ENABLE=true

# Interval between seed cycles in hours (default: 24)
SEED_INTERVAL_HOURS=24

# Maximum number of backups to keep (default: 3)
BACKUP_LIMIT=3
```

**Manual Operations:**

```bash
# Create a backup manually
cd backend
python backup_seed_data.py

# Run a manual backup + seed cycle
python run_seeder_task.py --manual

# Start the scheduled seeder service
python run_seeder_task.py
```

**Console Logs:**

When the system runs, you'll see:
- `🔁 Running backup rotation` - Backup creation started
- `📦 Restoring from latest backup: seed_backup_<timestamp>.json` - Using backup
- `✅ Seeding completed successfully` - Cycle complete

**Note:** The scheduled seeder runs as a background process when `AUTO_SEED_ENABLE=true`. Logs are saved to `/backend/logs/seeder.log` for troubleshooting.

## Step 5: Start the Application

### Option 1: Using Supervisor (Production)

```bash
# From the project root
sudo supervisorctl restart all
```

**Service Status:**
```bash
sudo supervisorctl status
# Should show:
# backend    RUNNING
# frontend   RUNNING
# mongodb    RUNNING
```

### Option 2: Manual Start (Development)

**Terminal 1 - Start Backend:**
```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
yarn start
```

**Terminal 3 - Start MongoDB (if not running):**
```bash
sudo systemctl start mongod
```

## Access Points

Once running, access the application at:

- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs (FastAPI Swagger UI)
- **MongoDB**: mongodb://localhost:27017

## Verification Steps

### 1. Check Backend Status

```bash
curl http://localhost:8001/api/auth/me
# Should return: {"detail": "Not authenticated"} (expected)
```

### 2. Check Frontend Status

Open http://localhost:3000 in browser - should show login page.

### 3. Verify Database

```bash
mongosh
use bus_tracker
db.users.countDocuments()      # Should show 20
db.students.countDocuments()   # Should show 15
db.buses.countDocuments()      # Should show 4
```

### 4. Test Login

Use demo credentials from [USER_GUIDE.md](./USER_GUIDE.md):
- Admin: `admin@school.com` / `password`
- Teacher: `teacher@school.com` / `password`
- Parent: `parent@school.com` / `password`

## Common Installation Issues

### Issue: MongoDB Connection Failed

```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Start MongoDB
sudo systemctl start mongod

# Enable auto-start on boot
sudo systemctl enable mongod
```

### Issue: Port Already in Use

```bash
# Kill process on port 8001 (backend)
sudo lsof -ti:8001 | xargs kill -9

# Kill process on port 3000 (frontend)
sudo lsof -ti:3000 | xargs kill -9
```

### Issue: Python Dependencies Fail

```bash
# Upgrade pip first
pip install --upgrade pip

# Install dependencies again
pip install -r requirements.txt
```

### Issue: Yarn Install Fails

```bash
# Clear yarn cache
yarn cache clean

# Install again
yarn install
```

### Issue: Permission Denied (Linux/Mac)

```bash
# Give execute permissions to scripts
chmod +x backend/*.py
chmod +x scripts/*.sh
```

## Production Deployment

### Environment Setup

**Backend .env (Production):**
```
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/
DB_NAME=bus_tracker_prod
```

**Frontend .env (Production):**
```
REACT_APP_BACKEND_URL=https://api.yourdomain.com
```

### Build Frontend

```bash
cd frontend
yarn build
# Creates optimized production build in frontend/build/
```

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /app/frontend/build;
        try_files $uri /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Docker Deployment (Optional)

```dockerfile
# Dockerfile example
FROM python:3.9-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

## Next Steps

- Review [USER_GUIDE.md](./USER_GUIDE.md) for login credentials
- Read [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for API details
- Check [DEVELOPMENT.md](./DEVELOPMENT.md) for development workflow

---

**Need Help?** See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues and solutions.
