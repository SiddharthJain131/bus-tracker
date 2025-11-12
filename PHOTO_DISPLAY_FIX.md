# Photo Display Fix - Deployed Environment

## Issue Summary
User photos were not displaying on the deployed website (https://card-portrait-fix.preview.emergentagent.com) while working correctly on localhost.

## Root Cause Analysis

### Infrastructure Issue
The Kubernetes ingress routing configuration routes requests based on path prefixes:
- **`/api/*`** routes → Backend (port 8001)
- **All other paths** → Frontend (port 3000)

### Original Configuration Problem
- Backend was serving photos at `/photos/*` endpoint
- This path did NOT match the `/api/*` ingress rule
- Result: Photo requests were being routed to frontend (HTML) instead of backend (image files)

### Why It Worked on Localhost
On localhost, both frontend (port 3000) and backend (port 8001) run independently:
- Frontend at `http://localhost:3000`
- Backend at `http://localhost:8001`
- Direct requests to `http://localhost:8001/photos/*` reached backend successfully
- No ingress routing layer to interfere

### Why It Failed in Production
Production uses Kubernetes ingress with path-based routing:
- Requests to `https://domain.com/photos/*` → Frontend (404 or HTML)
- Requests to `https://domain.com/api/*` → Backend
- Photos at `/photos/*` were unreachable via backend

## Solution Implemented

### 1. Changed Static File Mount Path
**File:** `/app/backend/server.py` (line ~1523)

**Before:**
```python
app.mount("/photos", StaticFiles(directory=str(PHOTO_DIR)), name="photos")
```

**After:**
```python
# Mount static files for photos under /api prefix to match Kubernetes ingress routing
app.mount("/api/photos", StaticFiles(directory=str(PHOTO_DIR)), name="photos")
```

### 2. Updated Photo URL Helper Function
**File:** `/app/backend/server.py` (lines ~241-261)

**Before:**
```python
def get_photo_url(photo_path: Optional[str]) -> Optional[str]:
    # Returns: "/photos/admins/abc123.jpg"
```

**After:**
```python
def get_photo_url(photo_path: Optional[str]) -> Optional[str]:
    """
    Convert backend photo path to accessible URL.
    Example: "backend/photos/admins/abc123.jpg" -> "/api/photos/admins/abc123.jpg"
    
    Note: Uses /api/photos prefix to match Kubernetes ingress routing rules
    that redirect /api/* requests to backend port 8001.
    """
    # Returns: "/api/photos/admins/abc123.jpg"
```

### 3. Updated Photo Upload Response
**File:** `/app/backend/server.py` (line ~364)

**Before:**
```python
return {"photo_url": f"/photos/{file_name}"}
```

**After:**
```python
return {"photo_url": f"/api/photos/{file_name}"}
```

## Verification Results

### Database Storage (Unchanged)
Photos are still stored with paths like:
```
backend/photos/admins/55b426f6-d039-4c7b-9b20-a4c09af39eec.jpg
backend/photos/teachers/abc123.jpg
backend/photos/parents/xyz789.jpg
backend/photos/students/student123/profile.jpg
```

### API Response (Now Returns Correct URLs)
The `get_photo_url()` function converts database paths to:
```
/api/photos/admins/55b426f6-d039-4c7b-9b20-a4c09af39eec.jpg
/api/photos/teachers/abc123.jpg
/api/photos/parents/xyz789.jpg
/api/photos/students/student123/profile.jpg
```

### Production Tests

✅ **New endpoint works:**
```bash
curl -I "https://card-portrait-fix.preview.emergentagent.com/api/photos/admins/55b426f6-d039-4c7b-9b20-a4c09af39eec.jpg"
# HTTP/2 200 
# content-type: image/jpeg
# content-length: 610351
```

❌ **Old endpoint fails (as expected):**
```bash
curl -I "https://card-portrait-fix.preview.emergentagent.com/photos/admins/55b426f6-d039-4c7b-9b20-a4c09af39eec.jpg"
# HTTP/2 200 
# content-type: text/html  <-- Wrong! Returns HTML instead of image
```

### Backend Logs Confirm Success
```
INFO: GET /api/photos/admins/55b426f6-d039-4c7b-9b20-a4c09af39eec.jpg HTTP/1.1" 200 OK
```

## Impact Assessment

### ✅ Fixed Components
- Admin Dashboard - Profile photos now display
- Teacher Dashboard - Profile photos now display  
- Parent Dashboard - Profile photos now display
- All user authentication endpoints return correct photo URLs
- Photo upload endpoint returns correct URLs

### ✅ Backward Compatibility
- No database migration needed (paths stored unchanged)
- Frontend code requires no changes (uses photo URLs from API)
- Works on both localhost AND production

### ✅ Alignment with System Architecture
This fix follows the documented system architecture requirement:
> "All backend API routes MUST be prefixed with '/api' to match Kubernetes ingress rules that redirect these requests to port 8001"

## Testing Checklist

- [x] Backend restarts successfully with changes
- [x] Photo files are accessible via `/api/photos/*` endpoint
- [x] Photo URLs in API responses use `/api/photos/` prefix
- [x] Photos display correctly in deployed frontend
- [x] Old `/photos/` endpoint confirms routing issue (returns HTML)
- [x] Database photo paths remain unchanged
- [x] No console errors in frontend
- [x] Works for all user roles (admin, teacher, parent)

## Files Modified

1. `/app/backend/server.py`
   - Line ~241-261: Updated `get_photo_url()` function
   - Line ~364: Updated photo upload response
   - Line ~1523: Changed static file mount path

## No Changes Needed

- Frontend components (already use photo URLs from API)
- Database records (photo_path fields unchanged)
- Photo files on disk (location unchanged)

## Lessons Learned

1. **Always check ingress routing rules** when debugging production issues
2. **Path prefixes matter** in Kubernetes environments with path-based routing
3. **Test in production-like environments** to catch routing issues early
4. **Document infrastructure constraints** in code comments for future developers

## Related Documentation

- System Prompt: "All backend API routes MUST be prefixed with '/api'"
- test_result.md (line ~662): Previous note about photo routing issues
- Kubernetes ingress rules: `/api/*` → Backend, everything else → Frontend

---

**Status:** ✅ RESOLVED  
**Date:** 2025-11-12  
**Deployed:** Yes  
**Testing:** Complete
