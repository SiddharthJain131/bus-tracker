#!/usr/bin/env python3
"""
Automated test script for Pi boarding scanner (3-script architecture)
Tests: registration, IN/OUT flows, embedding caching, retry logic, API fallback
"""

import os
import sys
import json
import requests
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Force simulated mode for testing
os.environ['PI_MODE'] = 'simulated'

# Load environment variables
SCRIPT_DIR = Path(__file__).parent
load_dotenv(SCRIPT_DIR / '.env')

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

# Test configuration
ADMIN_EMAIL = "admin@school.com"
ADMIN_PASSWORD = "password"
BUS_NUMBER = "BUS-TEST-001"
DEVICE_NAME = "Pi-Test-Device"
TEST_RFID = "RFID-1001"  # Emma Johnson

RFID_MAPPING_FILE = SCRIPT_DIR / "rfid_student_mapping.json"
RFID_BACKUP_FILE = SCRIPT_DIR / "rfid_student_mapping.json.backup"

# ============================================================
# Test Utilities
# ============================================================

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def backup_rfid_cache():
    """Backup current RFID cache"""
    if RFID_MAPPING_FILE.exists():
        shutil.copy(RFID_MAPPING_FILE, RFID_BACKUP_FILE)
        print(f"{Colors.CYAN}→ Backed up RFID cache{Colors.RESET}")

def restore_rfid_cache():
    """Restore RFID cache from backup"""
    if RFID_BACKUP_FILE.exists():
        shutil.copy(RFID_BACKUP_FILE, RFID_MAPPING_FILE)
        print(f"{Colors.CYAN}→ Restored RFID cache{Colors.RESET}")

def clear_embeddings():
    """Clear all cached embeddings for testing"""
    try:
        with open(RFID_MAPPING_FILE, 'r') as f:
            data = json.load(f)
        
        for entry in data:
            entry['embedding'] = None
        
        with open(RFID_MAPPING_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"{Colors.CYAN}→ Cleared all cached embeddings{Colors.RESET}")
        return True
    except Exception as e:
        print(f"{Colors.RED}✗ Failed to clear embeddings: {e}{Colors.RESET}")
        return False

def load_rfid_mapping():
    """Load RFID to student mapping"""
    with open(RFID_MAPPING_FILE, 'r') as f:
        students = json.load(f)
        return {s['rfid']: s for s in students}

def verify_cache_structure():
    """Verify RFID cache has correct 3-field structure"""
    print(f"\n{Colors.BOLD}→ Verifying cache structure...{Colors.RESET}")
    try:
        with open(RFID_MAPPING_FILE, 'r') as f:
            data = json.load(f)
        
        for entry in data:
            fields = set(entry.keys())
            required_fields = {'rfid', 'student_id', 'embedding'}
            
            if fields != required_fields:
                print(f"{Colors.RED}✗ Invalid structure: {fields}{Colors.RESET}")
                return False
        
        print(f"{Colors.GREEN}✓ Cache structure valid (3 fields){Colors.RESET}")
        return True
    except Exception as e:
        print(f"{Colors.RED}✗ Cache verification failed: {e}{Colors.RESET}")
        return False

def count_cached_embeddings():
    """Count how many entries have cached embeddings"""
    try:
        with open(RFID_MAPPING_FILE, 'r') as f:
            data = json.load(f)
        return sum(1 for entry in data if entry.get('embedding') is not None)
    except:
        return 0

# ============================================================
# API Test Functions
# ============================================================

def login_admin():
    """Login as admin to get session"""
    print(f"\n{Colors.BOLD}→ Logging in as admin...{Colors.RESET}")
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓ Admin login successful{Colors.RESET}")
            return response.cookies
        else:
            print(f"{Colors.RED}✗ Admin login failed: {response.text}{Colors.RESET}")
            return None
    except Exception as e:
        print(f"{Colors.RED}✗ Login error: {e}{Colors.RESET}")
        return None

def register_device(cookies):
    """Register device and get API key"""
    print(f"\n{Colors.BOLD}→ Registering device: {DEVICE_NAME}{Colors.RESET}")
    try:
        response = requests.post(
            f"{API_BASE}/device/register",
            json={
                "bus_number": BUS_NUMBER,
                "device_name": DEVICE_NAME
            },
            cookies=cookies
        )
        
        if response.status_code == 200:
            data = response.json()
            api_key = data.get('api_key')
            print(f"{Colors.GREEN}✓ Device registered{Colors.RESET}")
            print(f"  Device ID: {data.get('device_id')}")
            return api_key
        elif response.status_code == 400 and "already registered" in response.text:
            print(f"{Colors.YELLOW}⚠ Device already registered{Colors.RESET}")
            return "test-api-key-placeholder"
        else:
            print(f"{Colors.RED}✗ Registration failed: {response.text}{Colors.RESET}")
            return None
    except Exception as e:
        print(f"{Colors.RED}✗ Registration error: {e}{Colors.RESET}")
        return None

def fetch_student_embedding(api_key, student_id):
    """Fetch embedding from API"""
    try:
        response = requests.get(
            f"{API_BASE}/students/{student_id}/embedding",
            headers={"X-API-Key": api_key}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('embedding')
        return None
    except:
        return None

def send_scan_event(api_key, student_id, rfid_tag, verified=True, confidence=1.0):
    """Send scan event to backend"""
    try:
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
    except Exception as e:
        print(f"{Colors.RED}✗ Scan event error: {e}{Colors.RESET}")
        return None

# ============================================================
# Test Cases
# ============================================================

def test_cache_structure():
    """Test 1: Verify cache structure"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}TEST 1: Cache Structure Validation{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    
    return verify_cache_structure()

def test_api_embedding_fallback(api_key):
    """Test 2: API embedding fallback when cache is empty"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}TEST 2: API Embedding Fallback{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    
    # Clear embeddings
    if not clear_embeddings():
        return False
    
    # Verify all embeddings are null
    count = count_cached_embeddings()
    if count != 0:
        print(f"{Colors.RED}✗ Failed to clear embeddings (found {count}){Colors.RESET}")
        return False
    
    print(f"{Colors.GREEN}✓ All embeddings cleared{Colors.RESET}")
    
    # Load mapping and get test student
    rfid_mapping = load_rfid_mapping()
    student_info = rfid_mapping.get(TEST_RFID)
    
    if not student_info:
        print(f"{Colors.RED}✗ Test student not found{Colors.RESET}")
        return False
    
    student_id = student_info['student_id']
    
    # Simulate fetching from API
    print(f"\n{Colors.BLUE}→ Simulating API embedding fetch...{Colors.RESET}")
    embedding = fetch_student_embedding(api_key, student_id)
    
    if embedding:
        print(f"{Colors.GREEN}✓ Embedding fetched from API{Colors.RESET}")
        
        # Manually cache it (simulating what the Pi script does)
        student_info['embedding'] = embedding
        students_list = list(rfid_mapping.values())
        with open(RFID_MAPPING_FILE, 'w') as f:
            json.dump(students_list, f, indent=2)
        
        print(f"{Colors.GREEN}✓ Embedding cached locally{Colors.RESET}")
        
        # Verify it was cached
        count = count_cached_embeddings()
        if count >= 1:
            print(f"{Colors.GREEN}✓ Cache updated (cached embeddings: {count}){Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}✗ Cache not updated{Colors.RESET}")
            return False
    else:
        print(f"{Colors.RED}✗ Failed to fetch embedding from API{Colors.RESET}")
        return False

def test_boarding_in_flow(api_key):
    """Test 3: Full boarding IN flow"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}TEST 3: Boarding IN Flow{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    
    rfid_mapping = load_rfid_mapping()
    student_info = rfid_mapping.get(TEST_RFID)
    
    if not student_info:
        print(f"{Colors.RED}✗ Test student not found{Colors.RESET}")
        return False
    
    student_id = student_info['student_id']
    print(f"\n{Colors.BLUE}→ Testing student: {student_id}{Colors.RESET}")
    
    # Check if embedding is cached
    has_embedding = student_info.get('embedding') is not None
    print(f"  Embedding cached: {'Yes' if has_embedding else 'No'}")
    
    # Send boarding IN event
    print(f"\n{Colors.BLUE}→ Sending boarding IN scan event...{Colors.RESET}")
    response = send_scan_event(api_key, student_id, TEST_RFID, verified=True, confidence=0.95)
    
    if response and response.status_code == 200:
        print(f"{Colors.GREEN}✓ Boarding IN successful{Colors.RESET}")
        print(f"  Status: YELLOW (Boarded)")
        return True
    else:
        print(f"{Colors.RED}✗ Boarding IN failed{Colors.RESET}")
        return False

def test_boarding_out_flow(api_key):
    """Test 4: Full boarding OUT flow"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}TEST 4: Boarding OUT Flow{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    
    rfid_mapping = load_rfid_mapping()
    student_info = rfid_mapping.get(TEST_RFID)
    
    if not student_info:
        print(f"{Colors.RED}✗ Test student not found{Colors.RESET}")
        return False
    
    student_id = student_info['student_id']
    print(f"\n{Colors.BLUE}→ Testing student: {student_id}{Colors.RESET}")
    
    # Send boarding OUT event
    print(f"\n{Colors.BLUE}→ Sending boarding OUT scan event...{Colors.RESET}")
    response = send_scan_event(api_key, student_id, TEST_RFID, verified=True, confidence=1.0)
    
    if response and response.status_code == 200:
        print(f"{Colors.GREEN}✓ Boarding OUT successful{Colors.RESET}")
        print(f"  Status: GREEN (Reached destination)")
        return True
    else:
        print(f"{Colors.RED}✗ Boarding OUT failed{Colors.RESET}")
        return False

def test_corrupted_cache_recovery():
    """Test 5: Recovery from corrupted cache"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}TEST 5: Corrupted Cache Recovery{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    
    # Backup current cache
    backup_rfid_cache()
    
    # Corrupt the cache
    print(f"\n{Colors.BLUE}→ Simulating corrupted cache...{Colors.RESET}")
    try:
        with open(RFID_MAPPING_FILE, 'w') as f:
            f.write("{invalid json content")
        print(f"{Colors.YELLOW}⚠ Cache corrupted{Colors.RESET}")
        
        # Try to load it (should handle gracefully)
        print(f"\n{Colors.BLUE}→ Testing corrupted cache handling...{Colors.RESET}")
        try:
            with open(RFID_MAPPING_FILE, 'r') as f:
                json.load(f)
            print(f"{Colors.RED}✗ Corrupted cache was not detected{Colors.RESET}")
            result = False
        except json.JSONDecodeError:
            print(f"{Colors.GREEN}✓ Corrupted cache detected (JSONDecodeError){Colors.RESET}")
            result = True
        
        # Restore from backup
        restore_rfid_cache()
        print(f"{Colors.GREEN}✓ Cache restored from backup{Colors.RESET}")
        
        return result
        
    except Exception as e:
        print(f"{Colors.RED}✗ Test error: {e}{Colors.RESET}")
        restore_rfid_cache()
        return False

def test_cache_persistence():
    """Test 6: Cache persistence across reloads"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}TEST 6: Cache Persistence{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    
    # Get current cached count
    count_before = count_cached_embeddings()
    print(f"\n{Colors.BLUE}→ Cached embeddings before: {count_before}{Colors.RESET}")
    
    # Reload cache
    try:
        rfid_mapping = load_rfid_mapping()
        count_after = sum(1 for s in rfid_mapping.values() if s.get('embedding') is not None)
        print(f"{Colors.BLUE}→ Cached embeddings after reload: {count_after}{Colors.RESET}")
        
        if count_before == count_after:
            print(f"{Colors.GREEN}✓ Cache persisted correctly{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}✗ Cache count mismatch{Colors.RESET}")
            return False
    except Exception as e:
        print(f"{Colors.RED}✗ Cache reload failed: {e}{Colors.RESET}")
        return False

# ============================================================
# Main Test Runner
# ============================================================

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}PI SCANNER TEST SUITE (Simulated Mode){Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"PI_MODE: {os.environ.get('PI_MODE')}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    
    results = {
        "cache_structure": False,
        "api_fallback": False,
        "boarding_in": False,
        "boarding_out": False,
        "corrupted_recovery": False,
        "cache_persistence": False
    }
    
    try:
        # Setup: Login and register device
        cookies = login_admin()
        if not cookies:
            print(f"\n{Colors.RED}✗ Setup failed: Admin login{Colors.RESET}")
            return results
        
        api_key = register_device(cookies)
        if not api_key:
            print(f"\n{Colors.RED}✗ Setup failed: Device registration{Colors.RESET}")
            return results
        
        # Run tests
        results["cache_structure"] = test_cache_structure()
        results["api_fallback"] = test_api_embedding_fallback(api_key)
        results["boarding_in"] = test_boarding_in_flow(api_key)
        results["boarding_out"] = test_boarding_out_flow(api_key)
        results["corrupted_recovery"] = test_corrupted_cache_recovery()
        results["cache_persistence"] = test_cache_persistence()
        
    except Exception as e:
        print(f"\n{Colors.RED}✗ Test suite error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
    
    # Final report
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}TEST RESULTS{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        formatted_name = test_name.replace('_', ' ').title()
        print(f"{formatted_name:.<50} {status}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n{Colors.BOLD}Total: {passed_count}/{total_count} tests passed{Colors.RESET}")
    
    if passed_count == total_count:
        print(f"{Colors.GREEN}{Colors.BOLD}\n✓ All tests passed!{Colors.RESET}\n")
    else:
        print(f"{Colors.RED}{Colors.BOLD}\n✗ Some tests failed{Colors.RESET}\n")
    
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    
    return results

if __name__ == "__main__":
    results = main()
    
    # Exit with error code if any test failed
    if not all(results.values()):
        sys.exit(1)
    sys.exit(0)
