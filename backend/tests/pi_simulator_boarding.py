#!/usr/bin/env python3
"""
Pi Simulator for Boarding - Face Recognition & Attendance Testing

This simulator:
1. Loads students from JSON file
2. Uses their actual profile photos from backend/photos/students/<student_id>/profile.jpg
3. Generates embeddings using DeepFace (Facenet model)
4. Compares with backend embeddings using cosine similarity
5. Sends scan events with photos to the backend
6. Saves photos to attendance folders
"""

import os
import sys
import json
import base64
import requests
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

# ============================================================
# CONFIGURATION
# ============================================================
from simulator_config import BASE_URL, DEVICE_API_KEY, BUS_ID

# Student data file
STUDENTS_JSON_FILE = Path(__file__).parent / "students_boarding.json"

# Photo directories
PHOTO_BASE_DIR = Path(__file__).parent.parent / "photos" / "students"

# Placeholder photo source
PLACEHOLDER_PHOTO_URL = "https://thispersondoesnotexist.com"

# GPS coordinates for the bus
TEST_GPS = {
    "lat": 37.7749,
    "lon": -122.4194
}

# Similarity threshold for verification
SIMILARITY_THRESHOLD = 0.6  # Cosine similarity threshold

# ============================================================
# COLOR CODES
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
# DEEPFACE SETUP
# ============================================================

def check_and_install_deepface():
    """Check if DeepFace is installed, install if not"""
    try:
        import deepface
        print(f"{Colors.GREEN}✓ DeepFace is already installed{Colors.RESET}")
        return True
    except ImportError:
        print(f"{Colors.YELLOW}⚠ DeepFace not found. Installing...{Colors.RESET}")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", 
                                 "deepface", "tf-keras", "tensorflow"])
            print(f"{Colors.GREEN}✓ DeepFace installed successfully{Colors.RESET}")
            return True
        except Exception as e:
            print(f"{Colors.RED}✗ Failed to install DeepFace: {e}{Colors.RESET}")
            return False

def generate_embedding(image_path: str) -> Optional[np.ndarray]:
    """Generate face embedding using DeepFace Facenet model"""
    try:
        from deepface import DeepFace
        
        # Generate embedding using Facenet model
        embedding_objs = DeepFace.represent(
            img_path=str(image_path),
            model_name='Facenet',
            enforce_detection=False  # Don't fail if face not detected
        )
        
        if embedding_objs and len(embedding_objs) > 0:
            # Get first face embedding
            embedding = embedding_objs[0]['embedding']
            return np.array(embedding)
        else:
            return None
            
    except Exception as e:
        print(f"{Colors.RED}   Error generating embedding: {e}{Colors.RESET}")
        return None

def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Calculate cosine similarity between two embeddings"""
    try:
        # Normalize embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)
        
    except Exception as e:
        print(f"{Colors.RED}   Error calculating similarity: {e}{Colors.RESET}")
        return 0.0

# ============================================================
# PHOTO MANAGEMENT
# ============================================================

def get_student_photo_path(student_id: str) -> Path:
    """Get the path to student's profile photo"""
    student_dir = PHOTO_BASE_DIR / student_id
    
    # Check for different image formats
    for ext in ['.jpg', '.jpeg', '.png']:
        photo_path = student_dir / f"profile{ext}"
        if photo_path.exists():
            return photo_path
    
    return student_dir / "profile.jpg"  # Default

def download_placeholder_photo(student_id: str) -> Optional[Path]:
    """Download placeholder photo from thispersondoesnotexist.com"""
    try:
        print(f"{Colors.YELLOW}   Downloading placeholder photo...{Colors.RESET}")
        
        response = requests.get(PLACEHOLDER_PHOTO_URL, timeout=10)
        response.raise_for_status()
        
        # Ensure student directory exists
        student_dir = PHOTO_BASE_DIR / student_id
        student_dir.mkdir(parents=True, exist_ok=True)
        
        # Save photo
        photo_path = student_dir / "profile.jpg"
        with open(photo_path, 'wb') as f:
            f.write(response.content)
        
        print(f"{Colors.GREEN}   ✓ Placeholder photo saved{Colors.RESET}")
        return photo_path
        
    except Exception as e:
        print(f"{Colors.RED}   ✗ Failed to download placeholder: {e}{Colors.RESET}")
        return None

def ensure_photo_exists(student_id: str) -> Optional[Path]:
    """Ensure student has a profile photo, download if needed"""
    photo_path = get_student_photo_path(student_id)
    
    if photo_path.exists():
        return photo_path
    
    # Photo doesn't exist, download placeholder
    return download_placeholder_photo(student_id)

def save_attendance_photo(student_id: str, photo_path: Path, scan_type: str = "AM") -> Optional[Path]:
    """Save photo to attendance folder"""
    try:
        # Create attendance folder
        attendance_dir = PHOTO_BASE_DIR / student_id / "attendance"
        attendance_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with date and scan type
        today = datetime.now().strftime("%Y-%m-%d")
        attendance_photo_path = attendance_dir / f"{today}_{scan_type}.jpg"
        
        # Copy photo to attendance folder
        import shutil
        shutil.copy2(photo_path, attendance_photo_path)
        
        return attendance_photo_path
        
    except Exception as e:
        print(f"{Colors.RED}   Error saving attendance photo: {e}{Colors.RESET}")
        return None

def photo_to_base64(photo_path: Path) -> Optional[str]:
    """Convert photo to base64 string"""
    try:
        with open(photo_path, 'rb') as f:
            photo_bytes = f.read()
            return base64.b64encode(photo_bytes).decode('utf-8')
    except Exception as e:
        print(f"{Colors.RED}   Error converting photo to base64: {e}{Colors.RESET}")
        return None

# ============================================================
# API INTERACTIONS
# ============================================================

def get_api_headers() -> Dict[str, str]:
    """Get API headers with device key"""
    return {
        'X-API-Key': DEVICE_API_KEY,
        'Content-Type': 'application/json'
    }

def get_backend_embedding(student_id: str) -> Optional[np.ndarray]:
    """Get student embedding from backend"""
    try:
        headers = get_api_headers()
        response = requests.get(
            f"{BASE_URL}/api/students/{student_id}/embedding",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('has_embedding') and data.get('embedding'):
                # Parse embedding (could be string, list, or already array)
                embedding_data = data['embedding']
                if isinstance(embedding_data, str):
                    # If base64 encoded
                    try:
                        embedding_bytes = base64.b64decode(embedding_data)
                        return np.frombuffer(embedding_bytes, dtype=np.float32)
                    except:
                        return None
                else:
                    return np.array(embedding_data)
            else:
                return None
        else:
            print(f"{Colors.RED}   Backend embedding fetch failed: {response.status_code}{Colors.RESET}")
            return None
            
    except Exception as e:
        print(f"{Colors.RED}   Error fetching backend embedding: {e}{Colors.RESET}")
        return None

def send_scan_event(
    student_id: str,
    rfid: str,
    photo_base64: str,
    embedding_similarity: float,
    verified: bool = True,
    scan_type: str = "AM"
) -> Tuple[bool, str]:
    """Send scan event to backend"""
    try:
        # Build scan event payload
        payload = {
            "device_id": BUS_ID,  # Using BUS_ID as device_id
            "student_id": student_id,
            "tag_id": rfid,
            "verified": verified,
            "confidence": embedding_similarity,
            "scan_type": scan_type.lower(),  # "yellow" for AM boarding
            "lat": TEST_GPS["lat"],
            "lon": TEST_GPS["lon"],
            "photo_base64": photo_base64
        }
        
        headers = get_api_headers()
        response = requests.post(
            f"{BASE_URL}/api/scan_event",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, data.get('message', 'Success')
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
            
    except Exception as e:
        return False, str(e)

# ============================================================
# MAIN SIMULATION LOGIC
# ============================================================

def load_students_from_json() -> List[Dict]:
    """Load student data from JSON file"""
    try:
        if not STUDENTS_JSON_FILE.exists():
            print(f"{Colors.RED}✗ Student JSON file not found: {STUDENTS_JSON_FILE}{Colors.RESET}")
            print(f"{Colors.YELLOW}  Creating sample file...{Colors.RESET}")
            create_sample_students_json()
        
        with open(STUDENTS_JSON_FILE, 'r') as f:
            students = json.load(f)
        
        print(f"{Colors.GREEN}✓ Loaded {len(students)} students from JSON{Colors.RESET}")
        return students
        
    except Exception as e:
        print(f"{Colors.RED}✗ Error loading students: {e}{Colors.RESET}")
        return []

def create_sample_students_json():
    """Create sample students JSON from actual photo directories"""
    try:
        # Get student IDs from photo directories
        student_dirs = [d for d in PHOTO_BASE_DIR.iterdir() if d.is_dir()]
        
        students = []
        for i, student_dir in enumerate(student_dirs[:10]):  # First 10 students
            student_id = student_dir.name
            students.append({
                "student_id": student_id,
                "rfid": f"RFID-{1000 + i}",
                "class": "5",
                "section": "A",
                "name": f"Student {i+1}"
            })
        
        # Save to JSON
        with open(STUDENTS_JSON_FILE, 'w') as f:
            json.dump(students, f, indent=2)
        
        print(f"{Colors.GREEN}✓ Created sample students JSON with {len(students)} students{Colors.RESET}")
        
    except Exception as e:
        print(f"{Colors.RED}✗ Error creating sample JSON: {e}{Colors.RESET}")

def process_student(
    student: Dict,
    scan_type: str = "AM"
) -> Dict:
    """Process a single student for boarding simulation"""
    student_id = student['student_id']
    student_name = student.get('name', 'Unknown')
    rfid = student['rfid']
    
    print(f"\n{Colors.CYAN}{Colors.BOLD}Processing: {student_name} ({student_id}){Colors.RESET}")
    
    result = {
        'student_id': student_id,
        'student_name': student_name,
        'rfid': rfid,
        'similarity': 0.0,
        'verified': False,
        'upload_status': 'Failed',
        'saved_photo_path': None,
        'error': None
    }
    
    # Step 1: Ensure photo exists
    print(f"{Colors.BLUE}1. Loading profile photo...{Colors.RESET}")
    photo_path = ensure_photo_exists(student_id)
    
    if not photo_path or not photo_path.exists():
        result['error'] = 'Photo not available'
        print(f"{Colors.RED}   ✗ Photo not available{Colors.RESET}")
        return result
    
    print(f"{Colors.GREEN}   ✓ Photo loaded: {photo_path.name}{Colors.RESET}")
    
    # Step 2: Generate embedding using DeepFace
    print(f"{Colors.BLUE}2. Generating embedding with DeepFace...{Colors.RESET}")
    local_embedding = generate_embedding(photo_path)
    
    if local_embedding is None:
        result['error'] = 'Embedding generation failed'
        print(f"{Colors.RED}   ✗ Embedding generation failed{Colors.RESET}")
        return result
    
    print(f"{Colors.GREEN}   ✓ Embedding generated (shape: {local_embedding.shape}){Colors.RESET}")
    
    # Step 3: Get backend embedding
    print(f"{Colors.BLUE}3. Fetching backend embedding...{Colors.RESET}")
    backend_embedding = get_backend_embedding(student_id)
    
    if backend_embedding is not None:
        print(f"{Colors.GREEN}   ✓ Backend embedding fetched{Colors.RESET}")
        
        # Step 4: Compare embeddings
        print(f"{Colors.BLUE}4. Comparing embeddings...{Colors.RESET}")
        similarity = cosine_similarity(local_embedding, backend_embedding)
        result['similarity'] = similarity
        result['verified'] = similarity >= SIMILARITY_THRESHOLD
        
        print(f"{Colors.GREEN}   ✓ Similarity: {similarity:.4f} (Threshold: {SIMILARITY_THRESHOLD}){Colors.RESET}")
        if result['verified']:
            print(f"{Colors.GREEN}   ✓ Verification: PASSED{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}   ⚠ Verification: FAILED (below threshold){Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}   ⚠ Backend embedding not available, using local only{Colors.RESET}")
        # Use local embedding only, assume verified
        result['similarity'] = 1.0  # Assume perfect match if no backend comparison
        result['verified'] = True
    
    # Step 5: Convert photo to base64
    print(f"{Colors.BLUE}5. Converting photo to base64...{Colors.RESET}")
    photo_base64 = photo_to_base64(photo_path)
    
    if not photo_base64:
        result['error'] = 'Base64 conversion failed'
        print(f"{Colors.RED}   ✗ Base64 conversion failed{Colors.RESET}")
        return result
    
    print(f"{Colors.GREEN}   ✓ Photo converted ({len(photo_base64)} chars){Colors.RESET}")
    
    # Step 6: Send scan event
    print(f"{Colors.BLUE}6. Sending scan event to backend...{Colors.RESET}")
    success, message = send_scan_event(
        student_id=student_id,
        rfid=rfid,
        photo_base64=photo_base64,
        embedding_similarity=result['similarity'],
        verified=result['verified'],
        scan_type=scan_type
    )
    
    if success:
        result['upload_status'] = 'Success'
        print(f"{Colors.GREEN}   ✓ Scan event uploaded: {message}{Colors.RESET}")
    else:
        result['upload_status'] = 'Failed'
        result['error'] = message
        print(f"{Colors.RED}   ✗ Upload failed: {message}{Colors.RESET}")
        return result
    
    # Step 7: Save photo to attendance folder
    print(f"{Colors.BLUE}7. Saving photo to attendance folder...{Colors.RESET}")
    attendance_photo_path = save_attendance_photo(student_id, photo_path, scan_type)
    
    if attendance_photo_path:
        result['saved_photo_path'] = str(attendance_photo_path)
        print(f"{Colors.GREEN}   ✓ Photo saved: {attendance_photo_path.name}{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}   ⚠ Photo save failed{Colors.RESET}")
    
    return result

def run_boarding_simulation(scan_type: str = "AM"):
    """Run boarding simulation for all students"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}🚌 Pi Boarding Simulator - {scan_type} Boarding{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
    
    # Check DeepFace installation
    print(f"\n{Colors.YELLOW}Checking dependencies...{Colors.RESET}")
    if not check_and_install_deepface():
        print(f"{Colors.RED}✗ Cannot proceed without DeepFace{Colors.RESET}")
        return
    
    # Load students
    print(f"\n{Colors.YELLOW}Loading students...{Colors.RESET}")
    students = load_students_from_json()
    
    if not students:
        print(f"{Colors.RED}✗ No students to process{Colors.RESET}")
        return
    
    # Process each student
    results = []
    print(f"\n{Colors.YELLOW}Starting boarding simulation...{Colors.RESET}")
    
    for i, student in enumerate(students):
        print(f"\n{Colors.BOLD}[{i+1}/{len(students)}]{Colors.RESET}")
        result = process_student(student, scan_type)
        results.append(result)
        time.sleep(0.5)  # Small delay between students
    
    # Print summary
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}📊 Simulation Summary{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
    
    # Summary table header
    print(f"\n{Colors.BOLD}{'Student ID':<40} | {'Similarity':<10} | {'Verified':<8} | {'Upload':<10}{Colors.RESET}")
    print(f"{'-'*40}-+-{'-'*10}-+-{'-'*8}-+-{'-'*10}")
    
    # Summary table rows
    success_count = 0
    verified_count = 0
    
    for result in results:
        student_id_short = result['student_id'][:36]
        similarity = f"{result['similarity']:.4f}"
        verified = '✓' if result['verified'] else '✗'
        upload = result['upload_status']
        
        # Color code the row
        if result['upload_status'] == 'Success':
            color = Colors.GREEN
            success_count += 1
            if result['verified']:
                verified_count += 1
        else:
            color = Colors.RED
        
        print(f"{color}{student_id_short:<40} | {similarity:<10} | {verified:<8} | {upload:<10}{Colors.RESET}")
        
        if result['saved_photo_path']:
            print(f"   Photo: {result['saved_photo_path']}")
        if result.get('error'):
            print(f"   {Colors.RED}Error: {result['error']}{Colors.RESET}")
    
    # Statistics
    print(f"\n{Colors.BOLD}Statistics:{Colors.RESET}")
    print(f"   Total Students: {len(results)}")
    print(f"   {Colors.GREEN}Successful Uploads: {success_count}{Colors.RESET}")
    print(f"   {Colors.GREEN}Verified: {verified_count}{Colors.RESET}")
    print(f"   {Colors.YELLOW}Failed: {len(results) - success_count}{Colors.RESET}")
    print(f"   Success Rate: {(success_count / len(results) * 100):.1f}%")
    print(f"   Verification Rate: {(verified_count / len(results) * 100):.1f}%")
    
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")

# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Pi Boarding Simulator with Face Recognition')
    parser.add_argument(
        '--scan-type',
        choices=['AM', 'PM', 'yellow', 'green'],
        default='AM',
        help='Scan type: AM (morning boarding), PM (afternoon boarding), yellow (on board), green (reached)'
    )
    
    args = parser.parse_args()
    
    # Map scan types
    scan_type_map = {
        'AM': 'yellow',
        'PM': 'green',
        'yellow': 'yellow',
        'green': 'green'
    }
    
    scan_type = scan_type_map.get(args.scan_type, 'yellow')
    
    try:
        run_boarding_simulation(scan_type)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.CYAN}👋 Simulation interrupted{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}✗ Simulation error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
