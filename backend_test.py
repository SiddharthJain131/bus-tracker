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

def test_scenario_b_bus_stops_endpoint():
    """SCENARIO B: Bus Stops Endpoint Testing"""
    print_test_header("SCENARIO B: BUS STOPS ENDPOINT TESTING")
    
    session = TestSession()
    results = []
    
    # Login as admin
    print("\n[Setup] Login as admin")
    response = session.login("admin@school.com", "password")
    if response.status_code != 200:
        print_result(False, "Admin login failed")
        return [("Test B - Setup failed", False)]
    
    # Get list of buses
    print("\n[Setup] Get list of buses")
    response = session.get("/buses")
    if response.status_code != 200:
        print_result(False, "Failed to get buses list")
        return [("Test B - Setup failed", False)]
    
    buses = response.json()
    print(f"Found {len(buses)} buses")
    
    # Find a bus with route
    bus_with_route = None
    for bus in buses:
        if bus.get('route_id'):
            bus_with_route = bus
            break
    
    # Test B.1: Get stops for bus with route
    if bus_with_route:
        print(f"\n[Test B.1] GET /api/buses/{bus_with_route['bus_id']}/stops - Bus with route")
        print(f"  Bus: {bus_with_route.get('bus_number')}, Route ID: {bus_with_route.get('route_id')}")
        
        response = session.get(f"/buses/{bus_with_route['bus_id']}/stops")
        
        if response.status_code == 200:
            stops = response.json()
            
            if isinstance(stops, list) and len(stops) > 0:
                print_result(True, f"Returns array of {len(stops)} stops")
                
                # Verify stop structure
                first_stop = stops[0]
                required_fields = ['stop_id', 'stop_name', 'lat', 'lon', 'order_index']
                has_all_fields = all(field in first_stop for field in required_fields)
                
                if has_all_fields:
                    print(f"  Sample stop: {first_stop.get('stop_name')} (order: {first_stop.get('order_index')})")
                    
                    # Verify sorting by order_index
                    is_sorted = all(stops[i].get('order_index', 0) <= stops[i+1].get('order_index', 0) 
                                   for i in range(len(stops)-1))
                    
                    if is_sorted:
                        print_result(True, "Stops are sorted by order_index")
                        results.append(("Test B.1 - Get stops for bus with route (sorted)", True))
                    else:
                        print_result(False, "Stops are NOT sorted by order_index")
                        results.append(("Test B.1 - Get stops for bus with route (sorted)", False))
                else:
                    print_result(False, f"Stop missing required fields. Has: {list(first_stop.keys())}")
                    results.append(("Test B.1 - Get stops for bus with route (sorted)", False))
            else:
                print_result(False, f"Expected non-empty array, got: {stops}")
                results.append(("Test B.1 - Get stops for bus with route (sorted)", False))
        else:
            print_result(False, f"Request failed with status {response.status_code}")
            results.append(("Test B.1 - Get stops for bus with route (sorted)", False))
    else:
        print_result(False, "No bus with route found in database")
        results.append(("Test B.1 - Get stops for bus with route (sorted)", False))
    
    # Test B.2: Create bus without route and test
    print("\n[Test B.2] GET /api/buses/{bus_id}/stops - Bus without route")
    
    # Create test bus without route
    test_bus_data = {
        "bus_number": "TEST-999",
        "driver_name": "Test Driver",
        "driver_phone": "+1-555-9999",
        "capacity": 30,
        "route_id": None
    }
    
    response = session.post("/buses", test_bus_data)
    
    if response.status_code == 200:
        test_bus = response.json()
        test_bus_id = test_bus.get('bus_id')
        print(f"  Created test bus: {test_bus_id}")
        
        # Get stops for bus without route
        response = session.get(f"/buses/{test_bus_id}/stops")
        
        if response.status_code == 200:
            stops = response.json()
            
            if isinstance(stops, list) and len(stops) == 0:
                print_result(True, "Returns empty array [] for bus without route")
                results.append(("Test B.2 - Get stops for bus without route (empty array)", True))
            else:
                print_result(False, f"Expected empty array, got: {stops}")
                results.append(("Test B.2 - Get stops for bus without route (empty array)", False))
        else:
            print_result(False, f"Request failed with status {response.status_code}")
            results.append(("Test B.2 - Get stops for bus without route (empty array)", False))
        
        # Cleanup: Delete test bus
        session.delete(f"/buses/{test_bus_id}")
    else:
        print_result(False, f"Failed to create test bus. Status: {response.status_code}")
        results.append(("Test B.2 - Get stops for bus without route (empty array)", False))
    
    # Test B.3: Get stops for non-existent bus
    print("\n[Test B.3] GET /api/buses/invalid-bus-id-12345/stops - Non-existent bus")
    
    response = session.get("/buses/invalid-bus-id-12345/stops")
    
    if response.status_code == 404:
        error_data = response.json()
        error_msg = error_data.get('detail', '')
        
        if 'Bus not found' in error_msg:
            print_result(True, f"Returns 404 with correct error: {error_msg}")
            results.append(("Test B.3 - Get stops for non-existent bus (404 error)", True))
        else:
            print_result(False, f"Returns 404 but wrong error message: {error_msg}")
            results.append(("Test B.3 - Get stops for non-existent bus (404 error)", False))
    else:
        print_result(False, f"Expected 404, got status {response.status_code}")
        results.append(("Test B.3 - Get stops for non-existent bus (404 error)", False))
    
    return results

def test_scenario_c_student_creation_with_stop():
    """SCENARIO C: Student Creation with Stop Field"""
    print_test_header("SCENARIO C: STUDENT CREATION WITH STOP FIELD")
    
    session = TestSession()
    results = []
    
    # Login as admin
    print("\n[Setup] Login as admin")
    response = session.login("admin@school.com", "password")
    if response.status_code != 200:
        print_result(False, "Admin login failed")
        return [("Test C - Setup failed", False)]
    
    # Get parent_id
    print("\n[Setup] Get parent user")
    response = session.get("/users")
    parent_id = None
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get('role') == 'parent':
                parent_id = user.get('user_id')
                print(f"  Found parent: {user.get('email')} (ID: {parent_id})")
                break
    
    if not parent_id:
        print_result(False, "No parent found in database")
        return [("Test C - Setup failed", False)]
    
    # Get bus_id and stop_id
    print("\n[Setup] Get bus and stop")
    response = session.get("/buses")
    bus_id = None
    stop_id = None
    
    if response.status_code == 200:
        buses = response.json()
        for bus in buses:
            if bus.get('route_id'):
                bus_id = bus.get('bus_id')
                print(f"  Found bus: {bus.get('bus_number')} (ID: {bus_id})")
                
                # Get stops for this bus
                stops_response = session.get(f"/buses/{bus_id}/stops")
                if stops_response.status_code == 200:
                    stops = stops_response.json()
                    if len(stops) > 0:
                        stop_id = stops[0].get('stop_id')
                        print(f"  Found stop: {stops[0].get('stop_name')} (ID: {stop_id})")
                        break
    
    if not bus_id or not stop_id:
        print_result(False, "No bus with stops found in database")
        return [("Test C - Setup failed", False)]
    
    # Test C.1: Create student with stop_id and teacher_id=null
    print("\n[Test C.1] POST /api/students - Create student with stop_id and teacher_id=null")
    
    student_data = {
        "name": "Test Student Auto",
        "roll_number": "TEST-001",
        "class_name": "Grade 5",
        "section": "A",
        "parent_id": parent_id,
        "teacher_id": None,
        "bus_id": bus_id,
        "stop_id": stop_id,
        "phone": "+1-555-1234",
        "emergency_contact": "+1-555-5678"
    }
    
    response = session.post("/students", student_data)
    
    if response.status_code == 200:
        created_student = response.json()
        student_id = created_student.get('student_id')
        
        # Verify fields
        has_stop_id = created_student.get('stop_id') == stop_id
        teacher_is_null = created_student.get('teacher_id') is None
        
        if has_stop_id and teacher_is_null:
            print_result(True, f"Student created successfully with stop_id={stop_id} and teacher_id=null")
            print(f"  Student ID: {student_id}")
            print(f"  Name: {created_student.get('name')}")
            print(f"  Stop ID: {created_student.get('stop_id')}")
            print(f"  Teacher ID: {created_student.get('teacher_id')}")
            results.append(("Test C.1 - Create student with stop_id and teacher_id=null", True))
            
            # Cleanup: Delete test student
            session.delete(f"/students/{student_id}")
        else:
            print_result(False, f"Student created but fields incorrect. stop_id={created_student.get('stop_id')}, teacher_id={created_student.get('teacher_id')}")
            results.append(("Test C.1 - Create student with stop_id and teacher_id=null", False))
            
            # Cleanup
            if student_id:
                session.delete(f"/students/{student_id}")
    else:
        print_result(False, f"Failed to create student. Status: {response.status_code}, Response: {response.text}")
        results.append(("Test C.1 - Create student with stop_id and teacher_id=null", False))
    
    return results

def test_scenario_d_student_update_with_stop():
    """SCENARIO D: Student Update with Stop Field"""
    print_test_header("SCENARIO D: STUDENT UPDATE WITH STOP FIELD")
    
    session = TestSession()
    results = []
    
    # Login as admin
    print("\n[Setup] Login as admin")
    response = session.login("admin@school.com", "password")
    if response.status_code != 200:
        print_result(False, "Admin login failed")
        return [("Test D - Setup failed", False)]
    
    # Get an existing student
    print("\n[Setup] Get existing student")
    response = session.get("/students")
    student_id = None
    original_stop_id = None
    
    if response.status_code == 200:
        students = response.json()
        if len(students) > 0:
            student = students[0]
            student_id = student.get('student_id')
            original_stop_id = student.get('stop_id')
            print(f"  Found student: {student.get('name')} (ID: {student_id})")
            print(f"  Current stop_id: {original_stop_id}")
    
    if not student_id:
        print_result(False, "No students found in database")
        return [("Test D - Setup failed", False)]
    
    # Get a different stop_id
    print("\n[Setup] Get different stop for update")
    response = session.get("/stops")
    different_stop_id = None
    
    if response.status_code == 200:
        stops = response.json()
        for stop in stops:
            if stop.get('stop_id') != original_stop_id:
                different_stop_id = stop.get('stop_id')
                print(f"  Found different stop: {stop.get('stop_name')} (ID: {different_stop_id})")
                break
    
    if not different_stop_id:
        print_result(False, "No different stop found for update test")
        return [("Test D - Setup failed", False)]
    
    # Test D.1: Update student's stop_id
    print(f"\n[Test D.1] PUT /api/students/{student_id} - Update student's stop_id")
    
    update_data = {
        "stop_id": different_stop_id
    }
    
    response = session.put(f"/students/{student_id}", update_data)
    
    if response.status_code == 200:
        print_result(True, f"Student update successful. Status: {response.status_code}")
        
        # Verify the update by fetching student details
        verify_response = session.get(f"/students/{student_id}")
        
        if verify_response.status_code == 200:
            updated_student = verify_response.json()
            new_stop_id = updated_student.get('stop_id')
            
            if new_stop_id == different_stop_id:
                print_result(True, f"Stop ID successfully updated from {original_stop_id} to {new_stop_id}")
                results.append(("Test D.1 - Update student's stop_id", True))
            else:
                print_result(False, f"Stop ID not updated correctly. Expected: {different_stop_id}, Got: {new_stop_id}")
                results.append(("Test D.1 - Update student's stop_id", False))
        else:
            print_result(False, f"Failed to verify update. Status: {verify_response.status_code}")
            results.append(("Test D.1 - Update student's stop_id", False))
        
        # Revert the change
        if original_stop_id:
            session.put(f"/students/{student_id}", {"stop_id": original_stop_id})
    else:
        print_result(False, f"Failed to update student. Status: {response.status_code}, Response: {response.text}")
        results.append(("Test D.1 - Update student's stop_id", False))
    
    return results

def main():
    print("\n" + "="*80)
    print("BACKEND API TESTING - AUTO SEED INITIALIZATION & STUDENT FORM UPDATE")
    print("="*80)
    
    all_results = []
    
    # Run all test scenarios
    all_results.extend(test_scenario_a_auto_seeding())
    all_results.extend(test_scenario_b_bus_stops_endpoint())
    all_results.extend(test_scenario_c_student_creation_with_stop())
    all_results.extend(test_scenario_d_student_update_with_stop())
    
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
