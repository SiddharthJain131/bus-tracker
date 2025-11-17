# 🔧 Troubleshooting Guide

Common issues and solutions for the Bus Tracker System.

## Quick Diagnostics

### Check System Status

```bash
# Check all services
sudo supervisorctl status

# Should show:
# backend    RUNNING
# frontend   RUNNING
# mongodb    RUNNING
```

### Check Backend Logs

```bash
# Error logs
tail -f /var/log/supervisor/backend.err.log

# Output logs
tail -f /var/log/supervisor/backend.out.log
```

### Check Frontend Logs

```bash
tail -f /var/log/supervisor/frontend.err.log
```

---

## Installation Issues

### MongoDB Not Running

**Symptoms:**
- Backend fails to start
- Error: "Connection refused" or "MongoDB connection failed"

**Solution:**
```bash
# Check MongoDB status
sudo systemctl status mongod

# Start MongoDB
sudo systemctl start mongod

# Enable auto-start
sudo systemctl enable mongod

# Verify connection
mongosh
```

---

### Port Already in Use

**Symptoms:**
- Error: "Address already in use"
- Services won't start

**Solution:**

**Backend (Port 8001):**
```bash
# Find process
sudo lsof -ti:8001

# Kill process
sudo lsof -ti:8001 | xargs kill -9

# Restart backend
sudo supervisorctl restart backend
```

**Frontend (Port 3000):**
```bash
# Kill process
sudo lsof -ti:3000 | xargs kill -9

# Restart frontend
sudo supervisorctl restart frontend
```

---

### Python Dependencies Failed

**Symptoms:**
- `pip install -r requirements.txt` fails
- Import errors when starting backend

**Solution:**
```bash
# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# If specific package fails, install manually
pip install <package-name>
```

---

### Node/Yarn Installation Issues

**Symptoms:**
- `yarn install` fails
- Module not found errors

**Solution:**
```bash
# Clear cache
yarn cache clean

# Remove node_modules and lock
rm -rf node_modules yarn.lock

# Reinstall
yarn install

# If still failing, update Node
nvm install 18
nvm use 18
```

---

## Runtime Issues

### Backend Won't Start

**Check logs first:**
```bash
tail -100 /var/log/supervisor/backend.err.log
```

**Common causes and fixes:**

**1. Import Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```
**Fix:**
```bash
cd backend
pip install -r requirements.txt
```

**2. MongoDB Connection:**
```
ServerSelectionTimeoutError: localhost:27017
```
**Fix:**
```bash
sudo systemctl start mongod
```

**3. Environment Variables:**
```
KeyError: 'MONGO_URL'
```
**Fix:**
```bash
cd backend
cat .env  # Verify exists
# If missing, create it with your configuration
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=bus_tracker
BACKEND_BASE_URL=${BACKEND_BASE_URL}
CORS_ORIGINS=*
EOF
```

**4. Permission Issues:**
```
PermissionError: [Errno 13] Permission denied
```
**Fix:**
```bash
sudo chown -R $USER:$USER /app
chmod -R 755 /app
```

---

### Frontend Won't Start

**Check logs:**
```bash
tail -100 /var/log/supervisor/frontend.err.log
```

**Common causes:**

**1. Module Not Found:**
```
Error: Cannot find module 'react'
```
**Fix:**
```bash
cd frontend
yarn install
```

**2. Backend URL Not Set:**
```
Undefined REACT_APP_BACKEND_URL
```
**Fix:**
```bash
cd frontend
# Set to your backend URL (e.g., http://localhost:8001 for local dev or your production URL)
echo "REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}" > .env
```

**3. Build Errors:**
```
Failed to compile
```
**Fix:**
```bash
# Clear cache
rm -rf node_modules/.cache

# Rebuild
yarn start
```

---

### Database Issues

**Seed Data Not Showing:**

```bash
# Check if data exists
mongosh
use bus_tracker
db.students.countDocuments()  # Should be 15
db.users.countDocuments()     # Should be 20

# If 0, re-seed
cd /app/backend
python seed_data.py
```

**Database Corrupted:**

```bash
# Stop services
sudo supervisorctl stop all

# Repair MongoDB
sudo systemctl stop mongod
sudo -u mongodb mongod --repair
sudo systemctl start mongod

# Restore from backup
mongorestore --db bus_tracker /backup/latest/
```

---

## Authentication Issues

### Can't Login

**Symptoms:**
- "Invalid credentials" error
- Login button doesn't work

**Solutions:**

**1. Verify credentials:**
```
Email: admin@school.com
Password: password
```

**2. Check if user exists:**
```bash
mongosh
use bus_tracker
db.users.findOne({email: "admin@school.com"})
```

**3. Reset password:**
```python
import bcrypt
password_hash = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode('utf-8')
print(password_hash)
```

```bash
mongosh
use bus_tracker
db.users.updateOne(
  {email: "admin@school.com"},
  {$set: {password_hash: "<hash_from_above>"}}
)
```

**4. Clear browser cookies:**
- Open DevTools (F12)
- Application → Cookies
- Delete `session_token`
- Try login again

---

### Session Expired

**Symptoms:**
- Logged out unexpectedly
- "Not authenticated" errors

**Solutions:**

**1. Login again**
- Sessions expire after 24 hours
- This is normal behavior

**2. If persistent:**
```bash
# Check backend logs
tail -f /var/log/supervisor/backend.err.log

# Look for session-related errors
```

---

## API Issues

### 404 Not Found

**Symptoms:**
- API calls fail with 404
- "Route not found"

**Check:**

**1. Backend is running:**
```bash
curl ${BACKEND_BASE_URL}/api/auth/me
# Should return JSON (even if not authenticated)
```

**2. Correct URL in frontend:**
```bash
cd frontend
cat .env
# Should show: REACT_APP_BACKEND_URL matching your backend's external URL
```

**3. API path is correct:**
- All backend routes must start with `/api`
- Example: `/api/students` not `/students`

---

### 500 Internal Server Error

**Symptoms:**
- API calls fail with 500
- Backend crashes

**Diagnose:**
```bash
# Check error logs
tail -50 /var/log/supervisor/backend.err.log

# Common causes:
# - Database query error
# - Missing field in model
# - Type mismatch
```

**Fix:**
- Review stack trace in logs
- Fix code error
- Restart backend

---

### CORS Errors

**Symptoms:**
- "CORS policy" error in browser console
- Frontend can't reach backend

**Fix:**

**1. Check backend CORS settings:**
```bash
# In backend/.env
# Set CORS_ORIGINS to allow your frontend URL
CORS_ORIGINS=*  # For development (allows all origins)
# OR for production, specify your frontend domain:
# CORS_ORIGINS=https://your-frontend-domain.com
```

```python
# In server.py (already configured to use environment variable)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_credentials=True,
)
```

**2. Verify frontend uses correct URL:**
- Frontend's REACT_APP_BACKEND_URL must match your backend's external URL
- Check frontend/.env configuration
- Don't mix http and https

---

## UI Issues

### Page Not Loading

**Symptoms:**
- Blank page
- Infinite loading spinner

**Diagnose:**

**1. Check browser console (F12):**
- Look for JavaScript errors
- Check Network tab for failed requests

**2. Check frontend logs:**
```bash
tail -f /var/log/supervisor/frontend.err.log
```

**3. Clear browser cache:**
- Hard refresh: Ctrl + Shift + R
- Clear all cached data

---

### Map Not Displaying

**Symptoms:**
- Gray box instead of map
- "Leaflet is not defined" error

**Solutions:**

**1. Check Leaflet CSS loaded:**
- Open DevTools → Network
- Look for leaflet.css
- Should return 200 OK

**2. Reinstall dependencies:**
```bash
cd frontend
yarn install
```

**3. Check GPS coordinates:**
```bash
# Verify bus has location
mongosh
use bus_tracker
db.bus_locations.find()
```

---

### GPS Issues & Location Tracking

#### Issue: Bus Shows Question Mark (🔴❓) on Map

**Symptoms:**
- Gray bus marker with red question mark badge
- Popup shows "GPS Unavailable"
- Location not updating

**This is Expected Behavior when:**
- GPS signal is unavailable (e.g., underground, poor sky view)
- ADB device disconnected (if using Android GPS)
- GPS disabled on Android device
- Location services not running

**System continues operating normally** - this is graceful GPS fallback.

**To Resolve:**

**1. For ADB GPS (Primary Method):**
```bash
# On Raspberry Pi, check ADB connection
adb devices

# If device offline, reconnect
adb kill-server
adb start-server
adb connect <ANDROID_IP>:5555

# Verify location services
adb shell dumpsys location | grep "last location"
```

**2. Enable GPS on Android:**
- Settings → Location → Enable
- Grant location permissions
- Wait 1-2 minutes for GPS fix
- Move to area with sky view

**3. Check GPS Function:**
```bash
# On Raspberry Pi, test GPS function
python3 -c "
from pi_hardware_mod import get_gps
gps = get_gps()
print(f'GPS: {gps}')
"

# Expected outputs:
# {"lat": 37.7749, "lon": -122.4194}  # GPS working
# {"lat": None, "lon": None}          # GPS unavailable (expected)
```

**4. Verify Backend Receiving Data:**
```bash
# Check backend logs for location updates
tail -f /var/log/supervisor/backend.out.log | grep "update_location"

# Look for:
# POST /api/update_location {"lat": null, "lon": null}  # Null is OK
# POST /api/update_location {"lat": 37.77, "lon": -122.41}  # Valid
```

**5. Check Database:**
```bash
mongosh
use bus_tracker
db.bus_locations.find({bus_number: "BUS-001"})

# Output will show:
# { lat: null, lon: null }  # GPS unavailable (system working as designed)
# or
# { lat: 37.7749, lon: -122.4194 }  # GPS working
```

#### Issue: Map Crashes or JavaScript Errors

**Symptoms:**
- Console error: "Cannot read property 'lat' of null"
- Map rendering stops
- Frontend becomes unresponsive

**Cause:** Old frontend code not handling null coordinates

**Solution:**

**1. Check BusMap.jsx has null-safe validation:**
```javascript
// Should have these checks around lines 182-196
if (location && location.lat !== null && location.lon !== null && 
    typeof location.lat === 'number' && typeof location.lon === 'number') {
  bounds.extend([location.lat, location.lon]);
}
```

**2. Update frontend if needed:**
```bash
cd /app/frontend
git pull  # Get latest null-safe code
yarn install
sudo supervisorctl restart frontend
```

**3. Clear browser cache:**
- Hard reload: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Or clear cache: DevTools → Application → Clear Storage

#### Issue: GPS Coordinates Inaccurate

**Symptoms:**
- Bus showing in wrong location
- Location jumps around map
- Coordinates don't match actual position

**Solutions:**

**1. Improve GPS Accuracy on Android:**
- Settings → Location → Mode → High Accuracy
- Enable "Wi-Fi scanning" and "Bluetooth scanning"
- Ensure good sky view for satellite signals

**2. Wait for GPS Fix:**
```bash
# Monitor GPS quality
adb shell dumpsys location

# Look for:
# accuracy: 15.0  # Good (< 20m)
# accuracy: 50.0  # Fair (20-100m)
# accuracy: 500.0 # Poor (> 100m) - wait for better fix
```

**3. Add Coordinate Validation:**
```python
# In pi_hardware_mod.py, add validation
def validate_gps(lat, lon):
    if lat is None or lon is None:
        return False
    # Check reasonable bounds for your region
    if not (30.0 <= lat <= 45.0):  # Example: adjust for your area
        return False
    if not (-130.0 <= lon <= -70.0):
        return False
    return True
```

**4. Use GPS Test Apps:**
- Install "GPS Status & Toolbox" on Android
- Check satellite count (need 4+ for good fix)
- Check HDOP value (lower is better, < 2.0 is good)

#### Issue: Location Not Updating (Stale)

**Symptoms:**
- Bus marker shows old position
- Timestamp is old
- No recent updates

**Diagnosis:**
```bash
# Check when last update received
mongosh
use bus_tracker
db.bus_locations.find({bus_number: "BUS-001"}).sort({timestamp: -1}).limit(1)

# Check timestamp - should be recent (< 60 seconds)
```

**Solutions:**

**1. Check Pi Server Running:**
```bash
# On Raspberry Pi
sudo systemctl status bus-tracker-pi

# Or check process
ps aux | grep pi_server
```

**2. Check Network Connectivity:**
```bash
# On Raspberry Pi, test backend connection
curl -I http://your-backend:8001/docs

# Test with API key
curl -H "X-API-Key: YOUR_KEY" http://your-backend:8001/api/device/list
```

**3. Check Location Updater Thread:**
```bash
# Review pi_server.py logs
journalctl -u bus-tracker-pi | grep "location update"

# Should see regular updates every 30 seconds:
# [OK] Location updated: BUS-001 (37.7749, -122.4194)
```

**4. Restart Pi Service:**
```bash
sudo systemctl restart bus-tracker-pi
```

#### Issue: "is_missing: true" in API Response

**This is Not an Error** - it's the system correctly reporting GPS unavailability.

**API Response Example:**
```json
{
  "bus_number": "BUS-001",
  "lat": null,
  "lon": null,
  "timestamp": "2025-11-17T14:00:00Z",
  "is_missing": true,     ← GPS unavailable (expected)
  "is_stale": false        ← Updated recently (good)
}
```

**What it means:**
- `is_missing: true` = GPS coordinates are null (system knows GPS is unavailable)
- `is_stale: false` = System received update recently (Pi is communicating)
- **System is working correctly** - this is graceful GPS fallback

**Action:** Fix GPS (see solutions above), or accept that GPS is temporarily unavailable. Attendance recording continues normally.

#### Issue: Rapid GPS Coordinates Changes

**Symptoms:**
- Location "jumps" frequently
- Erratic bus movement on map
- Coordinates unstable

**Causes & Solutions:**

**1. GPS Multipath Interference:**
- Move away from tall buildings
- Avoid underground areas
- Ensure clear sky view

**2. Implement Smoothing:**
```python
# Add to pi_hardware_mod.py
from collections import deque

last_positions = deque(maxlen=5)

def get_smoothed_gps():
    lat, lon = get_gps_location_adb()
    if lat and lon:
        last_positions.append((lat, lon))
        # Average last 5 positions
        avg_lat = sum(p[0] for p in last_positions) / len(last_positions)
        avg_lon = sum(p[1] for p in last_positions) / len(last_positions)
        return avg_lat, avg_lon
    return None, None
```

**3. Reduce Update Frequency:**
```python
# In pi_server.py, increase LOCATION_UPDATE_INTERVAL
LOCATION_UPDATE_INTERVAL = 60  # From 30 to 60 seconds
```

---

### Images Not Loading

**Symptoms:**
- Broken image icons
- Photo URLs don't work

**Solutions:**

**1. Check photo directory exists:**
```bash
ls -la /app/photos/
```

**2. Check permissions:**
```bash
chmod -R 755 /app/photos
```

**3. Verify photo URLs:**
- Should be: `/photos/{student_id}/{date}_{trip}.jpg`
- Check database for correct paths

---

## Performance Issues

### Slow API Responses

**Diagnose:**

**1. Check MongoDB indexes:**
```bash
mongosh
use bus_tracker
db.students.getIndexes()
db.attendance.getIndexes()
```

**2. Monitor query performance:**
```javascript
db.setProfilingLevel(2)  // Log all queries
db.system.profile.find().limit(10).sort({ts: -1})
```

**Solutions:**

**1. Add missing indexes:**
```javascript
db.attendance.createIndex({student_id: 1, date: 1, trip: 1})
```

**2. Use pagination:**
```python
# Limit results
students = db.students.find().limit(50)
```

---

### High Memory Usage

**Check usage:**
```bash
free -h
ps aux --sort=-%mem | head -10
```

**Solutions:**

**1. Restart services:**
```bash
sudo supervisorctl restart all
```

**2. Increase swap:**
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Data Issues

### Duplicate Records

**Symptoms:**
- Same student appears twice
- Multiple attendance for same date/trip

**Fix:**

**1. Remove duplicates:**
```bash
mongosh
use bus_tracker

# Find duplicates
db.students.aggregate([
  {$group: {_id: "$roll_number", count: {$sum: 1}}},
  {$match: {count: {$gt: 1}}}
])

# Delete duplicates (keep first)
db.students.deleteMany({
  student_id: {$in: ["duplicate-uuid-1", "duplicate-uuid-2"]}
})
```

**2. Ensure unique indexes exist:**
```javascript
db.students.createIndex(
  {class_name: 1, section: 1, roll_number: 1},
  {unique: true}
)
```

---

### Missing Data After Update

**Symptoms:**
- Student data disappeared
- Attendance records missing

**Solutions:**

**1. Check if accidentally deleted:**
```bash
mongosh
use bus_tracker
db.students.find({student_id: "uuid"})
```

**2. Restore from backup:**
```bash
mongorestore --db bus_tracker /backup/20250115/
```

**3. Re-seed if demo data:**
```bash
cd /app/backend
python seed_data.py
```

---

## Raspberry Pi Integration Issues

### Upload Failing

**Symptoms:**
- Attendance not recorded
- "401 Unauthorized" errors

**Solutions:**

**1. Check device authentication:**
```python
# Verify token is valid
response = requests.get(
    "http://your-server/api/auth/me",
    headers={"Authorization": f"Bearer {token}"}
)
print(response.status_code)  # Should be 200
```

**2. Verify endpoint URL:**
```python
# Should include /api prefix
url = "http://your-server/api/scan_event"
```

**3. Check SIM800 connection:**
```bash
# On Raspberry Pi
ping -c 3 your-server-domain

# Check signal strength
at+csq
```

---

### Photos Not Uploading

**Symptoms:**
- Attendance created but no photo
- "413 Payload Too Large" errors

**Solutions:**

**1. Compress images:**
```python
from PIL import Image

img = Image.open("photo.jpg")
img.thumbnail((640, 480))
img.save("photo_compressed.jpg", quality=75)
```

**2. Check file size:**
```bash
du -h photo.jpg  # Should be < 5MB
```

**3. Use Base64 encoding:**
```python
import base64

with open("photo.jpg", "rb") as f:
    encoded = base64.b64encode(f.read()).decode()
    
data = {
    "photo_url": f"data:image/jpeg;base64,{encoded}"
}
```

---

## Helpful Commands

### Service Management

```bash
# Status
sudo supervisorctl status

# Start/Stop/Restart
sudo supervisorctl start <service>
sudo supervisorctl stop <service>
sudo supervisorctl restart <service>

# Restart all
sudo supervisorctl restart all

# Reload config
sudo supervisorctl reload
```

### Log Viewing

```bash
# Tail logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/frontend.err.log

# View last 100 lines
tail -100 /var/log/supervisor/backend.out.log

# Search logs
grep "error" /var/log/supervisor/backend.err.log
```

### Database Commands

```bash
# Connect
mongosh

# Switch database
use bus_tracker

# List collections
show collections

# Count documents
db.students.countDocuments()

# Find one
db.students.findOne()

# Delete all
db.students.deleteMany({})
```

---

## Getting More Help

### Enable Debug Mode

**Backend:**
```python
# In server.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```javascript
// In console
localStorage.setItem('debug', 'true')
```

### Collect Diagnostic Info

```bash
# Create diagnostic report
cat > diagnostic.txt << EOF
System Info:
$(uname -a)

Services:
$(sudo supervisorctl status)

Ports:
$(netstat -tuln | grep -E ':(3000|8001|27017)')

Disk Space:
$(df -h)

Memory:
$(free -h)

Backend Logs (last 50):
$(tail -50 /var/log/supervisor/backend.err.log)

Frontend Logs (last 50):
$(tail -50 /var/log/supervisor/frontend.err.log)
EOF
```

### Contact Support

If issue persists:

1. Create GitHub issue with:
   - Error message
   - Steps to reproduce
   - Diagnostic report
   - Screenshots

2. Email: support@schoolbustrack.com

3. Include:
   - Bus Tracker version
   - Environment (dev/prod)
   - Browser/OS info

---

**Still stuck?** Check [User Guide](./USER_GUIDE.md) or [API Documentation](./API_DOCUMENTATION.md) for more details.
