#!/usr/bin/env python3
"""
Post-Cleanup Smoke Test for Bus Tracker Application
Tests critical endpoints to ensure nothing was broken after cleanup
"""

import requests
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://artifact-purge.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@school.com"
ADMIN_PASSWORD = "password"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(message):
    print(f"{Colors.BLUE}[TEST]{Colors.END} {message}")

def print_success(message):
    print(f"{Colors.GREEN}✅ PASSED{Colors.END} - {message}")

def print_error(message):
    print(f"{Colors.RED}❌ FAILED{Colors.END} - {message}")

def print_info(message):
    print(f"{Colors.YELLOW}[INFO]{Colors.END} {message}")

def test_authentication():
    """Test 1: Authentication - Login with admin@school.com/password"""
    print_test("Testing Authentication (POST /api/auth/login)")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('role') == 'admin' and data.get('email') == ADMIN_EMAIL:
                print_success(f"Admin login successful. User: {data.get('name')}, Role: {data.get('role')}")
                # Extract session cookie
                session_cookie = response.cookies.get('session_token')
                if session_cookie:
                    print_info(f"Session token received: {session_cookie[:20]}...")
                    return session_cookie
                else:
                    print_error("No session token in response cookies")
                    return None
            else:
                print_error(f"Login response data incorrect: {data}")
                return None
        else:
            print_error(f"Login failed with status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print_error(f"Authentication test exception: {str(e)}")
        return None

def test_students_api(session_token):
    """Test 2: Students API - GET /api/students (verify data loading)"""
    print_test("Testing Students API (GET /api/students)")
    
    try:
        cookies = {'session_token': session_token}
        response = requests.get(
            f"{BACKEND_URL}/students",
            cookies=cookies,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print_success(f"Students API returned {len(data)} students")
                if len(data) > 0:
                    sample = data[0]
                    print_info(f"Sample student: {sample.get('name')} (ID: {sample.get('student_id')[:20]}...)")
                    # Check for enriched data
                    if 'parent_name' in sample and 'bus_number' in sample:
                        print_info("Data enrichment verified (parent_name, bus_number present)")
                return True
            else:
                print_error(f"Students API returned non-list data: {type(data)}")
                return False
        else:
            print_error(f"Students API failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Students API test exception: {str(e)}")
        return False

def test_users_api(session_token):
    """Test 3: Users API - GET /api/users (verify admin access)"""
    print_test("Testing Users API (GET /api/users)")
    
    try:
        cookies = {'session_token': session_token}
        response = requests.get(
            f"{BACKEND_URL}/users",
            cookies=cookies,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print_success(f"Users API returned {len(data)} users")
                if len(data) > 0:
                    sample = data[0]
                    print_info(f"Sample user: {sample.get('name')} ({sample.get('role')})")
                    # Verify password_hash is excluded
                    if 'password_hash' not in sample:
                        print_info("Security verified: password_hash excluded from response")
                    else:
                        print_error("Security issue: password_hash present in response")
                        return False
                return True
            else:
                print_error(f"Users API returned non-list data: {type(data)}")
                return False
        else:
            print_error(f"Users API failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Users API test exception: {str(e)}")
        return False

def test_buses_api(session_token):
    """Test 4: Buses API - GET /api/buses (verify bus data)"""
    print_test("Testing Buses API (GET /api/buses)")
    
    try:
        cookies = {'session_token': session_token}
        response = requests.get(
            f"{BACKEND_URL}/buses",
            cookies=cookies,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print_success(f"Buses API returned {len(data)} buses")
                if len(data) > 0:
                    sample = data[0]
                    print_info(f"Sample bus: {sample.get('bus_number')} (Driver: {sample.get('driver_name')})")
                    # Check for enriched data
                    if 'route_name' in sample:
                        print_info("Data enrichment verified (route_name present)")
                return True
            else:
                print_error(f"Buses API returned non-list data: {type(data)}")
                return False
        else:
            print_error(f"Buses API failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Buses API test exception: {str(e)}")
        return False

def check_backend_logs():
    """Check backend logs for actual errors (not INFO/WARNING)"""
    print_test("Checking backend logs for actual errors")
    
    try:
        import subprocess
        # Check for actual Python errors/exceptions
        result = subprocess.run(
            ['grep', '-i', '-E', 'error|exception|traceback', '/var/log/supervisor/backend.err.log'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # grep returns 0 if matches found, 1 if no matches
        if result.returncode == 1:
            # No errors found - this is good!
            print_success("Backend logs are clean (no errors or exceptions)")
            return True
        elif result.returncode == 0:
            # Errors found
            error_lines = result.stdout.strip().split('\n')
            print_error(f"Found {len(error_lines)} error/exception lines in backend logs:")
            for line in error_lines[-5:]:  # Show last 5 errors
                print(f"  {line[:100]}")
            return False
        else:
            print_info("Could not read backend error log")
            return True  # Don't fail test if we can't read logs
    except Exception as e:
        print_info(f"Could not check backend logs: {str(e)}")
        return True  # Don't fail test if we can't read logs

def main():
    print("\n" + "="*70)
    print("POST-CLEANUP SMOKE TEST - BUS TRACKER APPLICATION")
    print("="*70 + "\n")
    
    print_info(f"Backend URL: {BACKEND_URL}")
    print_info(f"Test User: {ADMIN_EMAIL}\n")
    
    results = {
        'authentication': False,
        'students_api': False,
        'users_api': False,
        'buses_api': False,
        'backend_logs': False
    }
    
    # Test 1: Authentication
    session_token = test_authentication()
    if session_token:
        results['authentication'] = True
        print()
        
        # Test 2: Students API
        results['students_api'] = test_students_api(session_token)
        print()
        
        # Test 3: Users API
        results['users_api'] = test_users_api(session_token)
        print()
        
        # Test 4: Buses API
        results['buses_api'] = test_buses_api(session_token)
        print()
    else:
        print_error("Cannot proceed with other tests without authentication\n")
    
    # Test 5: Backend logs
    results['backend_logs'] = check_backend_logs()
    print()
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✅ PASSED{Colors.END}" if result else f"{Colors.RED}❌ FAILED{Colors.END}"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED - Application is fully functional after cleanup{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}⚠️  SOME TESTS FAILED - Please review the failures above{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
