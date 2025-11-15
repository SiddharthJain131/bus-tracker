# Pi Scanner Modular Architecture

## Overview

The Pi boarding scanner has been refactored into a modular architecture with interchangeable backend modules for hardware and simulation modes.

## File Structure

```
/app/backend/tests/
├── pi_boarding_scanner.py    # Main controller script
├── pi_simulated.py           # Simulated backend module (default)
├── pi_hardware.py            # Hardware backend module
├── rfid_student_mapping.json # RFID cache (rfid, student_id, embedding)
├── .env                      # Configuration (PI_MODE, BACKEND_URL)
└── pi_device_config.json     # Device registration data
```

## Main Controller (`pi_boarding_scanner.py`)

The main script orchestrates the boarding process without containing hardware or simulation logic.

**Responsibilities:**
- Device registration
- RFID mapping management
- Embedding cache management
- Verification logic and retry handling
- Backend module coordination

**Does NOT contain:**
- RFID reading logic
- Photo capture logic
- Hardware initialization
- Simulation-specific code

## Backend Modules

Both modules expose **identical function signatures** for seamless swapping:

### Common Interface

```python
def initialize() -> bool
    """Initialize backend (hardware/simulation)"""

def read_rfid() -> Optional[str]
    """Read RFID tag"""

def capture_student_photo(config: Dict, student_id: str, script_dir: Path) -> Optional[str]
    """Capture/fetch student photo"""

def generate_face_embedding(photo_path: str) -> Optional[np.ndarray]
    """Generate face embedding from photo"""

def send_packet(config: Dict, payload: Dict) -> bool
    """Send data packet to backend"""

def cleanup()
    """Cleanup resources"""
```

### `pi_simulated.py` (Default)

**Purpose:** Development and testing without hardware

**Implementations:**
- `read_rfid()` - Prompts user input for RFID
- `capture_student_photo()` - Fetches photo from backend API
- `generate_face_embedding()` - Uses DeepFace on fetched photo
- `send_packet()` - Sends API request to backend
- `initialize()` - Checks DeepFace installation
- `cleanup()` - Minimal cleanup

**Use Case:** Testing on non-Pi systems, development environments

### `pi_hardware.py`

**Purpose:** Production use on Raspberry Pi with actual hardware

**Implementations:**
- `read_rfid()` - Reads from MFRC522 RFID reader
- `capture_student_photo()` - Captures from Pi Camera
- `generate_face_embedding()` - Uses DeepFace on captured photo
- `send_packet()` - Sends API request to backend
- `initialize()` - Initializes RFID reader, camera, DeepFace
- `cleanup()` - Closes camera, cleans up GPIO

**Hardware Requirements:**
- MFRC522 RFID reader module
- Raspberry Pi Camera (picamera2 or picamera)
- GPIO pins configured

**Libraries:**
- `mfrc522` - RFID reader interface
- `RPi.GPIO` - GPIO control
- `picamera2` or `picamera` - Camera interface

## Configuration

### `.env` File

```env
BACKEND_URL=http://localhost:8001
PI_MODE=simulated
```

**PI_MODE Options:**
- `simulated` (default) - Uses `pi_simulated.py`
- `hardware` - Uses `pi_hardware.py`

### Switching Modes

**Method 1: Edit `.env`**
```bash
# For simulation
PI_MODE=simulated

# For hardware
PI_MODE=hardware
```

**Method 2: Environment variable**
```bash
PI_MODE=hardware python3 pi_boarding_scanner.py
```

**Method 3: CLI argument (future enhancement)**
```bash
python3 pi_boarding_scanner.py --mode hardware
```

## Usage

### Simulated Mode (Default)

```bash
cd /app/backend/tests
python3 pi_boarding_scanner.py
```

- Prompts for RFID input
- Fetches photos from backend
- No hardware required

### Hardware Mode

```bash
cd /app/backend/tests
# Ensure .env has PI_MODE=hardware
python3 pi_boarding_scanner.py
```

- Reads RFID from hardware
- Captures photos with Pi Camera
- Requires actual Pi hardware

## Workflow

```
Start
  ↓
Load .env config
  ↓
Import module (pi_simulated OR pi_hardware)
  ↓
Initialize backend module
  ↓
Register device (if needed)
  ↓
Load RFID mapping
  ↓
Main Loop:
  ├─ Read RFID (via backend module)
  ├─ Check embedding cache
  ├─ Capture photo (via backend module)
  ├─ Generate embedding (via backend module)
  ├─ Compare embeddings (main controller)
  ├─ Retry logic if needed (main controller)
  └─ Send packet (via backend module)
  ↓
Cleanup (via backend module)
  ↓
Exit
```

## Adding New Backend Modules

To create a new backend (e.g., `pi_cloud.py`):

1. Create new module file
2. Implement all 6 required functions with identical signatures
3. Update `.env` with new mode name
4. Main script automatically loads it

**Example:**
```python
# pi_cloud.py
def initialize() -> bool:
    # Cloud-specific initialization
    pass

def read_rfid() -> Optional[str]:
    # Read from cloud RFID service
    pass

# ... implement all other functions
```

## Benefits

✅ **No main script changes** when switching modes
✅ **Clean separation** of concerns
✅ **Easy testing** with simulated mode
✅ **Extensible** - add new backends easily
✅ **Maintainable** - isolated hardware/simulation logic
✅ **Development-friendly** - test without Pi hardware

## Dependencies

**Common:**
- `requests` - API communication
- `numpy` - Embedding operations
- `python-dotenv` - Environment config
- `deepface` - Face recognition
- `tensorflow`, `tf-keras` - DeepFace dependencies

**Hardware-specific:**
- `mfrc522` - RFID reader
- `RPi.GPIO` - GPIO control
- `picamera2` or `picamera` - Camera

## Notes

- Main script always prefers simulated mode if hardware initialization fails
- Embedding verification and retry logic remain in main controller
- Both modules use the same DeepFace model (Facenet)
- Hardware module requires Pi-specific libraries
