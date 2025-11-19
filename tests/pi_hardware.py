#!/usr/bin/env python3
"""
Hardware Backend Module for Pi Scanner - FULLY INTEGRATED WITH cam_test.py
===========================================================================

This module provides real hardware implementations for Raspberry Pi.
Integrates RFID scanning, camera capture via DroidCam (HTTP stream) with ADB fallback,
face detection, and GPS location.

IMPORTANT: All camera operations route through cam_test.py module.
DO NOT reimplement camera logic - import and use cam_test functions directly.
"""

import sys
import os
import re
import time
import subprocess
import threading
from pathlib import Path
from typing import Optional, Dict, Tuple

import cv2
import numpy as np
from datetime import datetime

# CRITICAL: Import cam_test.py as the authoritative camera module
# All camera operations route through this proven stable implementation
import cam_test

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

# ============================================================
# CONFIGURATION - All values can be overridden by environment
# ============================================================

# Camera Configuration
DEVICE_IP = os.getenv("DEVICE_IP", "172.17.72.186")
DEVICE_ID = f"{DEVICE_IP}:5555"
DROIDCAM_PORT = os.getenv("DROIDCAM_PORT", "4747")
DROIDCAM_URL = f"http://{DEVICE_IP}:{DROIDCAM_PORT}/video"
CAMERA_TIMEOUT = int(os.getenv("CAMERA_TIMEOUT", "10"))  # seconds
CAPTURE_WINDOW = float(os.getenv("CAPTURE_WINDOW", "8.0"))  # seconds

# Photo Configuration
PHOTO_AGE_LIMIT = int(os.getenv("PHOTO_AGE_LIMIT", "20"))  # seconds
MAX_RETRIES = int(os.getenv("MAX_PHOTO_RETRIES", "5"))
RETRY_SLEEP_TIME = float(os.getenv("RETRY_SLEEP_TIME", "5.0"))  # seconds

# Face Detection Configuration
OFFSET_RATIO = float(os.getenv("FACE_OFFSET_RATIO", "0.30"))
FACE_MAX_AGE = float(os.getenv("FACE_MAX_AGE", "3.0"))  # seconds
DETECTION_THROTTLE = float(os.getenv("DETECTION_THROTTLE", "0.10"))  # seconds

# GPIO Configuration
LED_SCAN = int(os.getenv("GPIO_LED_SCAN", "22"))
BIN0 = int(os.getenv("GPIO_BIN0", "23"))
BIN1 = int(os.getenv("GPIO_BIN1", "24"))
BIN2 = int(os.getenv("GPIO_BIN2", "25"))
BINARY_PINS = [BIN0, BIN1, BIN2]

# RFID Configuration
RFID_READ_TIMEOUT = float(os.getenv("RFID_READ_TIMEOUT", "60.0"))  # seconds

# ============================================================
# GLOBAL STATE - Protected with locks where necessary
# ============================================================

# Hardware handles
rfid_reader = None
detector = None
gpio_available = False
camera_mode = None  # "droidcam" or "adb_connected" or None

# ============================================================
# INITIALIZATION FUNCTIONS
# ============================================================

def initialize() -> bool:
    """
    Initialize hardware components with graceful degradation.
    Returns True if critical components initialized successfully.
    Non-critical failures (like GPIO LEDs) will warn but not fail.
    """
    print(f"{Colors.CYAN}-> Initializing HARDWARE mode{Colors.RESET}")

    critical_failures = []

    # Initialize GPIO for LEDs (non-critical - for visual feedback only)
    if not init_gpio():
        print(f"{Colors.YELLOW}[WARN] Continuing without GPIO LED controls{Colors.RESET}")

    # Initialize RFID reader (CRITICAL)
    if not init_rfid_reader():
        critical_failures.append("RFID reader")

    # Initialize camera (CRITICAL)
    if not init_camera():
        critical_failures.append("Camera")

    # Initialize face detector (CRITICAL)
    if not init_face_detector():
        critical_failures.append("Face detector")

    # Check DeepFace (CRITICAL)
    try:
        import deepface  # noqa: F401
        print(f"{Colors.GREEN}[OK] DeepFace available{Colors.RESET}")
    except ImportError:
        print(f"{Colors.YELLOW}[WARN] DeepFace not installed, attempting installation...{Colors.RESET}")
        if not install_deepface():
            critical_failures.append("DeepFace")

    # Report initialization status
    if critical_failures:
        print(f"\n{Colors.RED}[ERROR] Critical component failures:{Colors.RESET}")
        for component in critical_failures:
            print(f"  ❌ {component}")
        print(f"{Colors.RED}Cannot proceed without these components.{Colors.RESET}")
        return False

    print(f"\n{Colors.GREEN}[OK] All critical hardware components initialized{Colors.RESET}")
    return True

def init_gpio() -> bool:
    """Initialize GPIO pins for LEDs and binary counter display"""
    global gpio_available

    try:
        import RPi.GPIO as GPIO
        GPIO.setwarnings(True)  # Enable warnings for debugging
        GPIO.setmode(GPIO.BCM)

        # Cleanup any previous state
        try:
            GPIO.cleanup()
        except:
            pass

        # Setup pins
        GPIO.setup(LED_SCAN, GPIO.OUT, initial=GPIO.LOW)
        for pin in BINARY_PINS:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

        gpio_available = True
        print(f"{Colors.GREEN}[OK] GPIO initialized{Colors.RESET}")
        return True

    except ImportError:
        print(f"{Colors.YELLOW}[WARN] RPi.GPIO not installed - LED controls disabled{Colors.RESET}")
        print(f"{Colors.YELLOW}  Install: pip install RPi.GPIO{Colors.RESET}")
        return False

    except RuntimeError as e:
        print(f"{Colors.YELLOW}[WARN] GPIO not available (not running on Pi hardware): {e}{Colors.RESET}")
        return False

    except Exception as e:
        print(f"{Colors.YELLOW}[WARN] GPIO initialization failed: {e}{Colors.RESET}")
        return False

def set_gpio_output(pin: int, state: bool) -> None:
    """Safely set GPIO output"""
    if not gpio_available:
        return

    try:
        import RPi.GPIO as GPIO
        GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
    except Exception as e:
        print(f"{Colors.YELLOW}[WARN] GPIO output error on pin {pin}: {e}{Colors.RESET}")

def default_gpio_state() -> None:
    """Turn off all LEDs"""
    set_gpio_output(LED_SCAN, False)
    for pin in BINARY_PINS:
        set_gpio_output(pin, False)

def display_binary(value: int) -> None:
    """Display a 3-bit number on the binary LEDs"""
    if not gpio_available:
        return

    for i in range(len(BINARY_PINS)):
        set_gpio_output(BINARY_PINS[i], bool((value >> i) & 1))

def install_deepface() -> bool:
    """Install DeepFace and dependencies"""
    print(f"{Colors.YELLOW}Installing DeepFace...{Colors.RESET}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "deepface", "tf-keras", "tensorflow", "--quiet"],
            timeout=300
        )
        print(f"{Colors.GREEN}[OK] DeepFace installed{Colors.RESET}")
        return True
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}[ERROR] DeepFace installation timed out{Colors.RESET}")
        return False
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Failed to install DeepFace: {e}{Colors.RESET}")
        return False

def init_rfid_reader() -> bool:
    """Initialize RFID reader hardware"""
    global rfid_reader

    try:
        from mfrc522 import SimpleMFRC522

        rfid_reader = SimpleMFRC522()
        print(f"{Colors.GREEN}[OK] RFID reader initialized{Colors.RESET}")
        return True

    except ImportError:
        print(f"{Colors.RED}[ERROR] RFID library not found{Colors.RESET}")
        print(f"{Colors.YELLOW}  Install: pip install mfrc522 RPi.GPIO{Colors.RESET}")
        return False

    except Exception as e:
        print(f"{Colors.RED}[ERROR] RFID initialization failed: {e}{Colors.RESET}")
        return False

def init_camera() -> bool:
    """
    Initialize camera via DroidCam HTTP stream (preferred) with ADB as fallback.

    CRITICAL: Routes through cam_test.py authoritative implementation.
    DO NOT modify camera initialization logic - it's managed by cam_test.
    """
    global camera_mode, detector

    # Try DroidCam first - delegate to cam_test.py
    print(f"{Colors.CYAN}-> Attempting to initialize camera via cam_test module...{Colors.RESET}")

    try:
        # CRITICAL: Use cam_test.py's initialization - proven stable
        if cam_test.initialize_camera(DROIDCAM_URL, detector):
            camera_mode = "droidcam"
            print(f"{Colors.GREEN}[OK] Camera initialized (DroidCam via cam_test){Colors.RESET}")
            return True
        else:
            print(f"{Colors.YELLOW}[WARN] cam_test initialization failed{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.YELLOW}[WARN] DroidCam connection failed: {e}{Colors.RESET}")

    # Fallback to ADB
    print(f"{Colors.CYAN}-> Trying ADB connect fallback to {DEVICE_IP}...{Colors.RESET}")

    try:
        subprocess.run(
            ["adb", "connect", f"{DEVICE_IP}:5555"],
            check=True,
            timeout=10,
            capture_output=True
        )

        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )

        if f"{DEVICE_IP}:5555" in result.stdout:
            camera_mode = "adb_connected"
            print(f"{Colors.GREEN}[OK] Camera initialized (ADB){Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}[ERROR] ADB device not found or offline{Colors.RESET}")
            return False

    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}[ERROR] ADB connection timed out{Colors.RESET}")
        return False

    except Exception as e:
        print(f"{Colors.RED}[ERROR] Camera initialization failed: {e}{Colors.RESET}")
        return False

def init_face_detector() -> bool:
    """Initialize UltraLight face detector"""
    global detector

    try:
        from ultralight import UltraLightDetector
        detector = UltraLightDetector()
        print(f"{Colors.GREEN}[OK] Face detector initialized{Colors.RESET}")
        return True

    except ImportError:
        print(f"{Colors.RED}[ERROR] ultralight not installed{Colors.RESET}")
        print(f"{Colors.YELLOW}  Install: pip install ultralight{Colors.RESET}")
        return False

    except Exception as e:
        print(f"{Colors.RED}[ERROR] Face detector initialization failed: {e}{Colors.RESET}")
        return False

# ============================================================
# ADB UTILITY FUNCTIONS
# ============================================================

def adb_command(cmd: list, timeout: float = 10.0) -> Tuple[bool, str]:
    """
    Run an ADB command and return success status and output.
    Returns: (success, output)
    """
    full_cmd = ["adb", "-s", DEVICE_ID] + cmd

    try:
        result = subprocess.run(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=True
        )
        return True, result.stdout.strip()

    except subprocess.TimeoutExpired:
        print(f"{Colors.YELLOW}[WARN] ADB command timed out: {' '.join(cmd)}{Colors.RESET}")
        return False, ""

    except subprocess.CalledProcessError as e:
        if e.stderr:
            print(f"{Colors.YELLOW}[WARN] ADB error: {e.stderr.strip()}{Colors.RESET}")
        return False, e.stdout.strip() if e.stdout else ""

    except Exception as e:
        print(f"{Colors.YELLOW}[WARN] ADB command failed: {e}{Colors.RESET}")
        return False, ""

def take_photo_adb() -> bool:
    """Trigger Android camera shutter via ADB"""
    print(f"{Colors.BLUE}-> Triggering camera via ADB...{Colors.RESET}")
    success, _ = adb_command(["shell", "input", "keyevent", "27"], timeout=5.0)

    if success:
        time.sleep(2)  # Wait for photo to be saved
        return True

    return False

def get_recent_photo_adb() -> Optional[str]:
    """Get newest photo file name from Android device"""
    success, output = adb_command(["shell", "ls", "-t", "/storage/emulated/0/DCIM/Camera/"])

    if success and output:
        return output.splitlines()[0].strip()

    return None

def get_file_age_adb(file_path: str) -> int:
    """Calculate file age in seconds"""
    curr_time = int(time.time())
    success, output = adb_command(["shell", "stat", "-c", "%Y", file_path])

    if success and output:
        try:
            file_mod_time = int(output)
            return curr_time - file_mod_time
        except ValueError:
            pass

    return 999999  # Very old if can't determine

def pull_recent_photo_adb(dest_folder: Path) -> Tuple[bool, Optional[str]]:
    """Take photo via ADB and pull it from device if recent enough"""
    dest_folder.mkdir(exist_ok=True)

    for retry_count in range(MAX_RETRIES):
        if not take_photo_adb():
            time.sleep(RETRY_SLEEP_TIME)
            continue

        recent_file = get_recent_photo_adb()
        if not recent_file:
            print(f"{Colors.YELLOW}[WARN] No photo found on device (attempt {retry_count + 1}/{MAX_RETRIES}){Colors.RESET}")
            time.sleep(RETRY_SLEEP_TIME)
            continue

        file_path = f"/storage/emulated/0/DCIM/Camera/{recent_file}"
        age = get_file_age_adb(file_path)

        print(f"{Colors.CYAN}File: {recent_file}, Age: {age} seconds{Colors.RESET}")

        if age < PHOTO_AGE_LIMIT:
            print(f"{Colors.BLUE}-> Recent photo detected, pulling...{Colors.RESET}")

            success, _ = adb_command(["pull", file_path, str(dest_folder)])
            if success:
                # Clean up device
                adb_command(["shell", "rm", file_path])
                return True, recent_file

        print(f"{Colors.YELLOW}[WARN] Photo too old, retrying...{Colors.RESET}")
        time.sleep(RETRY_SLEEP_TIME)

    print(f"{Colors.RED}[ERROR] No recent photo found after {MAX_RETRIES} retries{Colors.RESET}")
    return False, None

def get_gps_location_adb() -> Tuple[Optional[float], Optional[float]]:
    """Get GPS location from Android device via ADB"""
    success, output = adb_command(["shell", "dumpsys", "location"], timeout=5.0)

    if not success or not output:
        return None, None

    # Parse location from dumpsys output
    locations = re.findall(r'last location=Location\[([^\]]+)\]', output)
    valid_locations = [loc for loc in locations if 'null' not in loc.lower()]

    if not valid_locations:
        return None, None

    latest_loc = valid_locations[-1]
    match = re.search(r'([-\d.]+),([-\d.]+)', latest_loc)

    if match:
        try:
            latitude = float(match.group(1))
            longitude = float(match.group(2))
            print(f"{Colors.GREEN}[OK] GPS: ({latitude:.6f}, {longitude:.6f}){Colors.RESET}")
            return latitude, longitude
        except ValueError:
            pass

    return None, None

# ============================================================
# CAMERA AND FACE DETECTION - ROUTES THROUGH cam_test.py
# ============================================================

def crop_with_offset(frame: np.ndarray, box: list, offset_ratio: float = OFFSET_RATIO) -> np.ndarray:
    """
    Crop face with offset for better framing.

    CRITICAL: Routes to cam_test.py authoritative implementation.
    DO NOT reimplement - use cam_test's proven logic.
    """
    return cam_test.crop_with_offset(frame, box, offset_ratio)

def start_camera_thread() -> bool:
    """
    Start background thread for continuous frame capture.

    CRITICAL: Routes to cam_test.py authoritative implementation.
    All camera threading is managed by cam_test - DO NOT reimplement.
    """
    if camera_mode != "droidcam":
        print(f"{Colors.YELLOW}[WARN] Cannot start camera thread: not DroidCam mode{Colors.RESET}")
        return False

    # Delegate to cam_test.py's proven thread management
    return cam_test.start_camera_thread()

def stop_camera_thread() -> None:
    """
    Stop background camera thread safely.

    CRITICAL: Routes to cam_test.py authoritative cleanup.
    """
    cam_test.stop_camera_thread()

def get_latest_frame_from_thread() -> Optional[np.ndarray]:
    """
    Get the latest full frame from the camera thread.

    CRITICAL: Routes to cam_test.py authoritative frame retrieval.
    Thread-safe access managed by cam_test module.

    Returns:
        Full frame copy or None if unavailable
    """
    return cam_test.get_latest_frame()

def get_latest_face(student_id: str, script_dir: Path) -> Optional[str]:
    """
    Capture face from camera thread's latest frame.

    Uses cam_test.py for frame retrieval and face detection.

    Returns None if no frame or no face detected.
    """
    # Get latest frame from cam_test thread
    frame = get_latest_frame_from_thread()

    if frame is None:
        return None

    if detector is None:
        print(f"{Colors.YELLOW}[WARN] Detector not available{Colors.RESET}")
        return None

    try:
        # Use cam_test's face detection
        boxes, scores = cam_test.detect_faces_in_frame(frame)

        if boxes is None or len(boxes) == 0:
            return None

        # Find best face (highest confidence)
        boxes_list = boxes.tolist() if isinstance(boxes, np.ndarray) else list(boxes)
        scores_list = scores.tolist() if isinstance(scores, np.ndarray) else list(scores)
        best_idx = scores_list.index(max(scores_list))
        best_box = boxes_list[best_idx]

        # Use cam_test's crop function
        cropped_face = crop_with_offset(frame, best_box)

        if cropped_face.size == 0:
            return None

        # Save to temp directory
        temp_dir = script_dir / "temp_photos"
        temp_dir.mkdir(exist_ok=True)
        out_path = temp_dir / f"{student_id}_captured.jpg"

        cv2.imwrite(str(out_path), cropped_face)
        print(f"{Colors.GREEN}[OK] Captured face from camera thread{Colors.RESET}")
        return str(out_path)

    except Exception as e:
        print(f"{Colors.YELLOW}[WARN] Failed to capture from thread: {e}{Colors.RESET}")
        return None

def capture_student_photo(config: Dict, student_id: str, script_dir: Path) -> Optional[str]:
    """
    Capture photo using best available method.

    Priority order:
    1. Camera thread (if running) - instant capture from live feed via cam_test
    2. ADB fallback (for non-DroidCam scenarios)

    All camera operations route through cam_test.py for stability.
    """
    print(f"{Colors.BLUE}-> [HW] Capturing photo for {student_id}...{Colors.RESET}")

    temp_dir = script_dir / "temp_photos"
    temp_dir.mkdir(exist_ok=True)

    # Check if detector is available
    if detector is None:
        print(f"{Colors.RED}[ERROR] Face detector not available{Colors.RESET}")
        success, photo_filename = pull_recent_photo_adb(temp_dir)
        return str(temp_dir / photo_filename) if success else None

    # Priority 1: Try to use cam_test thread's latest frame (fastest and most reliable)
    if camera_mode == "droidcam" and cam_test.is_camera_running():
        print(f"{Colors.CYAN}-> Using cam_test camera thread frame...{Colors.RESET}")

        # Try multiple times to get a frame with detected face
        for attempt in range(5):
            frame = get_latest_frame_from_thread()

            if frame is None:
                time.sleep(0.1)
                continue

            try:
                # Use cam_test's face detection
                boxes, scores = cam_test.detect_faces_in_frame(frame)

                if boxes is not None and len(boxes) > 0:
                    # Find best face
                    boxes_list = boxes.tolist() if isinstance(boxes, np.ndarray) else list(boxes)
                    scores_list = scores.tolist() if isinstance(scores, np.ndarray) else list(scores)
                    best_idx = scores_list.index(max(scores_list))
                    best_box = boxes_list[best_idx]

                    # Use cam_test's crop function
                    cropped_face = crop_with_offset(frame, best_box)
                    if cropped_face.size > 0:
                        final_path = temp_dir / f"{student_id}_captured.jpg"
                        cv2.imwrite(str(final_path), cropped_face)
                        print(f"{Colors.GREEN}[OK] Captured from cam_test thread (attempt {attempt + 1}){Colors.RESET}")
                        return str(final_path)
            except Exception as e:
                print(f"{Colors.YELLOW}[WARN] Detection error: {e}{Colors.RESET}")

            time.sleep(0.2)  # Wait for next frame

        print(f"{Colors.YELLOW}[WARN] No face detected in cam_test thread frames{Colors.RESET}")

    # Priority 2: ADB fallback
    print(f"{Colors.CYAN}-> Using ADB capture fallback{Colors.RESET}")
    success, photo_filename = pull_recent_photo_adb(temp_dir)

    if not success:
        return None

    photo_path = temp_dir / photo_filename

    # Try to detect and crop face from ADB photo using cam_test
    try:
        frame = cv2.imread(str(photo_path))
        if frame is not None:
            # Use cam_test's face detection
            boxes, scores = cam_test.detect_faces_in_frame(frame)

            if boxes is not None and len(boxes) > 0:
                boxes_list = boxes.tolist() if isinstance(boxes, np.ndarray) else list(boxes)
                scores_list = scores.tolist() if isinstance(scores, np.ndarray) else list(scores)

                best_idx = scores_list.index(max(scores_list))
                best_box = boxes_list[best_idx]

                # Use cam_test's crop function
                cropped_face = crop_with_offset(frame, best_box)
                final_path = temp_dir / f"{student_id}_captured.jpg"
                cv2.imwrite(str(final_path), cropped_face)

                print(f"{Colors.GREEN}[OK] Face detected from ADB photo (via cam_test){Colors.RESET}")
                return str(final_path)
    except Exception as e:
        print(f"{Colors.YELLOW}[WARN] Face detection on ADB photo failed: {e}{Colors.RESET}")

    return str(photo_path)

def generate_face_embedding(photo_path: str) -> Optional[np.ndarray]:
    """Generate face embedding using DeepFace"""
    try:
        from deepface import DeepFace

        print(f"{Colors.BLUE}-> [HW] Generating face embedding...{Colors.RESET}")

        embedding_objs = DeepFace.represent(
            img_path=str(photo_path),
            model_name='Facenet',
            enforce_detection=False
        )

        if embedding_objs and len(embedding_objs) > 0:
            embedding = embedding_objs[0]['embedding']
            print(f"{Colors.GREEN}[OK] Embedding generated (dim: {len(embedding)}){Colors.RESET}")
            return np.array(embedding, dtype=np.float32)
        else:
            print(f"{Colors.RED}[ERROR] No face detected in photo{Colors.RESET}")
            return None

    except Exception as e:
        print(f"{Colors.RED}[ERROR] Embedding generation failed: {e}{Colors.RESET}")
        return None

# ============================================================
# RFID FUNCTIONS
# ============================================================

def read_rfid() -> Optional[str]:
    """Read RFID tag from hardware reader with timeout"""
    if rfid_reader is None:
        print(f"{Colors.RED}[ERROR] RFID reader not initialized{Colors.RESET}")
        return None

    try:
        print(f"\n{Colors.CYAN}-> [HW] Waiting for RFID scan...{Colors.RESET}")

        # Turn on scan LED
        set_gpio_output(LED_SCAN, True)

        # Read from RFID reader (blocking)
        rfid_result = [None]
        read_error = [None]

        def read_thread():
            try:
                id_val, _ = rfid_reader.read()
                rfid_result[0] = id_val
            except Exception as e:
                read_error[0] = e

        thread = threading.Thread(target=read_thread, daemon=True)
        thread.start()
        thread.join()  # Wait for RFID read

        # Turn off scan LED
        set_gpio_output(LED_SCAN, False)

        if read_error[0]:
            raise read_error[0]

        if rfid_result[0]:
            rfid_tag = f"RFID-{rfid_result[0]}"
            print(f"{Colors.GREEN}[OK] RFID scanned: {rfid_tag}{Colors.RESET}")
            return rfid_tag
        else:
            print(f"{Colors.YELLOW}[WARN] No RFID detected{Colors.RESET}")
            return None

    except KeyboardInterrupt:
        set_gpio_output(LED_SCAN, False)
        print(f"\n{Colors.YELLOW}Scan interrupted{Colors.RESET}")
        return None

    except Exception as e:
        set_gpio_output(LED_SCAN, False)
        print(f"{Colors.RED}[ERROR] RFID read error: {e}{Colors.RESET}")
        return None

# ============================================================
# NETWORK FUNCTIONS
# ============================================================

def send_packet(config: Dict, payload: Dict) -> bool:
    """Send data packet to backend (scan event)"""
    try:
        import requests

        print(f"{Colors.BLUE}-> [HW] Sending packet to backend...{Colors.RESET}")

        # Add GPS location if available
        lat, lon = get_gps_location_adb()
        if lat is not None and lon is not None:
            payload['lat'] = lat
            payload['lon'] = lon

        url = f"{config['backend_url']}/api/scan_event"
        headers = {"X-API-Key": config['api_key']}

        response = requests.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code == 200:
            print(f"{Colors.GREEN}[OK] Packet sent successfully{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}[ERROR] Backend returned {response.status_code}: {response.text}{Colors.RESET}")
            return False

    except requests.exceptions.Timeout:
        print(f"{Colors.RED}[ERROR] Request timed out{Colors.RESET}")
        return False

    except Exception as e:
        print(f"{Colors.RED}[ERROR] Send packet failed: {e}{Colors.RESET}")
        return False

def get_gps() -> Dict[str, Optional[float]]:
    """
    Get GPS location from Android device via ADB.
    Returns dict with 'lat' and 'lon' keys, or None values if GPS unavailable.
    """
    try:
        lat, lon = get_gps_location_adb()
        return {"lat": lat, "lon": lon}
    except Exception as e:
        print(f"{Colors.YELLOW}[WARN] GPS error: {e}{Colors.RESET}")
        return {"lat": None, "lon": None}

# ============================================================
# CLEANUP
# ============================================================

def cleanup() -> None:
    """
    Cleanup hardware resources safely.

    CRITICAL: Routes camera cleanup to cam_test.py authoritative implementation.
    """
    print(f"{Colors.CYAN}-> [HW] Cleaning up hardware resources...{Colors.RESET}")

    # Stop camera thread via cam_test (authoritative cleanup)
    stop_camera_thread()

    # Perform cam_test cleanup (handles all camera resources)
    cam_test.cleanup()

    # Cleanup GPIO
    if gpio_available:
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            print(f"{Colors.GREEN}[OK] GPIO cleaned up{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.YELLOW}[WARN] GPIO cleanup warning: {e}{Colors.RESET}")

    print(f"{Colors.CYAN}-> [HW] Hardware cleanup complete{Colors.RESET}")
