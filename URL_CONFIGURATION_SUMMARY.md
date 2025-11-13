# URL Configuration Update Summary

## Overview
All hardcoded localhost references have been replaced with dynamic environment variables to support flexible deployment configurations.

## Environment Variables

### Backend Configuration (`/app/backend/.env`)
```bash
MONGO_URL="mongodb://localhost:27017"  # Internal MongoDB connection
DB_NAME="bus_tracker"
BACKEND_BASE_URL="https://modal-hover-sync.preview.emergentagent.com"  # External backend URL
CORS_ORIGINS="*"  # Allowed CORS origins (comma-separated)
```

### Frontend Configuration (`/app/frontend/.env`)
```bash
REACT_APP_BACKEND_URL=https://modal-hover-sync.preview.emergentagent.com  # Backend API endpoint
WDS_SOCKET_PORT=443
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
```

## Changes Made

### 1. Backend Changes
- ✅ Added `BACKEND_BASE_URL` environment variable to `/app/backend/.env`
- ✅ CORS configuration already using `CORS_ORIGINS` from environment (no code changes needed)

### 2. Frontend Changes
- ✅ Fixed merge conflict in `/app/frontend/.env` 
- ✅ Kept production URL: `https://modal-hover-sync.preview.emergentagent.com`
- ✅ Frontend code already has fallback to localhost for development (HolidaysManagementModal.jsx)

### 3. Documentation Updates
All documentation files updated to use environment variable references:

#### README.md
- Replaced `http://localhost:8001` with `${REACT_APP_BACKEND_URL}`
- Updated setup instructions to use environment variables
- Changed access instructions to reference environment configuration

#### docs/INSTALLATION.md
- Updated backend .env setup to include `BACKEND_BASE_URL` and `CORS_ORIGINS`
- Updated frontend .env setup with environment variable syntax
- Added descriptions for all environment variables
- Changed access points to use environment variable references
- Updated verification steps to use `${BACKEND_BASE_URL}`

#### docs/API_TEST_DEVICE.md (13 replacements)
- All `http://localhost:8001` replaced with `${BACKEND_BASE_URL}`
- Updated curl examples
- Updated Postman examples
- Updated configuration examples
- Updated troubleshooting examples
- Updated Python script examples

#### docs/API_DOCUMENTATION.md
- Replaced hardcoded URLs with environment variable reference
- Simplified base URL section

#### docs/TROUBLESHOOTING.md
- Updated environment variable setup examples
- Updated CORS configuration examples
- Updated API testing examples
- Updated frontend URL verification steps

### 4. Files NOT Modified (No Changes Needed)
- `/app/backend/server.py` - Already uses `os.environ.get('CORS_ORIGINS', '*')`
- `/app/frontend/src/components/HolidaysManagementModal.jsx` - Already has fallback logic
- `/app/docs/RASPBERRY_PI_INTEGRATION.md` - No localhost references

## Configuration for Different Environments

### Local Development
```bash
# Backend .env
BACKEND_BASE_URL=http://localhost:8001

# Frontend .env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Production/Staging
```bash
# Backend .env
BACKEND_BASE_URL=https://your-domain.com

# Frontend .env
REACT_APP_BACKEND_URL=https://your-domain.com
```

## CORS Configuration

The backend CORS middleware is already configured to use the `CORS_ORIGINS` environment variable:

```python
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### CORS Examples:
- **Allow all origins (development):** `CORS_ORIGINS=*`
- **Single origin:** `CORS_ORIGINS=https://frontend.com`
- **Multiple origins:** `CORS_ORIGINS=https://frontend.com,https://admin.frontend.com`

## Testing Checklist

- [ ] Backend starts successfully with new BACKEND_BASE_URL variable
- [ ] Frontend can reach backend API
- [ ] CORS allows requests from frontend
- [ ] All API endpoints accessible
- [ ] Documentation examples are clear

## Notes

1. **MONGO_URL** remains as `mongodb://localhost:27017` since it's for internal container communication
2. **BACKEND_BASE_URL** is the external-facing URL used in documentation and by external services
3. **REACT_APP_BACKEND_URL** is used by frontend to make API calls to the backend
4. All documentation now uses `${VARIABLE_NAME}` syntax to indicate environment variables
5. Frontend code has fallback to `http://localhost:8001/api` for development when REACT_APP_BACKEND_URL is not set

