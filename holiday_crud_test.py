#!/usr/bin/env python3
"""
Holiday CRUD API Comprehensive Testing for Bus Tracker Application
Test Scenarios:
A. Holiday Model & CRUD Operations
   1. CREATE Holiday (POST /api/admin/holidays) - with and without description
   2. READ Holidays (GET /api/admin/holidays) - verify description field, admin-only access
   3. UPDATE Holiday (PUT /api/admin/holidays/{holiday_id}) - NEW ENDPOINT
   4. DELETE Holiday (DELETE /api/admin/holidays/{holiday_id})
B. Integration with Attendance
   5. Holiday Date Reflection in Attendance - verify blue status
"""

import requests
import json
import sys
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Backend URL
BACKEND_URL = "https://bus-tracker-update.preview.emergentagent.com/api"

class TestSession:
    def __init__(self):
        self.session = requests.Session()
        self.cookies = {}
    
    def login(self, email: str, password: str) -> requests.Response:
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
    
    def post(self, endpoint: str, data: Dict) -> requests.Response:
        """POST request with session"""
        return self.session.post(f"{BACKEND_URL}{endpoint}", json=data)
    
    def put(self, endpoint: str, data: Dict) -> requests.Response:
        """PUT request with session"""
        return self.session.put(f"{BACKEND_URL}{endpoint}", json=data)
    
    def delete(self, endpoint: str) -> requests.Response:
        """DELETE request with session"""
        return self.session.delete(f"{BACKEND_URL}{endpoint}")

def print_test_header(test_name: str):
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")

def print_result(passed: bool, message: str):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {message}")

def print_section(section_name: str):
    print(f"\n{'─'*80}")
    print(f"SECTION: {section_name}")
    print(f"{'─'*80}")

# Global variables to store created holiday IDs for cleanup
created_holiday_ids = []

def test_scenario_a_holiday_crud():
    """Test Scenario A: Holiday Model & CRUD Operations"""
    print_test_header("SCENARIO A: HOLIDAY MODEL & CRUD OPERATIONS")
    
    results = []
    admin_session = TestSession()
    teacher_session = TestSession()
    
    # Login as admin
    print_section("A.0: Admin Authentication")
    print("\n[Test A.0.1] Login as admin@school.com")
    response = admin_session.login("admin@school.com", "password")
    
    if response.status_code == 200:
        print_result(True, f"Admin login successful. User: {response.json().get('name')}")
        results.append(("A.0.1 - Admin login", True))
    else:
        print_result(False, f"Admin login failed with status {response.status_code}")
        results.append(("A.0.1 - Admin login", False))
        return results
    
    # Login as teacher (non-admin) for 403 tests
    print("\n[Test A.0.2] Login as teacher@school.com (non-admin)")
    response = teacher_session.login("teacher@school.com", "password")
    
    if response.status_code == 200:
        print_result(True, f"Teacher login successful. User: {response.json().get('name')}")
        results.append(("A.0.2 - Teacher login", True))
    else:
        print_result(False, f"Teacher login failed with status {response.status_code}")
        results.append(("A.0.2 - Teacher login", False))
    
    # Test A.1: CREATE Holiday WITH description
    print_section("A.1: CREATE Holiday WITH Description")
    print("\n[Test A.1.1] POST /api/admin/holidays - Create holiday WITH description")
    
    holiday_with_desc = {
        "name": "Test Holiday 1",
        "date": "2025-12-25",
        "description": "Christmas celebration"
    }
    
    response = admin_session.post("/admin/holidays", holiday_with_desc)
    
    if response.status_code == 200:
        data = response.json()
        holiday_id_1 = data.get("holiday_id")
        created_holiday_ids.append(holiday_id_1)
        
        # Verify all fields
        has_id = "holiday_id" in data
        has_name = data.get("name") == "Test Holiday 1"
        has_date = data.get("date") == "2025-12-25"
        has_desc = data.get("description") == "Christmas celebration"
        
        if has_id and has_name and has_date and has_desc:
            print_result(True, f"Holiday created successfully with description")
            print(f"  Holiday ID: {holiday_id_1}")
            print(f"  Name: {data.get('name')}")
            print(f"  Date: {data.get('date')}")
            print(f"  Description: {data.get('description')}")
            results.append(("A.1.1 - Create holiday WITH description", True))
        else:
            print_result(False, f"Holiday created but missing fields. Response: {data}")
            results.append(("A.1.1 - Create holiday WITH description", False))
    else:
        print_result(False, f"Failed to create holiday. Status: {response.status_code}, Response: {response.text}")
        results.append(("A.1.1 - Create holiday WITH description", False))
    
    # Test A.2: CREATE Holiday WITHOUT description
    print_section("A.2: CREATE Holiday WITHOUT Description")
    print("\n[Test A.2.1] POST /api/admin/holidays - Create holiday WITHOUT description")
    
    holiday_without_desc = {
        "name": "Test Holiday 2",
        "date": "2025-07-04",
        "description": ""
    }
    
    response = admin_session.post("/admin/holidays", holiday_without_desc)
    
    if response.status_code == 200:
        data = response.json()
        holiday_id_2 = data.get("holiday_id")
        created_holiday_ids.append(holiday_id_2)
        
        # Verify all fields
        has_id = "holiday_id" in data
        has_name = data.get("name") == "Test Holiday 2"
        has_date = data.get("date") == "2025-07-04"
        has_desc_field = "description" in data
        desc_is_empty = data.get("description") == ""
        
        if has_id and has_name and has_date and has_desc_field and desc_is_empty:
            print_result(True, f"Holiday created successfully without description")
            print(f"  Holiday ID: {holiday_id_2}")
            print(f"  Name: {data.get('name')}")
            print(f"  Date: {data.get('date')}")
            print(f"  Description: '{data.get('description')}' (empty string)")
            results.append(("A.2.1 - Create holiday WITHOUT description", True))
        else:
            print_result(False, f"Holiday created but fields incorrect. Response: {data}")
            results.append(("A.2.1 - Create holiday WITHOUT description", False))
    else:
        print_result(False, f"Failed to create holiday. Status: {response.status_code}, Response: {response.text}")
        results.append(("A.2.1 - Create holiday WITHOUT description", False))
    
    # Test A.3: READ Holidays
    print_section("A.3: READ Holidays (GET /api/admin/holidays)")
    
    # Test A.3.1: Admin can read holidays
    print("\n[Test A.3.1] GET /api/admin/holidays - Admin access")
    response = admin_session.get("/admin/holidays")
    
    if response.status_code == 200:
        holidays = response.json()
        
        # Find our created holidays
        test_holiday_1 = next((h for h in holidays if h.get("name") == "Test Holiday 1"), None)
        test_holiday_2 = next((h for h in holidays if h.get("name") == "Test Holiday 2"), None)
        
        if test_holiday_1 and test_holiday_2:
            # Verify description field exists
            has_desc_1 = "description" in test_holiday_1
            has_desc_2 = "description" in test_holiday_2
            
            if has_desc_1 and has_desc_2:
                print_result(True, f"Both holidays found with description field")
                print(f"  Test Holiday 1: description='{test_holiday_1.get('description')}'")
                print(f"  Test Holiday 2: description='{test_holiday_2.get('description')}'")
                results.append(("A.3.1 - GET holidays returns description field", True))
            else:
                print_result(False, f"Holidays found but missing description field")
                results.append(("A.3.1 - GET holidays returns description field", False))
        else:
            print_result(False, f"Created holidays not found in response. Found {len(holidays)} holidays")
            results.append(("A.3.1 - GET holidays returns description field", False))
    else:
        print_result(False, f"Failed to get holidays. Status: {response.status_code}")
        results.append(("A.3.1 - GET holidays returns description field", False))
    
    # Test A.3.2: Non-admin cannot read holidays (403)
    print("\n[Test A.3.2] GET /api/admin/holidays - Non-admin access (expect 403)")
    response = teacher_session.get("/admin/holidays")
    
    if response.status_code == 403:
        print_result(True, f"Non-admin correctly blocked with 403. Error: {response.json().get('detail')}")
        results.append(("A.3.2 - Non-admin blocked from GET holidays (403)", True))
    else:
        print_result(False, f"Expected 403, got {response.status_code}")
        results.append(("A.3.2 - Non-admin blocked from GET holidays (403)", False))
    
    # Test A.4: UPDATE Holiday (NEW ENDPOINT)
    print_section("A.4: UPDATE Holiday (PUT /api/admin/holidays/{holiday_id}) ⭐ NEW ENDPOINT")
    
    if len(created_holiday_ids) < 2:
        print_result(False, "Cannot test UPDATE - holidays not created")
        results.append(("A.4.1 - Update Test Holiday 1", False))
        results.append(("A.4.2 - Update Test Holiday 2", False))
        results.append(("A.4.3 - Update non-existent holiday (404)", False))
        results.append(("A.4.4 - Non-admin blocked from UPDATE (403)", False))
    else:
        # Test A.4.1: Update Test Holiday 1
        print("\n[Test A.4.1] PUT /api/admin/holidays/{holiday_id} - Update Test Holiday 1")
        
        update_data_1 = {
            "name": "Christmas Day",
            "date": "2025-12-25",
            "description": "National holiday"
        }
        
        response = admin_session.put(f"/admin/holidays/{created_holiday_ids[0]}", update_data_1)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify updates
            name_updated = data.get("name") == "Christmas Day"
            date_correct = data.get("date") == "2025-12-25"
            desc_updated = data.get("description") == "National holiday"
            
            if name_updated and date_correct and desc_updated:
                print_result(True, f"Holiday updated successfully")
                print(f"  Name: {data.get('name')}")
                print(f"  Date: {data.get('date')}")
                print(f"  Description: {data.get('description')}")
                results.append(("A.4.1 - Update Test Holiday 1 (name, date, description)", True))
            else:
                print_result(False, f"Holiday updated but fields incorrect. Response: {data}")
                results.append(("A.4.1 - Update Test Holiday 1 (name, date, description)", False))
        else:
            print_result(False, f"Failed to update holiday. Status: {response.status_code}, Response: {response.text}")
            results.append(("A.4.1 - Update Test Holiday 1 (name, date, description)", False))
        
        # Test A.4.2: Update Test Holiday 2 (add description)
        print("\n[Test A.4.2] PUT /api/admin/holidays/{holiday_id} - Update Test Holiday 2 (add description)")
        
        update_data_2 = {
            "name": "Test Holiday 2",
            "date": "2025-07-04",
            "description": "Independence Day celebration"
        }
        
        response = admin_session.put(f"/admin/holidays/{created_holiday_ids[1]}", update_data_2)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify description added
            desc_added = data.get("description") == "Independence Day celebration"
            
            if desc_added:
                print_result(True, f"Description added successfully")
                print(f"  Name: {data.get('name')}")
                print(f"  Date: {data.get('date')}")
                print(f"  Description: {data.get('description')}")
                results.append(("A.4.2 - Update Test Holiday 2 (add description)", True))
            else:
                print_result(False, f"Description not added correctly. Response: {data}")
                results.append(("A.4.2 - Update Test Holiday 2 (add description)", False))
        else:
            print_result(False, f"Failed to update holiday. Status: {response.status_code}, Response: {response.text}")
            results.append(("A.4.2 - Update Test Holiday 2 (add description)", False))
        
        # Test A.4.3: Update non-existent holiday (404)
        print("\n[Test A.4.3] PUT /api/admin/holidays/{non_existent_id} - Expect 404")
        
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {
            "name": "Fake Holiday",
            "date": "2025-01-01",
            "description": "This should fail"
        }
        
        response = admin_session.put(f"/admin/holidays/{fake_id}", update_data)
        
        if response.status_code == 404:
            print_result(True, f"Non-existent holiday correctly returns 404. Error: {response.json().get('detail')}")
            results.append(("A.4.3 - Update non-existent holiday returns 404", True))
        else:
            print_result(False, f"Expected 404, got {response.status_code}")
            results.append(("A.4.3 - Update non-existent holiday returns 404", False))
        
        # Test A.4.4: Non-admin cannot update holiday (403)
        print("\n[Test A.4.4] PUT /api/admin/holidays/{holiday_id} - Non-admin access (expect 403)")
        
        response = teacher_session.put(f"/admin/holidays/{created_holiday_ids[0]}", update_data_1)
        
        if response.status_code == 403:
            print_result(True, f"Non-admin correctly blocked with 403. Error: {response.json().get('detail')}")
            results.append(("A.4.4 - Non-admin blocked from UPDATE (403)", True))
        else:
            print_result(False, f"Expected 403, got {response.status_code}")
            results.append(("A.4.4 - Non-admin blocked from UPDATE (403)", False))
    
    # Test A.5: DELETE Holiday
    print_section("A.5: DELETE Holiday (DELETE /api/admin/holidays/{holiday_id})")
    
    if len(created_holiday_ids) < 1:
        print_result(False, "Cannot test DELETE - holidays not created")
        results.append(("A.5.1 - Delete Test Holiday 1", False))
        results.append(("A.5.2 - Verify deletion", False))
        results.append(("A.5.3 - Non-admin blocked from DELETE (403)", False))
    else:
        # Test A.5.1: Delete Test Holiday 1
        print("\n[Test A.5.1] DELETE /api/admin/holidays/{holiday_id} - Delete Test Holiday 1")
        
        response = admin_session.delete(f"/admin/holidays/{created_holiday_ids[0]}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "deleted":
                print_result(True, f"Holiday deleted successfully. Response: {data}")
                results.append(("A.5.1 - Delete Test Holiday 1", True))
            else:
                print_result(False, f"Unexpected response. Got: {data}")
                results.append(("A.5.1 - Delete Test Holiday 1", False))
        else:
            print_result(False, f"Failed to delete holiday. Status: {response.status_code}, Response: {response.text}")
            results.append(("A.5.1 - Delete Test Holiday 1", False))
        
        # Test A.5.2: Verify deletion - GET should not return deleted holiday
        print("\n[Test A.5.2] GET /api/admin/holidays - Verify deleted holiday not returned")
        
        response = admin_session.get("/admin/holidays")
        
        if response.status_code == 200:
            holidays = response.json()
            deleted_holiday = next((h for h in holidays if h.get("holiday_id") == created_holiday_ids[0]), None)
            
            if deleted_holiday is None:
                print_result(True, f"Deleted holiday not found in GET response (correct)")
                results.append(("A.5.2 - Deleted holiday not in GET response", True))
            else:
                print_result(False, f"Deleted holiday still appears in GET response")
                results.append(("A.5.2 - Deleted holiday not in GET response", False))
        else:
            print_result(False, f"Failed to get holidays. Status: {response.status_code}")
            results.append(("A.5.2 - Deleted holiday not in GET response", False))
        
        # Test A.5.3: Non-admin cannot delete holiday (403)
        print("\n[Test A.5.3] DELETE /api/admin/holidays/{holiday_id} - Non-admin access (expect 403)")
        
        if len(created_holiday_ids) >= 2:
            response = teacher_session.delete(f"/admin/holidays/{created_holiday_ids[1]}")
            
            if response.status_code == 403:
                print_result(True, f"Non-admin correctly blocked with 403. Error: {response.json().get('detail')}")
                results.append(("A.5.3 - Non-admin blocked from DELETE (403)", True))
            else:
                print_result(False, f"Expected 403, got {response.status_code}")
                results.append(("A.5.3 - Non-admin blocked from DELETE (403)", False))
        else:
            print_result(False, "No holiday available for non-admin DELETE test")
            results.append(("A.5.3 - Non-admin blocked from DELETE (403)", False))
    
    return results

def test_scenario_b_attendance_integration():
    """Test Scenario B: Integration with Attendance"""
    print_test_header("SCENARIO B: INTEGRATION WITH ATTENDANCE")
    
    results = []
    admin_session = TestSession()
    
    # Login as admin
    print_section("B.0: Admin Authentication")
    print("\n[Test B.0.1] Login as admin@school.com")
    response = admin_session.login("admin@school.com", "password")
    
    if response.status_code != 200:
        print_result(False, f"Admin login failed with status {response.status_code}")
        results.append(("B.0.1 - Admin login", False))
        return results
    
    print_result(True, f"Admin login successful")
    results.append(("B.0.1 - Admin login", True))
    
    # Test B.1: Create holiday for today's date
    print_section("B.1: Create Holiday for Today's Date")
    
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n[Test B.1.1] POST /api/admin/holidays - Create holiday for today ({today})")
    
    today_holiday = {
        "name": "Test Today Holiday",
        "date": today,
        "description": "Testing attendance integration"
    }
    
    response = admin_session.post("/admin/holidays", today_holiday)
    
    today_holiday_id = None
    if response.status_code == 200:
        data = response.json()
        today_holiday_id = data.get("holiday_id")
        created_holiday_ids.append(today_holiday_id)
        
        print_result(True, f"Holiday created for today")
        print(f"  Holiday ID: {today_holiday_id}")
        print(f"  Date: {data.get('date')}")
        results.append(("B.1.1 - Create holiday for today", True))
    else:
        print_result(False, f"Failed to create holiday. Status: {response.status_code}, Response: {response.text}")
        results.append(("B.1.1 - Create holiday for today", False))
        return results
    
    # Test B.2: Get a valid student_id
    print_section("B.2: Get Valid Student ID")
    print("\n[Test B.2.1] GET /api/students - Get first student")
    
    response = admin_session.get("/students")
    
    student_id = None
    if response.status_code == 200:
        students = response.json()
        
        if len(students) > 0:
            student_id = students[0].get("student_id")
            student_name = students[0].get("name")
            print_result(True, f"Found student: {student_name} (ID: {student_id})")
            results.append(("B.2.1 - Get valid student_id", True))
        else:
            print_result(False, "No students found in database")
            results.append(("B.2.1 - Get valid student_id", False))
            return results
    else:
        print_result(False, f"Failed to get students. Status: {response.status_code}")
        results.append(("B.2.1 - Get valid student_id", False))
        return results
    
    # Test B.3: Call GET /api/get_attendance for current month
    print_section("B.3: Verify Holiday Shows Blue Status in Attendance")
    
    current_month = datetime.now().strftime("%Y-%m")
    print(f"\n[Test B.3.1] GET /api/get_attendance?student_id={student_id}&month={current_month}")
    
    response = admin_session.get(f"/get_attendance?student_id={student_id}&month={current_month}")
    
    if response.status_code == 200:
        data = response.json()
        grid = data.get("grid", [])
        
        # Find today's entry in the grid
        today_day = int(datetime.now().strftime("%d"))
        today_entry = next((entry for entry in grid if entry.get("day") == today_day), None)
        
        if today_entry:
            am_status = today_entry.get("am_status")
            pm_status = today_entry.get("pm_status")
            
            if am_status == "blue" and pm_status == "blue":
                print_result(True, f"Holiday date shows blue status in attendance")
                print(f"  Date: {today_entry.get('date')}")
                print(f"  AM Status: {am_status}")
                print(f"  PM Status: {pm_status}")
                results.append(("B.3.1 - Holiday date shows blue status (am_status: blue, pm_status: blue)", True))
            else:
                print_result(False, f"Holiday date does not show blue status. AM: {am_status}, PM: {pm_status}")
                results.append(("B.3.1 - Holiday date shows blue status (am_status: blue, pm_status: blue)", False))
        else:
            print_result(False, f"Today's entry not found in attendance grid")
            results.append(("B.3.1 - Holiday date shows blue status (am_status: blue, pm_status: blue)", False))
    else:
        print_result(False, f"Failed to get attendance. Status: {response.status_code}, Response: {response.text}")
        results.append(("B.3.1 - Holiday date shows blue status (am_status: blue, pm_status: blue)", False))
    
    return results

def cleanup_test_holidays():
    """Cleanup: Delete all test holidays created during testing"""
    print_section("CLEANUP: Delete Test Holidays")
    
    admin_session = TestSession()
    admin_session.login("admin@school.com", "password")
    
    for holiday_id in created_holiday_ids:
        print(f"Deleting holiday: {holiday_id}")
        response = admin_session.delete(f"/admin/holidays/{holiday_id}")
        if response.status_code == 200:
            print(f"  ✅ Deleted successfully")
        else:
            print(f"  ⚠️  Failed to delete (may already be deleted)")

def main():
    print("\n" + "="*80)
    print("HOLIDAY CRUD API COMPREHENSIVE TESTING - BUS TRACKER APPLICATION")
    print("="*80)
    print("\nTest Credentials:")
    print("  Admin: admin@school.com / password")
    print("  Non-admin: teacher@school.com / password")
    print("\nAPI Base URL:", BACKEND_URL)
    
    all_results = []
    
    try:
        # Run Scenario A: Holiday CRUD Operations
        all_results.extend(test_scenario_a_holiday_crud())
        
        # Run Scenario B: Attendance Integration
        all_results.extend(test_scenario_b_attendance_integration())
        
    finally:
        # Cleanup test holidays
        cleanup_test_holidays()
    
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
    
    # Group results by scenario
    scenario_a_results = [(name, result) for name, result in all_results if name.startswith("A.")]
    scenario_b_results = [(name, result) for name, result in all_results if name.startswith("B.")]
    
    print("\n📋 SCENARIO A: HOLIDAY MODEL & CRUD OPERATIONS")
    print("─" * 80)
    for test_name, result in scenario_a_results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print("\n📋 SCENARIO B: INTEGRATION WITH ATTENDANCE")
    print("─" * 80)
    for test_name, result in scenario_b_results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
