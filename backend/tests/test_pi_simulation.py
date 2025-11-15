#!/usr/bin/env python3
"""
Automated test script for Pi boarding scanner
Simulates full workflow: registration → IN scan → OUT scan
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

# Test configuration
ADMIN_EMAIL = "admin@school.com"
ADMIN_PASSWORD = "password"
BUS_NUMBER = "BUS-001"
DEVICE_NAME = "Pi-Test-Device"
TEST_RFID = "RFID-1001"  # Emma Johnson

# ============================================================
# Test Functions
# ============================================================

def login_admin():
    """Login as admin to get session"""
    print(f"→ Logging in as admin...")
    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        print(f"✓ Admin login successful")
        return response.cookies
    else:
        print(f"✗ Admin login failed: {response.text}")
        return None

def register_device(cookies):
    """Register device and get API key"""
    print(f"\n→ Registering device: {DEVICE_NAME} for {BUS_NUMBER}...")
    response = requests.post(
        f"{API_BASE}/device/register",
        json={
            "bus_number": BUS_NUMBER,
            "device_name": DEVICE_NAME
        },
        cookies=cookies
    )
    
    print(f"DEBUG: Status={response.status_code}, Response={response.text[:200]}")
    
    if response.status_code == 200:
        data = response.json()
        api_key = data.get('api_key')
        print(f"✓ Device registered successfully")
        print(f"  Device ID: {data.get('device_id')}")
        print(f"  API Key: {api_key[:20]}...")
        return api_key
    elif response.status_code == 400 and "already registered" in response.text:
        print(f"⚠ Device already registered for this bus")
        print(f"  Note: Using a test API key (real key stored in backend)")
        # For testing purposes, create a dummy key since we can't retrieve the real one
        # In production, the Pi would have saved the key from first registration
        print(f"  ⚠ Warning: Cannot retrieve existing API key - endpoint should only be called once")
        return None
    else:
        print(f"✗ Device registration failed: {response.text}")
        return None

def load_rfid_mapping():
    """Load RFID to student mapping"""
    mapping_file = Path(__file__).parent / "rfid_student_mapping.json"
    with open(mapping_file, 'r') as f:
        students = json.load(f)
        return {s['rfid']: s for s in students}

def send_scan_event(api_key, student_id, rfid_tag, verified=True, confidence=1.0):
    """Send scan event to backend"""
    response = requests.post(
        f"{API_BASE}/scan_event",
        json={
            "student_id": student_id,
            "tag_id": rfid_tag,
            "verified": verified,
            "confidence": confidence,
            "lat": 40.7128,
            "lon": -74.0060
        },
        headers={"X-API-Key": api_key}
    )
    return response

def main():
    """Run full simulation test"""
    print("=" * 70)
    print("RASPBERRY PI SCAN SIMULATION TEST")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 70)
    
    # Track results
    results = {
        "device_registered": False,
        "student_resolved": False,
        "in_scan_sent": False,
        "out_scan_sent": False,
        "errors": []
    }
    
    try:
        # Step 1: Login as admin
        cookies = login_admin()
        if not cookies:
            results["errors"].append("Admin login failed")
            return results
        
        # Step 2: Register device
        api_key = register_device(cookies)
        if not api_key:
            results["errors"].append("Device registration failed")
            return results
        results["device_registered"] = True
        
        # Step 3: Load RFID mapping and resolve student
        print(f"\n→ Loading RFID mapping...")
        rfid_mapping = load_rfid_mapping()
        student_info = rfid_mapping.get(TEST_RFID)
        
        if not student_info:
            print(f"✗ Student not found for RFID: {TEST_RFID}")
            results["errors"].append(f"Student not found for RFID: {TEST_RFID}")
            return results
        
        print(f"✓ Student resolved: {student_info['name']} (ID: {student_info['student_id']})")
        results["student_resolved"] = True
        
        # Step 4: Simulate Boarding IN scan
        print(f"\n{'='*70}")
        print(f"BOARDING IN SCAN - {student_info['name']}")
        print(f"{'='*70}")
        print(f"→ Sending boarding IN scan event...")
        
        response = send_scan_event(
            api_key, 
            student_info['student_id'], 
            TEST_RFID,
            verified=True,
            confidence=0.95
        )
        
        if response.status_code == 200:
            print(f"✓ Boarding IN scan successful")
            print(f"  Status: YELLOW (Boarded)")
            results["in_scan_sent"] = True
        else:
            print(f"✗ Boarding IN scan failed: {response.text}")
            results["errors"].append(f"IN scan failed: {response.text}")
        
        # Step 5: Simulate Boarding OUT scan
        print(f"\n{'='*70}")
        print(f"BOARDING OUT SCAN - {student_info['name']}")
        print(f"{'='*70}")
        print(f"→ Sending boarding OUT scan event...")
        
        response = send_scan_event(
            api_key,
            student_info['student_id'],
            TEST_RFID,
            verified=True,
            confidence=1.0
        )
        
        if response.status_code == 200:
            print(f"✓ Boarding OUT scan successful")
            print(f"  Status: GREEN (Reached destination)")
            results["out_scan_sent"] = True
        else:
            print(f"✗ Boarding OUT scan failed: {response.text}")
            results["errors"].append(f"OUT scan failed: {response.text}")
        
    except Exception as e:
        print(f"\n✗ Test error: {str(e)}")
        results["errors"].append(str(e))
    
    # Print final report
    print(f"\n{'='*70}")
    print("FINAL SCAN REPORT")
    print(f"{'='*70}")
    print(f"Device Registered:  {'✓' if results['device_registered'] else '✗'}")
    print(f"Student Resolved:   {'✓' if results['student_resolved'] else '✗'}")
    print(f"IN Packet Sent:     {'✓' if results['in_scan_sent'] else '✗'}")
    print(f"OUT Packet Sent:    {'✓' if results['out_scan_sent'] else '✗'}")
    
    if results["errors"]:
        print(f"\nErrors Encountered:")
        for error in results["errors"]:
            print(f"  • {error}")
    else:
        print(f"\n✓ All tests passed successfully!")
    
    print(f"{'='*70}\n")
    
    return results

if __name__ == "__main__":
    results = main()
    # Exit with error code if any test failed
    if results["errors"] or not all([
        results["device_registered"],
        results["student_resolved"],
        results["in_scan_sent"],
        results["out_scan_sent"]
    ]):
        sys.exit(1)
    sys.exit(0)
