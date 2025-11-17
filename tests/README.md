# Raspberry Pi Boarding Scanner

This directory contains the Raspberry Pi boarding scanner system for handling student attendance with RFID scanning and face verification.

## 📁 Files

### Core Pi Scripts (Production)
- **`pi_boarding_scanner.py`** - Main controller script for Pi operation
- **`pi_simulated.py`** - Simulated backend module (for development/testing)
- **`pi_hardware.py`** - Hardware backend module (for Raspberry Pi)
- **`pi_device_config.json`** - Device configuration (auto-generated after registration)
- **`rfid_student_mapping.json`** - RFID tag to student ID mapping with embedding cache

### Testing & Documentation
- **`test_pi_workflow.py`** - Automated end-to-end workflow test script
- **`PI_MODULES_README.md`** - Detailed module architecture documentation

## 🎯 Overview

The Pi boarding scanner uses a **modular 3-script architecture**:

1. **Main Controller** (`pi_boarding_scanner.py`) - Orchestrates boarding logic
2. **Backend Modules** (`pi_simulated.py` / `pi_hardware.py`) - Interchangeable hardware/simulation implementations
3. **Test Script** (`test_pi_workflow.py`) - Automated testing with simulated inputs

### Key Features
- ✅ Device registration with backend
- ✅ RFID-based student identification
- ✅ Face verification using DeepFace (Facenet model)
- ✅ Embedding caching for offline operation
- ✅ Automatic retry logic (2 failures → fresh API fetch → 3 retries)
- ✅ API fallback for missing embeddings
- ✅ Automated yellow/green status determination
- ✅ Interchangeable hardware/simulation backends

## 🚀 Quick Start

### Testing (Simulation Mode)

Run the automated test script to verify the complete workflow:

```bash
cd /app/backend/tests
python3 test_pi_workflow.py
```

This will test:
- Device registration and authentication
- RFID input handling
- Student lookup via API
- Embedding retrieval and caching
- IN scan packet (Yellow status)
- OUT scan packet (Green status)
- Cache update mechanism
- Retry logic verification
- API fallback verification

### Manual Testing (Simulation Mode)

Run the main Pi scanner in simulation mode:

```bash
cd /app/backend/tests
python3 pi_boarding_scanner.py
```

You'll be prompted to:
1. Enter RFID tags manually
2. Select scan type (IN or OUT)
3. View verification results

### Production Use (Hardware Mode)

On a Raspberry Pi with RFID reader and camera:

```bash
cd /app/backend/tests
# Ensure PI_MODE=hardware in .env file
python3 pi_boarding_scanner.py
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in `/app/backend/tests/`:

```env
PI_MODE=simulated          # or "hardware"
BACKEND_URL=http://localhost:8001
```

### RFID Mapping File

`rfid_student_mapping.json` structure:

```json
[
  {
    "rfid": "RFID-1001",
    "student_id": "uuid-here",
    "embedding": null
  }
]
```

- **rfid**: RFID tag identifier
- **student_id**: Must match backend database
- **embedding**: Cached face embedding (auto-populated on first fetch)

### Device Configuration

`pi_device_config.json` (auto-generated on first run):

```json
{
  "backend_url": "http://localhost:8001",
  "device_id": "uuid-here",
  "device_name": "pi-test-device",
  "bus_number": "BUS-001",
  "api_key": "your-api-key",
  "registered_at": "2025-11-15T10:30:00Z"
}
```

## 📊 Workflow

### Boarding IN (First Scan - Yellow Status)
```
RFID Scanned
    ↓
Check Local Embedding Cache
    ↓
No Cache? → Fetch from API
    ↓
Capture/Fetch Student Photo
    ↓
Generate Face Embedding
    ↓
Compare Embeddings (threshold ≥ 60%)
    ↓
Send Scan Event (verified: true/false)
    ↓
Backend Creates YELLOW Status
```

### Boarding OUT (Second Scan - Green Status)
```
RFID Scanned
    ↓
Send Scan Event (verified: true)
    ↓
Backend Updates to GREEN Status
```

### Retry Logic (After 2 Failures)
```
2 Consecutive Verification Failures
    ↓
Fetch Fresh Embedding from API
    ↓
Update Local Cache
    ↓
Retry Verification (up to 3 attempts)
    ↓
Success? → Verified Scan
Fail? → Unverified Scan (allows boarding)
```

## 🔌 API Endpoints Used

All device endpoints require `X-API-Key` header authentication.

### Authentication & Registration
- `POST /api/auth/login` - Admin login for device registration
- `POST /api/device/register` - Register device and receive API key

### Device Operations
- `GET /api/students/{id}/photo` - Fetch student profile photo
- `GET /api/students/{id}/embedding` - Fetch stored face embedding
- `POST /api/scan_event` - Send boarding scan event

### Scan Event Payload
```json
{
  "student_id": "uuid",
  "tag_id": "RFID-1001",
  "verified": true,
  "confidence": 0.85,
  "lat": 37.7749,
  "lon": -122.4194
}
```

## 🧪 Testing

### Automated Test Script

The `test_pi_workflow.py` script performs comprehensive end-to-end testing:

```bash
python3 test_pi_workflow.py
```

**Test Coverage:**
1. Device registration validation
2. RFID input handling
3. Student lookup via API
4. Embedding retrieval and caching
5. IN scan packet transmission
6. OUT scan packet transmission
7. Cache update verification
8. Retry logic verification
9. API fallback verification

**Expected Output:**
```
✅ ALL TESTS PASSED (9/9)
✓ Device registration valid
✓ RFID input handling working
✓ Student lookup successful
✓ Embedding retrieval with fallback
✓ IN scan packet sent (Yellow)
✓ OUT scan packet sent (Green)
✓ Cache mechanism functional
✓ Retry logic present
✓ API fallback operational
```

## 🏗️ Architecture

### Modular Backend System

The Pi scanner uses interchangeable backend modules with identical function signatures:

**Common Interface:**
```python
def initialize() -> bool
def read_rfid() -> Optional[str]
def capture_student_photo(config, student_id, script_dir) -> Optional[str]
def generate_face_embedding(photo_path) -> Optional[np.ndarray]
def send_packet(config, payload) -> bool
def cleanup()
```

**Simulated Backend** (`pi_simulated.py`):
- Prompts for RFID input
- Fetches photos from backend API
- No hardware required

**Hardware Backend** (`pi_hardware.py`):
- Reads from MFRC522 RFID reader
- Captures from Pi Camera
- Requires GPIO and camera hardware

### Switching Modes

Edit `.env`:
```env
PI_MODE=simulated  # or "hardware"
```

Or set environment variable:
```bash
PI_MODE=hardware python3 pi_boarding_scanner.py
```

## 🔐 Security

- API keys stored in `pi_device_config.json` (keep secure)
- Device authentication via `X-API-Key` header
- Face embeddings cached locally for offline verification
- All backend communication over authenticated endpoints

## 📦 Dependencies

### Common (All Modes)
```bash
pip3 install requests numpy python-dotenv
pip3 install deepface tf-keras tensorflow
```

### Hardware Mode Only
```bash
pip3 install mfrc522 RPi.GPIO
pip3 install picamera2  # or picamera
```

## 🐛 Troubleshooting

### Device Registration Fails
- Verify backend URL is accessible
- Check admin credentials
- Ensure bus exists in backend
- Verify network connectivity

### RFID Tag Not Found
- Check `rfid_student_mapping.json` exists
- Verify RFID tag is in mapping
- Ensure student_id matches backend

### Face Verification Fails
- Ensure student has clear profile photo
- Check DeepFace installation
- Verify network connection
- Review lighting/angle for camera

### API Key Invalid
- Delete `pi_device_config.json` and re-register
- Verify device still exists in backend
- Check with admin that device is active

## 📚 Additional Documentation

- **Module Architecture**: See `PI_MODULES_README.md`
- **API Documentation**: See `/app/docs/API_DOCUMENTATION.md`
- **Backend Integration**: See `/app/docs/RASPBERRY_PI_INTEGRATION.md`
- **Device API Testing**: See `/app/docs/API_TEST_DEVICE.md`

## 🎓 Face Verification Details

### DeepFace Configuration
- **Model**: Facenet
- **Embedding**: 128-dimensional vector
- **Similarity**: Cosine similarity
- **Threshold**: ≥ 60% = verified

### Verification Outcomes

| Similarity | Status | Action |
|------------|--------|--------|
| ≥ 60% | ✓ Verified | Normal boarding |
| < 60% | ✗ Not Verified | Flagged for review |
| No embedding | ⚠ Warning | Unverified scan |
| No photo | ⚠ Warning | Unverified scan |

### Performance
- Face embedding generation: ~2-3 seconds
- Network requests: ~500ms
- Total scan time: ~3-5 seconds per student

## 📝 Notes

- Main script defaults to simulation mode if hardware initialization fails
- Embedding cache updates automatically on successful API fetch
- Retry logic activates after 2 consecutive verification failures
- API fallback ensures boarding continues even without embeddings
- All scan events logged with timestamp and verification status
