#!/usr/bin/env python3
"""
Local Device Simulator - Test Raspberry Pi API Calls
Simulates a registered Raspberry Pi device for testing device-only endpoints
"""

import requests
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import os

# ============================================================
# CONFIGURATION - Modify these values for your environment
# ============================================================

# Backend API base URL
BASE_URL = "http://localhost:8001"

# Device API Key (obtain from admin panel: Device Management > Register Device)
# Replace with your actual API key after registering a device
DEVICE_API_KEY = "your_device_api_key_here"

# Bus ID this device is assigned to (UUID format - get from GET /api/buses)
BUS_ID = "your_bus_id_here"

# Test Student ID for embedding/photo retrieval (UUID format - get from GET /api/students)
STUDENT_ID = "your_student_id_here"

# Test image path (for scan events with photo upload)
TEST_IMAGE_PATH = "test_scan_photo.jpg"

# GPS coordinates for testing (San Francisco example)
TEST_GPS_LAT = 37.7749
TEST_GPS_LON = -122.4194

# Log file path
LOG_FILE = Path(__file__).parent / "device_test_log.txt"

# ============================================================
# COLOR CODES FOR TERMINAL OUTPUT
# ============================================================

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# ============================================================
# LOGGING FUNCTIONS
# ============================================================

def log_message(message: str, level: str = "INFO"):
    """Log message to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    
    # Print to console (without color codes in file)
    print(message)
    
    # Write to log file
    try:
        with open(LOG_FILE, 'a') as f:
            # Remove color codes for file logging
            clean_entry = log_entry
            for color in [Colors.GREEN, Colors.RED, Colors.YELLOW, Colors.BLUE, 
                         Colors.CYAN, Colors.RESET, Colors.BOLD]:
                clean_entry = clean_entry.replace(color, '')
            f.write(clean_entry + '\n')
    except Exception as e:
        print(f"Warning: Failed to write to log file: {e}")


def log_response(response: requests.Response, endpoint: str):
    """Log API response details"""
    log_message(f"\n{'='*60}", "DEBUG")
    log_message(f"Endpoint: {endpoint}", "DEBUG")
    log_message(f"Status Code: {response.status_code}", "DEBUG")
    log_message(f"Response Headers: {dict(response.headers)}", "DEBUG")
    try:
        log_message(f"Response Body: {response.json()}", "DEBUG")
    except:
        log_message(f"Response Body: {response.text[:500]}", "DEBUG")
    log_message(f"{'='*60}\n", "DEBUG")


# ============================================================
# API TESTING FUNCTIONS
# ============================================================

def get_headers() -> Dict[str, str]:
    """Get API headers with device key"""
    return {
        'X-API-Key': DEVICE_API_KEY,
        'Content-Type': 'application/json'
    }


def test_get_embedding() -> bool:
    """
    Test GET /api/students/{id}/embedding
    Retrieves student face embedding data for local verification
    """
    log_message(f"\n{Colors.CYAN}{Colors.BOLD}🔍 Testing: Get Student Embedding{Colors.RESET}")
    log_message(f"{Colors.BLUE}Endpoint: GET {BASE_URL}/api/students/{STUDENT_ID}/embedding{Colors.RESET}")
    
    try:
        headers = get_headers()
        response = requests.get(
            f"{BASE_URL}/api/students/{STUDENT_ID}/embedding",
            headers=headers,
            timeout=10
        )
        
        log_response(response, f"GET /api/students/{STUDENT_ID}/embedding")
        
        if response.status_code == 200:
            data = response.json()
            log_message(f"{Colors.GREEN}✅ SUCCESS{Colors.RESET}")
            log_message(f"   Student: {data.get('name')}")
            log_message(f"   Has Embedding: {data.get('has_embedding')}")
            if data.get('embedding'):
                log_message(f"   Embedding Length: {len(str(data.get('embedding')))} chars")
            return True
        else:
            log_message(f"{Colors.RED}❌ FAILED - Status: {response.status_code}{Colors.RESET}")
            log_message(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        log_message(f"{Colors.RED}❌ EXCEPTION: {str(e)}{Colors.RESET}")
        return False


def test_get_photo() -> bool:
    """
    Test GET /api/students/{id}/photo
    Retrieves student photo URL as fallback
    """
    log_message(f"\n{Colors.CYAN}{Colors.BOLD}📷 Testing: Get Student Photo{Colors.RESET}")
    log_message(f"{Colors.BLUE}Endpoint: GET {BASE_URL}/api/students/{STUDENT_ID}/photo{Colors.RESET}")
    
    try:
        headers = get_headers()
        response = requests.get(
            f"{BASE_URL}/api/students/{STUDENT_ID}/photo",
            headers=headers,
            timeout=10
        )
        
        log_response(response, f"GET /api/students/{STUDENT_ID}/photo")
        
        if response.status_code == 200:
            data = response.json()
            log_message(f"{Colors.GREEN}✅ SUCCESS{Colors.RESET}")
            log_message(f"   Student: {data.get('name')}")
            log_message(f"   Has Photo: {data.get('has_photo')}")
            if data.get('photo_url'):
                log_message(f"   Photo URL: {data.get('photo_url')}")
            return True
        else:
            log_message(f"{Colors.RED}❌ FAILED - Status: {response.status_code}{Colors.RESET}")
            log_message(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        log_message(f"{Colors.RED}❌ EXCEPTION: {str(e)}{Colors.RESET}")
        return False


def test_scan_event(scan_type: str = "yellow") -> bool:
    """
    Test POST /api/scan_event
    Sends scan event with GPS coordinates and optional photo
    
    Args:
        scan_type: "yellow" for On Board, "green" for Reached
    """
    scan_label = "On Board (Yellow)" if scan_type == "yellow" else "Reached (Green)"
    log_message(f"\n{Colors.CYAN}{Colors.BOLD}🎫 Testing: Scan Event - {scan_label}{Colors.RESET}")
    log_message(f"{Colors.BLUE}Endpoint: POST {BASE_URL}/api/scan_event{Colors.RESET}")
    
    try:
        # Prepare scan data
        scan_data = {
            "student_id": STUDENT_ID,
            "tag_id": "RFID-TEST-001",
            "verified": True,
            "confidence": 0.95,  # Face recognition confidence (0.0 to 1.0)
            "scan_type": scan_type,
            "lat": TEST_GPS_LAT,
            "lon": TEST_GPS_LON
        }
        
        # Add photo if file exists
        photo_base64 = None
        if Path(TEST_IMAGE_PATH).exists():
            with open(TEST_IMAGE_PATH, 'rb') as f:
                photo_bytes = f.read()
                photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
                scan_data["photo_base64"] = photo_base64
                log_message(f"   📸 Photo included: {TEST_IMAGE_PATH} ({len(photo_bytes)} bytes)")
        else:
            log_message(f"   ℹ️  No photo file found at {TEST_IMAGE_PATH}, sending without photo")
        
        headers = get_headers()
        response = requests.post(
            f"{BASE_URL}/api/scan_event",
            headers=headers,
            json=scan_data,
            timeout=15
        )
        
        log_response(response, "POST /api/scan_event")
        
        if response.status_code == 200:
            data = response.json()
            log_message(f"{Colors.GREEN}✅ SUCCESS{Colors.RESET}")
            log_message(f"   Status: {data.get('status')}")
            log_message(f"   Message: {data.get('message')}")
            log_message(f"   Attendance Status: {data.get('attendance_status')}")
            log_message(f"   GPS: ({TEST_GPS_LAT}, {TEST_GPS_LON})")
            return True
        else:
            log_message(f"{Colors.RED}❌ FAILED - Status: {response.status_code}{Colors.RESET}")
            log_message(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        log_message(f"{Colors.RED}❌ EXCEPTION: {str(e)}{Colors.RESET}")
        return False


def test_update_location() -> bool:
    """
    Test POST /api/update_location
    Updates bus GPS location
    """
    log_message(f"\n{Colors.CYAN}{Colors.BOLD}📍 Testing: Update Bus Location{Colors.RESET}")
    log_message(f"{Colors.BLUE}Endpoint: POST {BASE_URL}/api/update_location{Colors.RESET}")
    
    try:
        location_data = {
            "bus_id": BUS_ID,
            "lat": TEST_GPS_LAT,
            "lon": TEST_GPS_LON
        }
        
        headers = get_headers()
        response = requests.post(
            f"{BASE_URL}/api/update_location",
            headers=headers,
            json=location_data,
            timeout=10
        )
        
        log_response(response, "POST /api/update_location")
        
        if response.status_code == 200:
            data = response.json()
            log_message(f"{Colors.GREEN}✅ SUCCESS{Colors.RESET}")
            log_message(f"   Status: {data.get('status')}")
            log_message(f"   Bus ID: {BUS_ID}")
            log_message(f"   GPS: ({TEST_GPS_LAT}, {TEST_GPS_LON})")
            return True
        else:
            log_message(f"{Colors.RED}❌ FAILED - Status: {response.status_code}{Colors.RESET}")
            log_message(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        log_message(f"{Colors.RED}❌ EXCEPTION: {str(e)}{Colors.RESET}")
        return False


def run_all_tests() -> Dict[str, bool]:
    """
    Run all API tests sequentially
    Returns dictionary with test results
    """
    log_message(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    log_message(f"{Colors.BOLD}🚀 Running All Device API Tests{Colors.RESET}")
    log_message(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    
    results = {
        "get_embedding": test_get_embedding(),
        "get_photo": test_get_photo(),
        "scan_yellow": test_scan_event("yellow"),
        "scan_green": test_scan_event("green"),
        "update_location": test_update_location()
    }
    
    # Print summary
    log_message(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    log_message(f"{Colors.BOLD}📊 Test Summary{Colors.RESET}")
    log_message(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✅ PASSED{Colors.RESET}" if result else f"{Colors.RED}❌ FAILED{Colors.RESET}"
        log_message(f"   {test_name}: {status}")
    
    success_rate = (passed / total) * 100
    log_message(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed ({success_rate:.0f}%){Colors.RESET}")
    
    return results


# ============================================================
# INTERACTIVE CLI MENU
# ============================================================

def print_menu():
    """Print interactive menu"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}🚌 Bus Tracker - Device API Simulator{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"\n{Colors.YELLOW}Configuration:{Colors.RESET}")
    print(f"   • Base URL: {BASE_URL}")
    print(f"   • Bus ID: {BUS_ID}")
    print(f"   • Student ID: {STUDENT_ID}")
    print(f"   • API Key: {'Configured ✓' if DEVICE_API_KEY != 'your_device_api_key_here' else 'NOT SET ⚠️'}")
    print(f"\n{Colors.YELLOW}Test Menu:{Colors.RESET}")
    print(f"   {Colors.CYAN}[1]{Colors.RESET} Get Student Embedding")
    print(f"   {Colors.CYAN}[2]{Colors.RESET} Get Student Photo")
    print(f"   {Colors.CYAN}[3]{Colors.RESET} Send Yellow Scan (On Board)")
    print(f"   {Colors.CYAN}[4]{Colors.RESET} Send Green Scan (Reached)")
    print(f"   {Colors.CYAN}[5]{Colors.RESET} Update GPS Location")
    print(f"   {Colors.CYAN}[6]{Colors.RESET} Run All Tests")
    print(f"   {Colors.CYAN}[0]{Colors.RESET} Exit")
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")


def validate_config() -> bool:
    """Validate configuration before running tests"""
    if DEVICE_API_KEY == "your_device_api_key_here":
        print(f"\n{Colors.RED}{Colors.BOLD}❌ ERROR: Device API Key not configured{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Please follow these steps:{Colors.RESET}")
        print(f"   1. Login as admin: {Colors.CYAN}admin@school.com{Colors.RESET} / {Colors.CYAN}password{Colors.RESET}")
        print(f"   2. Navigate to Device Management")
        print(f"   3. Register a new device for bus {Colors.CYAN}{BUS_ID}{Colors.RESET}")
        print(f"   4. Copy the generated API key")
        print(f"   5. Update {Colors.CYAN}DEVICE_API_KEY{Colors.RESET} in this script")
        print(f"\n{Colors.YELLOW}Or use the API:{Colors.RESET}")
        print(f"   curl -X POST {BASE_URL}/api/device/register \\")
        print(f"        -H 'Cookie: session=<admin_session>' \\")
        print(f"        -H 'Content-Type: application/json' \\")
        print(f"        -d '{{\"bus_id\":\"{BUS_ID}\", \"device_name\":\"Test Device\"}}'")
        return False
    return True


def interactive_menu():
    """Run interactive CLI menu"""
    # Initialize log file
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Device Simulator Started: {datetime.now().isoformat()}\n")
        f.write(f"{'='*60}\n\n")
    
    while True:
        print_menu()
        
        if not validate_config():
            input(f"\n{Colors.YELLOW}Press Enter to exit...{Colors.RESET}")
            break
        
        try:
            choice = input(f"\n{Colors.BOLD}Select option: {Colors.RESET}").strip()
            
            if choice == "0":
                log_message(f"\n{Colors.CYAN}👋 Exiting Device Simulator{Colors.RESET}")
                break
            elif choice == "1":
                test_get_embedding()
            elif choice == "2":
                test_get_photo()
            elif choice == "3":
                test_scan_event("yellow")
            elif choice == "4":
                test_scan_event("green")
            elif choice == "5":
                test_update_location()
            elif choice == "6":
                run_all_tests()
            else:
                print(f"{Colors.RED}Invalid option. Please try again.{Colors.RESET}")
            
            input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
            
        except KeyboardInterrupt:
            log_message(f"\n\n{Colors.CYAN}👋 Exiting Device Simulator (Ctrl+C){Colors.RESET}")
            break
        except Exception as e:
            log_message(f"{Colors.RED}Unexpected error: {e}{Colors.RESET}")


# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--run-all":
        # Non-interactive mode: run all tests
        if validate_config():
            run_all_tests()
        else:
            sys.exit(1)
    else:
        # Interactive mode
        interactive_menu()
