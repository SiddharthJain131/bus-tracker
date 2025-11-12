"""
Example Configuration for Local Device Simulator
Copy this file to the configuration section of local_device_simulator.py
"""

# Backend API base URL
BASE_URL = "https://user-photo-view.preview.emergentagent.com/"

# Device API Key (EXAMPLE - Replace with your actual key from device registration)
# Get your key by running: POST /api/device/register as admin
DEVICE_API_KEY = "295c6f8e454ebfa3e6d7929272f3ad98435193dba9fee7780dcc1c33c7fdc7fb"

# Bus ID this device is assigned to (UUID format from database)
BUS_ID = "3ca09d6a-2650-40e7-a874-5b2879025aff"

# Test Student ID for embedding/photo retrieval (UUID format from database)
# Get student IDs from: GET /api/students
STUDENT_ID = "9afb783f-7952-476d-8626-0143fdbbc2a1"  # Emma Johnson

# Test image path (for scan events with photo upload)
# Place a JPEG image in the tests directory
TEST_IMAGE_PATH = "test_scan_photo.txt"

# GPS coordinates for testing (San Francisco coordinates as example)
TEST_GPS_LAT = 37.7749
TEST_GPS_LON = -122.4194
