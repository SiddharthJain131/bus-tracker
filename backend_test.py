#!/usr/bin/env python3
"""
Backend API Testing for Elevated Admin Permissions and Roll Number Display
Test Groups:
1. Elevated Admin Permissions
2. Regular Admin Restrictions  
3. Roll Number Data
"""

import requests
import json
import sys
from typing import Dict, Optional

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

def test_group_1_elevated_admin_permissions():
    """Test Group 1: Elevated Admin Permissions"""
    print_test_header("GROUP 1: ELEVATED ADMIN PERMISSIONS")
    
    session = TestSession()
    results = []
    
    # Test 1.1: Login as elevated admin
    print("\n[Test 1.1] Login as elevated admin (admin@school.com)")
    response = session.login("admin@school.com", "password")
    
    if response.status_code == 200:
        data = response.json()
        has_field = "is_elevated_admin" in data
        is_true = data.get("is_elevated_admin") == True
        
        if has_field and is_true:
            print_result(True, f"Login successful. is_elevated_admin: {data.get('is_elevated_admin')}")
            results.append(("Test 1.1 - Login response has is_elevated_admin=true", True))
        else:
            print_result(False, f"Login response missing or incorrect is_elevated_admin field. Got: {data.get('is_elevated_admin')}")
            results.append(("Test 1.1 - Login response has is_elevated_admin=true", False))
    else:
        print_result(False, f"Login failed with status {response.status_code}")
        results.append(("Test 1.1 - Login response has is_elevated_admin=true", False))
        return results
    
    # Test 1.2: Verify /api/auth/me returns is_elevated_admin
    print("\n[Test 1.2] GET /api/auth/me returns is_elevated_admin")
    response = session.get("/auth/me")
    
    if response.status_code == 200:
        data = response.json()
        has_field = "is_elevated_admin" in data
        is_true = data.get("is_elevated_admin") == True
        
        if has_field and is_true:
            print_result(True, f"GET /api/auth/me returns is_elevated_admin: {data.get('is_elevated_admin')}")
            results.append(("Test 1.2 - GET /api/auth/me returns is_elevated_admin=true", True))
        else:
            print_result(False, f"GET /api/auth/me missing or incorrect is_elevated_admin. Got: {data.get('is_elevated_admin')}")
            results.append(("Test 1.2 - GET /api/auth/me returns is_elevated_admin=true", False))
    else:
        print_result(False, f"GET /api/auth/me failed with status {response.status_code}")
        results.append(("Test 1.2 - GET /api/auth/me returns is_elevated_admin=true", False))
    
    # Test 1.3: Get admin2 user_id
    print("\n[Test 1.3] Get admin2@school.com user_id for editing test")
    response = session.get("/users")
    
    admin2_user_id = None
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get("email") == "admin2@school.com":
                admin2_user_id = user.get("user_id")
                print(f"Found admin2 user_id: {admin2_user_id}")
                break
    
    if not admin2_user_id:
        print_result(False, "Could not find admin2@school.com user")
        results.append(("Test 1.3 - Edit another admin as elevated admin", False))
        results.append(("Test 1.4 - Delete another admin as elevated admin", False))
        return results
    
    # Test 1.4: Edit another admin (admin2) as elevated admin
    print("\n[Test 1.4] PUT /api/users/{admin2_user_id} - Edit admin2 as elevated admin")
    response = session.put(f"/users/{admin2_user_id}", {"name": "Patricia Williams Updated"})
    
    if response.status_code == 200:
        print_result(True, f"Successfully edited admin2 user. Status: {response.status_code}")
        results.append(("Test 1.4 - Edit another admin as elevated admin", True))
        
        # Revert the change
        session.put(f"/users/{admin2_user_id}", {"name": "Patricia Williams"})
    else:
        print_result(False, f"Failed to edit admin2. Status: {response.status_code}, Response: {response.text}")
        results.append(("Test 1.4 - Edit another admin as elevated admin", False))
    
    # Test 1.5: Create a temporary admin for deletion test
    print("\n[Test 1.5] Create temporary admin for deletion test")
    response = session.post("/users", {
        "email": "temp_admin@school.com",
        "password": "password",
        "role": "admin",
        "name": "Temp Admin",
        "is_elevated_admin": False
    })
    
    temp_admin_id = None
    if response.status_code == 200:
        temp_admin_id = response.json().get("user_id")
        print(f"Created temp admin with user_id: {temp_admin_id}")
    else:
        print_result(False, f"Failed to create temp admin. Status: {response.status_code}")
        results.append(("Test 1.5 - Delete another admin as elevated admin", False))
        return results
    
    # Test 1.6: Delete the temporary admin as elevated admin
    print("\n[Test 1.6] DELETE /api/users/{temp_admin_id} - Delete temp admin as elevated admin")
    response = session.delete(f"/users/{temp_admin_id}")
    
    if response.status_code == 200:
        print_result(True, f"Successfully deleted temp admin. Status: {response.status_code}")
        results.append(("Test 1.5 - Delete another admin as elevated admin", True))
    else:
        print_result(False, f"Failed to delete temp admin. Status: {response.status_code}, Response: {response.text}")
        results.append(("Test 1.5 - Delete another admin as elevated admin", False))
    
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
