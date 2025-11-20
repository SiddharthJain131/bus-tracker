#!/usr/bin/env python3
"""
Auto-Prog Hardware Backend Module for Pi Scanner
================================================

This module provides hardware implementations based on auto-prog.py workflow.
Integrates RFID scanning, ADB-based photo capture, GPS location, and LED indicators
with DeepFace embedding-based face verification.

DESIGN PRINCIPLES:
- Based directly on auto-prog.py proven workflow
- Uses ADB for all Android device interactions (camera trigger, photo pull, GPS)
- DeepFace Facenet model for embedding extraction
- Cosine similarity for face comparison (matching pi_server.py expectations)
- GPIO binary counter display for visual feedback
- Robust error handling with retries and timeouts
"""

import sys
import os
import re
import time
import subprocess
import threading
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime

import numpy as np
import serial

# Color codes for terminal output (matching project style)
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# ============================================================
# CONFIGURATION - All values from environment with defaults
# ============================================================

# ADB Configuration (from auto-prog.py)
DEVICE_IP = os.getenv("DEVICE_IP", "172.17.72.186")
DEVICE_ID = f"{DEVICE_IP}:5555"
ready_seen = False
# Photo Configuration (from auto-prog.py)
PHOTO_AGE_LIMIT = int(os.getenv("PHOTO_AGE_LIMIT", "20"))  # seconds
MAX_RETRIES = int(os.getenv("MAX_PHOTO_RETRIES", "5"))
RETRY_SLEEP_TIME = float(os.getenv("RETRY_SLEEP_TIME", "5.0"))  # seconds
DEST_FOLDER = "./photos"

# GPIO Configuration (from auto-prog.py)
LED_SCAN = int(os.getenv("GPIO_LED_SCAN", "22"))
BIN0 = int(os.getenv("GPIO_BIN0", "23"))
BIN1 = int(os.getenv("GPIO_BIN1", "24"))
BIN2 = int(os.getenv("GPIO_BIN2", "25"))
BINARY_PINS = [BIN0, BIN1, BIN2]

# RFID Configuration
RFID_READ_TIMEOUT = float(os.getenv("RFID_READ_TIMEOUT", "1200.0"))  # seconds
RFID_SERIAL_PORT = os.getenv("RFID_SERIAL_PORT", "/dev/ttyACM0")  # Arduino serial port
RFID_BAUD_RATE = int(os.getenv("RFID_BAUD_RATE", "115200"))  # Serial baud rate

# ============================================================
# GLOBAL STATE
# ============================================================

# Hardware handles
rfid_reader = None
gpio_available = False
adb_connected = False

# Counter state (from auto-prog.py)
scan_counter = 0

# ============================================================
# INITIALIZATION FUNCTIONS
# ============================================================

def initialize() -> bool:
    """
    Initialize hardware components with graceful degradation.
    Returns True if critical components initialized successfully.
    
    Critical components:
    - RFID reader
    - ADB connection
    - DeepFace library
    
    Non-critical:
    - GPIO LEDs (visual feedback only)
    """
    print(f"{Colors.CYAN}-> Initializing AUTO-PROG HARDWARE mode{Colors.RESET}")
    
    critical_failures = []
    
    # Initialize GPIO for LEDs (non-critical - visual feedback only)
    if not init_gpio():
        print(f"{Colors.YELLOW}[WARN] Continuing without GPIO LED controls{Colors.RESET}")
    
    # Initialize RFID reader (CRITICAL)
    if not init_rfid_reader():
        critical_failures.append("RFID reader")
    
    # Initialize ADB connection (CRITICAL)
    if not init_adb_connection():
        critical_failures.append("ADB connection")
    
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

def init_gpio() -> bool:
    """Initialize GPIO pins for LEDs and binary counter display (from auto-prog.py)"""
    global gpio_available
    
    try:
        import RPi.GPIO as GPIO
        
        # Cleanup any previous state
        GPIO.cleanup()
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        # Setup LED pins
        GPIO.setup(LED_SCAN, GPIO.OUT)
        for pin in BINARY_PINS:
            GPIO.setup(pin, GPIO.OUT)
        
        # Set to default state (all off)
        default_gpio_state()
        
        gpio_available = True
        print(f"{Colors.GREEN}[OK] GPIO initialized - Binary Counter Ready{Colors.RESET}")
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
    """Turn off all LEDs (from auto-prog.py)"""
    set_gpio_output(LED_SCAN, False)
    for pin in BINARY_PINS:
        set_gpio_output(pin, False)

def display_binary(value: int) -> None:
    """Display a 3-bit number on the binary LEDs (from auto-prog.py)"""
    if not gpio_available:
        return
    
    for i in range(len(BINARY_PINS)):
        set_gpio_output(BINARY_PINS[i], bool((value >> i) & 1))

def init_rfid_reader() -> bool:
    """Initialize RFID reader hardware - reads from Arduino via serial ACM0"""
    global rfid_reader
    
    try:
        print(f"{Colors.CYAN}-> Opening serial port {RFID_SERIAL_PORT} at {RFID_BAUD_RATE} baud...{Colors.RESET}")
        
        rfid_reader = serial.Serial(
            port=RFID_SERIAL_PORT,
            baudrate=RFID_BAUD_RATE,
            timeout=1,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        
        # Flush any existing data
        rfid_reader.reset_input_buffer()
        rfid_reader.reset_output_buffer()
        
        print(f"{Colors.GREEN}[OK] RFID reader initialized on {RFID_SERIAL_PORT}{Colors.RESET}")
        return True
        
    except serial.SerialException as e:
        print(f"{Colors.RED}[ERROR] Serial port error: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}  Check: Is Arduino connected to {RFID_SERIAL_PORT}?{Colors.RESET}")
        print(f"{Colors.YELLOW}  Check: Do you have permission? (sudo usermod -a -G dialout $USER){Colors.RESET}")
        return False
        
    except Exception as e:
        print(f"{Colors.RED}[ERROR] RFID initialization failed: {e}{Colors.RESET}")
        return False

def init_adb_connection() -> bool:
    """Initialize ADB connection to Android device (from auto-prog.py)"""
    global adb_connected
    
    print(f"{Colors.CYAN}-> Connecting to ADB device {DEVICE_IP}...{Colors.RESET}")
    
    try:
        # Connect to device
        result = subprocess.run(
            ["adb", "connect", f"{DEVICE_IP}:5555"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )
        
        # Verify connection
        devices_result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
        
        if f"{DEVICE_IP}:5555" not in devices_result.stdout:
            print(f"{Colors.RED}[ERROR] ADB device not found in device list{Colors.RESET}")
            return False
        
        if "device" not in devices_result.stdout.split(f"{DEVICE_IP}:5555")[-1]:
            print(f"{Colors.RED}[ERROR] ADB device offline or unauthorized{Colors.RESET}")
            print(f"{Colors.YELLOW}[HINT] Check USB debugging authorization on device{Colors.RESET}")
            return False
        
        adb_connected = True
        print(f"{Colors.GREEN}[OK] ADB device connected: {DEVICE_ID}{Colors.RESET}")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}[ERROR] ADB connection timed out{Colors.RESET}")
        return False
        
    except FileNotFoundError:
        print(f"{Colors.RED}[ERROR] ADB command not found - install Android SDK Platform Tools{Colors.RESET}")
        return False
        
    except Exception as e:
        print(f"{Colors.RED}[ERROR] ADB connection failed: {e}{Colors.RESET}")
        return False

# ============================================================
# ADB UTILITY FUNCTIONS (from auto-prog.py)
# ============================================================

def adb_command(cmd: list, timeout: float = 10.0) -> Tuple[bool, str]:
    """
    Run an ADB command and return success status and output.
    Based on auto-prog.py adb() function.
    
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
            check=False  # Don't raise on non-zero exit
        )
        
        if result.stderr and result.returncode != 0:
            print(f"{Colors.YELLOW}[WARN] ADB stderr: {result.stderr.strip()}{Colors.RESET}")
        
        return result.returncode == 0, result.stdout.strip()
        
    except subprocess.TimeoutExpired:
        print(f"{Colors.YELLOW}[WARN] ADB command timed out: {' '.join(cmd)}{Colors.RESET}")
        return False, ""
        
    except Exception as e:
        print(f"{Colors.YELLOW}[WARN] ADB command failed: {e}{Colors.RESET}")
        return False, ""

def take_photo_adb() -> bool:
    """Trigger Android camera shutter (from auto-prog.py)"""
    for i in range(5, 0, -1):
        print(f"    Triggering in {i}...", end="\r")
        time.sleep(1)
    print(f"{Colors.BLUE}-> Triggering Android camera...{Colors.RESET}")
    success, _ = adb_command(["shell", "input", "keyevent", "27"], timeout=5.0)
    
    if success:
        time.sleep(2)  # Wait for photo to be saved
        return True
    
    print(f"{Colors.YELLOW}[WARN] Failed to trigger camera{Colors.RESET}")
    return False

def get_recent_photo_adb() -> Optional[str]:
    """Get newest photo file name from Android device (from auto-prog.py)"""
    success, output = adb_command(["shell", "ls", "-t", "/storage/emulated/0/DCIM/Camera/"])
    
    if success and output:
        lines = output.splitlines()
        if lines:
            return lines[0].strip()
    
    return None

def get_file_age_adb(file_path: str) -> int:
    """Calculate file age in seconds (from auto-prog.py)"""
    curr_time = int(time.time())
    success, output = adb_command(["shell", "stat", "-c", "%Y", file_path])
    
    if success and output:
        try:
            file_mod_time = int(output)
            return curr_time - file_mod_time
        except ValueError:
            print(f"{Colors.YELLOW}[WARN] Invalid timestamp from stat{Colors.RESET}")
    
    return 999999  # Very old if can't determine

def pull_recent_photo_adb(dest_folder: Path) -> Tuple[bool, Optional[str]]:
    """
    Take photo and pull it from device if recent enough (from auto-prog.py).
    
    Returns: (success, filename)
    """
    dest_folder.mkdir(exist_ok=True)
    
    retry_count = 0
    
    while retry_count < MAX_RETRIES:
        # Take photo
        if not take_photo_adb():
            retry_count += 1
            time.sleep(RETRY_SLEEP_TIME)
            continue
        
        # Get recent photo filename
        recent_file = get_recent_photo_adb()
        if not recent_file:
            print(f"{Colors.YELLOW}[WARN] No photo found on device (attempt {retry_count + 1}/{MAX_RETRIES}){Colors.RESET}")
            retry_count += 1
            time.sleep(RETRY_SLEEP_TIME)
            continue
        
        # Check file age
        file_path = f"/storage/emulated/0/DCIM/Camera/{recent_file}"
        age = get_file_age_adb(file_path)
        
        print(f"{Colors.CYAN}File: {recent_file}, Age: {age} seconds{Colors.RESET}")
        
        if age < PHOTO_AGE_LIMIT:
            print(f"{Colors.BLUE}-> Recent photo detected, pulling...{Colors.RESET}")
            
            # Pull photo
            success, _ = adb_command(["pull", file_path, str(dest_folder)], timeout=15.0)
            
            if success:
                # Delete photo from device
                adb_command(["shell", "rm", file_path], timeout=5.0)
                print(f"{Colors.GREEN}[OK] Photo captured and saved successfully{Colors.RESET}")
                return True, recent_file
            else:
                print(f"{Colors.YELLOW}[WARN] Failed to pull photo{Colors.RESET}")
        
        print(f"{Colors.YELLOW}[WARN] Photo too old or pull failed, retrying...{Colors.RESET}")
        retry_count += 1
        time.sleep(RETRY_SLEEP_TIME)
    
    print(f"{Colors.RED}[ERROR] No photo less than {PHOTO_AGE_LIMIT} seconds old found after {MAX_RETRIES} retries{Colors.RESET}")
    return False, None

def get_gps_location_adb() -> Tuple[Optional[float], Optional[float]]:
    """
    Get GPS location from Android device via ADB (from auto-prog.py).
    
    Returns: (latitude, longitude) or (None, None)
    """
    success, output = adb_command(["shell", "dumpsys", "location"], timeout=10.0)
    
    if not success or not output:
        return None, None
    
    try:
        # Find all lines containing "last location=Location" but not "null"
        locations = re.findall(r'last location=Location\[([^\]]+)\]', output)
        valid_locations = [loc for loc in locations if 'null' not in loc.lower()]
        
        if not valid_locations:
            return None, None
        
        # Take the last (latest) valid location
        latest_loc = valid_locations[-1]
        
        # Regex to extract latitude and longitude
        match = re.search(r'([-\d.]+),([-\d.]+)', latest_loc)
        
        if match:
            latitude = float(match.group(1))
            longitude = float(match.group(2))
            print(f"{Colors.GREEN}[OK] GPS: ({latitude:.6f}, {longitude:.6f}){Colors.RESET}")
            return latitude, longitude
        
    except Exception as e:
        print(f"{Colors.YELLOW}[WARN] GPS parsing error: {e}{Colors.RESET}")
    
    return None, None

# ============================================================
# RFID FUNCTIONS (from auto-prog.py)
# ============================================================

def read_rfid() -> Optional[str]:
    """
    Read RFID tag from Arduino via serial ACM0 with timeout.
    
    Returns: RFID tag string in format "RFID-{id}" or None
    """
    if rfid_reader is None:
        print(f"{Colors.RED}[ERROR] RFID reader not initialized{Colors.RESET}")
        return None
    
    try:
        print(f"\n{Colors.CYAN}-> [AUTO] Waiting for RFID scan from {RFID_SERIAL_PORT}...{Colors.RESET}")
        
        # Turn on scan LED (visual feedback)
        set_gpio_output(LED_SCAN, True)
        
        # Read from serial port in thread
        rfid_result = [None]
        read_error = [None]
        
        def read_thread():
            try:
                global ready_seen
                rfid_reader.reset_input_buffer()

                start_time = time.time()

                # ---------------------------------------
                # STEP 1: Only wait for READY ONCE
                # ---------------------------------------
                if not ready_seen:
                    print("Waiting for Arduino READY...")

                    while (time.time() - start_time) < RFID_READ_TIMEOUT:
                        if rfid_reader.in_waiting > 0:
                            line = rfid_reader.readline().decode('utf-8', errors='ignore').strip()

                            if not line:
                                continue

                            print(f"[SERIAL] {line}")

                            if line.upper() == "READY":
                                print("Arduino READY received.")
                                ready_seen = True
                                break

                        time.sleep(0.05)

                    if not ready_seen:
                        print("READY not received in time.")
                        return

                # ---------------------------------------
                # STEP 2: Read RFID NUMBER every time
                # ---------------------------------------
                print("Waiting for RFID number...")

                while (time.time() - start_time) < RFID_READ_TIMEOUT:
                    if rfid_reader.in_waiting > 0:
                        line = rfid_reader.readline().decode('utf-8', errors='ignore').strip()

                        if not line:
                            continue

                        print(f"[SERIAL] {line}")

                        # Numeric only
                        rfid_id = ''.join(filter(str.isdigit, line))

                        if rfid_id != "":
                            rfid_result[0] = rfid_id
                            return

                    time.sleep(0.05)

            except Exception as e:
                print(f"Error: {e}")
                read_error[0] = e

        thread = threading.Thread(target=read_thread, daemon=True, name="RFID-Reader")
        thread.start()
        thread.join(timeout=RFID_READ_TIMEOUT + 5)
        
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
# PHOTO CAPTURE (based on auto-prog.py)
# ============================================================

def capture_student_photo(config: Dict, student_id: str, script_dir: Path) -> Optional[str]:
    """
    Capture photo using ADB-based approach from auto-prog.py.
    
    Uses the proven workflow:
    1. Trigger camera via ADB keyevent
    2. Wait for photo to be saved
    3. Pull recent photo from device
    4. Delete from device
    
    Args:
        config: Configuration dict (not used but required for API compatibility)
        student_id: Student ID for naming
        script_dir: Base directory for photo storage
    
    Returns:
        Path to captured photo or None
    """
    print(f"{Colors.BLUE}-> [AUTO] Capturing photo for {student_id}...{Colors.RESET}")
    
    # Use temp photos directory
    temp_dir = script_dir / "temp_photos"
    temp_dir.mkdir(exist_ok=True)
    
    # Pull recent photo via ADB
    success, photo_filename = pull_recent_photo_adb(temp_dir)
    
    if not success or not photo_filename:
        print(f"{Colors.RED}[ERROR] Photo capture failed{Colors.RESET}")
        return None
    
    # Return full path
    photo_path = temp_dir / photo_filename
    
    if not photo_path.exists():
        print(f"{Colors.RED}[ERROR] Photo file not found: {photo_path}{Colors.RESET}")
        return None
    
    return str(photo_path)

# ============================================================
# FACE EMBEDDING (using DeepFace as specified)
# ============================================================

def generate_face_embedding(photo_path: str) -> Optional[np.ndarray]:
    """
    Generate face embedding using DeepFace with Facenet model.
    
    This uses the exact same approach as pi_hardware.py:
    - Model: Facenet
    - enforce_detection: False
    - Returns: np.float32 array
    
    This embedding will be compared using cosine similarity in pi_server.py.
    
    Args:
        photo_path: Path to photo file
    
    Returns:
        Numpy array embedding or None if failed
    """
    try:
        from deepface import DeepFace
        
        print(f"{Colors.BLUE}-> [AUTO] Generating face embedding...{Colors.RESET}")
        
        # Verify photo exists
        if not Path(photo_path).exists():
            print(f"{Colors.RED}[ERROR] Photo not found: {photo_path}{Colors.RESET}")
            return None
        
        # Generate embedding using DeepFace with Facenet model
        # This matches the exact approach in pi_hardware.py
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
            
    except ImportError:
        print(f"{Colors.RED}[ERROR] DeepFace not installed{Colors.RESET}")
        return None
        
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Embedding generation failed: {e}{Colors.RESET}")
        return None

# ============================================================
# NETWORK FUNCTIONS
# ============================================================

def send_packet(config: Dict, payload: Dict) -> bool:
    """
    Send data packet to backend (scan event).
    
    Adds GPS location from ADB if available.
    
    Args:
        config: Configuration dict with backend_url and api_key
        payload: Data payload to send
    
    Returns:
        True if successful, False otherwise
    """
    try:
        import requests
        
        print(f"{Colors.BLUE}-> [AUTO] Sending packet to backend...{Colors.RESET}")
        
        # Add GPS location if available (from auto-prog.py workflow)
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
    
    This function is called by pi_server.py for continuous location updates.
    
    Returns:
        Dict with 'lat' and 'lon' keys
    """
    try:
        lat, lon = get_gps_location_adb()
        return {"lat": lat, "lon": lon}
    except Exception as e:
        print(f"{Colors.YELLOW}[WARN] GPS error: {e}{Colors.RESET}")
        return {"lat": None, "lon": None}

# ============================================================
# CAMERA THREAD FUNCTIONS (for API compatibility)
# ============================================================

def start_camera_thread() -> bool:
    """
    Start camera thread (not used in auto-prog workflow).
    
    The auto-prog.py approach uses on-demand photo capture via ADB,
    not continuous streaming. This function exists for API compatibility
    with pi_server.py but returns False to indicate no thread was started.
    
    Returns:
        False - camera thread not used in this backend
    """
    print(f"{Colors.CYAN}[INFO] Camera thread not used in auto-prog backend (uses on-demand ADB capture){Colors.RESET}")
    return False

def stop_camera_thread() -> None:
    """
    Stop camera thread (not used in auto-prog workflow).
    
    Exists for API compatibility with pi_server.py.
    """
    pass

def get_latest_face(student_id: str, script_dir: Path) -> Optional[str]:
    """
    Get latest face from camera thread (not used in auto-prog workflow).
    
    The auto-prog.py approach doesn't use a camera thread, so this
    returns None to signal that capture_student_photo() should be used instead.
    
    Returns:
        None - signals to use capture_student_photo() instead
    """
    return None

# ============================================================
# CLEANUP
# ============================================================

def cleanup() -> None:
    """
    Cleanup hardware resources safely.
    
    Performs cleanup of:
    - GPIO pins
    - LED states
    - Serial port connection
    """
    print(f"{Colors.CYAN}-> [AUTO] Cleaning up hardware resources...{Colors.RESET}")
    
    # Close serial port
    global rfid_reader
    if rfid_reader is not None:
        try:
            if rfid_reader.is_open:
                rfid_reader.close()
                print(f"{Colors.GREEN}[OK] Serial port closed{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.YELLOW}[WARN] Serial port cleanup warning: {e}{Colors.RESET}")
    
    # Reset GPIO to default state
    if gpio_available:
        try:
            import RPi.GPIO as GPIO
            
            # Turn off all LEDs
            default_gpio_state()
            
            # Cleanup GPIO
            GPIO.cleanup()
            print(f"{Colors.GREEN}[OK] GPIO cleaned up{Colors.RESET}")
            
        except Exception as e:
            print(f"{Colors.YELLOW}[WARN] GPIO cleanup warning: {e}{Colors.RESET}")
    
    print(f"{Colors.CYAN}-> [AUTO] Hardware cleanup complete{Colors.RESET}")
