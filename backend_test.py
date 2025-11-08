#!/usr/bin/env python3
"""
Backend API Testing for Auto Seed Initialization & Student Form Update
Test Groups:
1. Auto-Seeding Verification
2. Bus Stops Endpoint Testing
3. Student Creation with Stop Field
4. Student Update with Stop Field
"""

import requests
import json
import sys
from typing import Dict, Optional, List

# Get backend URL from environment
BACKEND_URL = "https://bus-tracker-update.preview.emergentagent.com/api"

class TestSession:
    def __init__(self):
        self.session = requests.Session()
        self.cookies = {}
    
    def login(self, email: str, password: str) -> Dict:
        """Login and store session cookie"""
        response = self.session.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            self.cookies = response.cookies
        return response
    
    def get(self, endpoint: str) -> requests.Response:
        """GET request with session"""
        return self.session.get(f"{BACKEND_URL}{endpoint}")
    
    def put(self, endpoint: str, data: Dict) -> requests.Response:
        """PUT request with session"""
        return self.session.put(f"{BACKEND_URL}{endpoint}", json=data)
    
    def delete(self, endpoint: str) -> requests.Response:
        """DELETE request with session"""
        return self.session.delete(f"{BACKEND_URL}{endpoint}")
    
    def post(self, endpoint: str, data: Dict) -> requests.Response:
        """POST request with session"""
        return self.session.post(f"{BACKEND_URL}{endpoint}", json=data)

def print_test_header(test_name: str):
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")

def print_result(passed: bool, message: str):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {message}")

def test_scenario_a_auto_seeding():
    """SCENARIO A: Auto-Seeding Verification"""
    print_test_header("SCENARIO A: AUTO-SEEDING VERIFICATION")
    
    results = []
    
    # Test A.1: Check backend logs for seeding messages
    print("\n[Test A.1] Check backend logs for auto-seeding messages")
    try:
        import subprocess
        log_output = subprocess.check_output(
            "tail -n 100 /var/log/supervisor/backend.out.log | grep -i 'seed'",
            shell=True,
            text=True
        )
        
        if "Auto-seeding completed successfully" in log_output or "Database already populated" in log_output:
            print_result(True, "Auto-seeding logs found in backend output")
            print(f"Log excerpt:\n{log_output[:500]}")
            results.append(("Test A.1 - Auto-seeding logs present", True))
        else:
            print_result(False, "Auto-seeding logs not found")
            results.append(("Test A.1 - Auto-seeding logs present", False))
    except Exception as e:
        print_result(False, f"Failed to check logs: {str(e)}")
        results.append(("Test A.1 - Auto-seeding logs present", False))
    
    return results

def test_group_2_regular_admin_restrictions():
    """Test Group 2: Regular Admin Restrictions"""
    print_test_header("GROUP 2: REGULAR ADMIN RESTRICTIONS")
    
    session = TestSession()
    results = []
    
    # Test 2.1: Login as regular admin
    print("\n[Test 2.1] Login as regular admin (admin2@school.com)")
    response = session.login("admin2@school.com", "password")
    
    if response.status_code == 200:
        data = response.json()
        has_field = "is_elevated_admin" in data
        is_false = data.get("is_elevated_admin") == False
        
        if has_field and is_false:
            print_result(True, f"Login successful. is_elevated_admin: {data.get('is_elevated_admin')}")
            results.append(("Test 2.1 - Login response has is_elevated_admin=false", True))
        else:
            print_result(False, f"Login response missing or incorrect is_elevated_admin field. Got: {data.get('is_elevated_admin')}")
            results.append(("Test 2.1 - Login response has is_elevated_admin=false", False))
    else:
        print_result(False, f"Login failed with status {response.status_code}")
        results.append(("Test 2.1 - Login response has is_elevated_admin=false", False))
        return results
    
    # Test 2.2: Get elevated admin (admin@school.com) user_id
    print("\n[Test 2.2] Get admin@school.com user_id for restriction tests")
    response = session.get("/users")
    
    admin1_user_id = None
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get("email") == "admin@school.com":
                admin1_user_id = user.get("user_id")
                print(f"Found admin1 user_id: {admin1_user_id}")
                break
    
    if not admin1_user_id:
        print_result(False, "Could not find admin@school.com user")
        results.append(("Test 2.2 - Edit elevated admin blocked with 403", False))
        results.append(("Test 2.3 - Delete elevated admin blocked with 403", False))
        return results
    
    # Test 2.3: Try to edit elevated admin as regular admin (should fail)
    print("\n[Test 2.3] PUT /api/users/{admin1_user_id} - Try to edit elevated admin as regular admin")
    response = session.put(f"/users/{admin1_user_id}", {"name": "James Anderson Updated"})
    
    if response.status_code == 403:
        error_msg = response.json().get("detail", "")
        expected_msg = "Only elevated admins can edit other admins"
        
        if expected_msg in error_msg:
            print_result(True, f"Correctly blocked with 403. Error: {error_msg}")
            results.append(("Test 2.2 - Edit elevated admin blocked with 403 and correct error", True))
        else:
            print_result(False, f"Blocked with 403 but wrong error message. Got: {error_msg}, Expected: {expected_msg}")
            results.append(("Test 2.2 - Edit elevated admin blocked with 403 and correct error", False))
    else:
        print_result(False, f"Should have been blocked with 403. Got status: {response.status_code}")
        results.append(("Test 2.2 - Edit elevated admin blocked with 403 and correct error", False))
    
    # Test 2.4: Try to delete elevated admin as regular admin (should fail)
    print("\n[Test 2.4] DELETE /api/users/{admin1_user_id} - Try to delete elevated admin as regular admin")
    response = session.delete(f"/users/{admin1_user_id}")
    
    if response.status_code == 403:
        error_msg = response.json().get("detail", "")
        expected_msg = "Only elevated admins can delete other admins"
        
        if expected_msg in error_msg:
            print_result(True, f"Correctly blocked with 403. Error: {error_msg}")
            results.append(("Test 2.3 - Delete elevated admin blocked with 403 and correct error", True))
        else:
            print_result(False, f"Blocked with 403 but wrong error message. Got: {error_msg}, Expected: {expected_msg}")
            results.append(("Test 2.3 - Delete elevated admin blocked with 403 and correct error", False))
    else:
        print_result(False, f"Should have been blocked with 403. Got status: {response.status_code}")
        results.append(("Test 2.3 - Delete elevated admin blocked with 403 and correct error", False))
    
    return results

def test_group_3_roll_number_data():
    """Test Group 3: Roll Number Data"""
    print_test_header("GROUP 3: ROLL NUMBER DATA")
    
    session = TestSession()
    results = []
    
    # Test 3.1: Login as teacher
    print("\n[Test 3.1] Login as teacher (teacher@school.com)")
    response = session.login("teacher@school.com", "password")
    
    if response.status_code != 200:
        print_result(False, f"Login failed with status {response.status_code}")
        results.append(("Test 3.1 - Teacher login", False))
        return results
    
    print_result(True, "Teacher login successful")
    results.append(("Test 3.1 - Teacher login", True))
    
    # Test 3.2: GET /api/teacher/students and verify roll_number field
    print("\n[Test 3.2] GET /api/teacher/students - Verify roll_number field present")
    response = session.get("/teacher/students")
    
    if response.status_code == 200:
        students = response.json()
        
        if len(students) == 0:
            print_result(False, "No students returned for teacher")
            results.append(("Test 3.2 - Roll number field present in teacher students", False))
            return results
        
        print(f"Found {len(students)} students")
        
        # Check if all students have roll_number field
        all_have_roll_number = True
        sample_roll_numbers = []
        
        for student in students[:5]:  # Check first 5 students
            student_name = student.get("name", "Unknown")
            roll_number = student.get("roll_number")
            
            if roll_number:
                sample_roll_numbers.append(f"{student_name}: {roll_number}")
            else:
                all_have_roll_number = False
                print(f"  ❌ Student {student_name} missing roll_number field")
        
        if all_have_roll_number and len(sample_roll_numbers) > 0:
            print_result(True, f"All students have roll_number field")
            print("\nSample roll numbers:")
            for sample in sample_roll_numbers:
                print(f"  - {sample}")
            results.append(("Test 3.2 - Roll number field present in teacher students", True))
        else:
            print_result(False, "Some students missing roll_number field")
            results.append(("Test 3.2 - Roll number field present in teacher students", False))
    else:
        print_result(False, f"GET /api/teacher/students failed with status {response.status_code}")
        results.append(("Test 3.2 - Roll number field present in teacher students", False))
    
    return results

def main():
    print("\n" + "="*80)
    print("BACKEND API TESTING - ELEVATED ADMIN PERMISSIONS & ROLL NUMBER DISPLAY")
    print("="*80)
    
    all_results = []
    
    # Run all test groups
    all_results.extend(test_group_1_elevated_admin_permissions())
    all_results.extend(test_group_2_regular_admin_restrictions())
    all_results.extend(test_group_3_roll_number_data())
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in all_results if result)
    total = len(all_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%\n")
    
    print("Detailed Results:")
    for test_name, result in all_results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
