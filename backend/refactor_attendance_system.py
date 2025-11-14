#!/usr/bin/env python3
"""
Refactor Attendance System
===========================
This script refactors the entire attendance system to match the required structure:
1. Corrects scan_photo naming (removes _green and _yellow suffixes)
2. Generates new profile photos for all students
3. Updates folder structure to match STRUCTURE_EXAMPLE.txt
4. Ensures all field names match the required schema
"""

import json
import os
import re
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Configuration
BACKEND_DIR = Path("/app/backend")
PHOTOS_DIR = BACKEND_DIR / "photos" / "students"
ATTENDANCE_BACKUP_DIR = BACKEND_DIR / "backups" / "attendance"
SEED_BACKUP_PATH = BACKEND_DIR / "backups" / "seed_backup_20251114_0532.json"
LOG_FILE = BACKEND_DIR / "logs" / "refactor_attendance_system.log"

# Ensure logs directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log_message(message: str, level: str = "INFO"):
    """Log a message to console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] [{level}] {message}"
    print(formatted_message)
    with open(LOG_FILE, "a") as f:
        f.write(formatted_message + "\n")

def load_json_file(file_path: Path) -> Dict:
    """Load a JSON file"""
    log_message(f"Loading JSON file: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(data: Dict, file_path: Path):
    """Save data to a JSON file"""
    log_message(f"Saving JSON file: {file_path}")
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def correct_scan_photo_path(scan_photo: str) -> str:
    """
    Remove _green and _yellow suffixes from scan photo paths
    Example: 2025-11-14_AM_green.jpg -> 2025-11-14_AM.jpg
    """
    if not scan_photo:
        return scan_photo
    
    # Remove _green or _yellow suffixes
    corrected = re.sub(r'_(green|yellow)\.jpg$', '.jpg', scan_photo)
    return corrected

def refactor_attendance_backup():
    """Refactor the attendance backup file to correct photo naming"""
    log_message("=" * 80)
    log_message("STEP 1: Refactoring Attendance Backup")
    log_message("=" * 80)
    
    # Find the latest attendance backup
    attendance_backups = sorted(ATTENDANCE_BACKUP_DIR.glob("attendance_backup_*.json"))
    if not attendance_backups:
        log_message("No attendance backup found!", "ERROR")
        return
    
    latest_backup = attendance_backups[-1]
    log_message(f"Processing backup: {latest_backup.name}")
    
    # Load the backup
    data = load_json_file(latest_backup)
    
    # Process attendance records
    attendance_records = data.get("collections", {}).get("attendance", [])
    log_message(f"Found {len(attendance_records)} attendance records")
    
    corrected_count = 0
    for record in attendance_records:
        original_path = record.get("scan_photo", "")
        if original_path:
            corrected_path = correct_scan_photo_path(original_path)
            if original_path != corrected_path:
                record["scan_photo"] = corrected_path
                corrected_count += 1
                log_message(f"  Corrected: {os.path.basename(original_path)} -> {os.path.basename(corrected_path)}")
    
    log_message(f"Corrected {corrected_count} scan photo paths")
    
    # Create backup of original file
    backup_path = latest_backup.with_suffix('.json.bak')
    log_message(f"Creating backup: {backup_path.name}")
    save_json_file(data, backup_path)
    
    # Save corrected version
    save_json_file(data, latest_backup)
    log_message(f"Saved corrected backup: {latest_backup.name}")
    
    return data

def generate_student_profile_photos(students_data: List[Dict]):
    """Generate new profile photos for all students using thispersondoesnotexist.com"""
    log_message("=" * 80)
    log_message("STEP 2: Generating New Profile Photos for Students")
    log_message("=" * 80)
    
    total_students = len(students_data)
    log_message(f"Generating photos for {total_students} students")
    
    success_count = 0
    failed_count = 0
    
    for idx, student in enumerate(students_data, 1):
        student_id = student.get("student_id")
        student_name = student.get("name", "Unknown")
        
        if not student_id:
            log_message(f"  [{idx}/{total_students}] Skipping student without ID", "WARNING")
            continue
        
        # Create student photo directory
        student_dir = PHOTOS_DIR / student_id
        student_dir.mkdir(parents=True, exist_ok=True)
        
        # Create attendance subfolder
        attendance_dir = student_dir / "attendance"
        attendance_dir.mkdir(parents=True, exist_ok=True)
        
        # Define profile photo path
        profile_photo_path = student_dir / "profile.jpg"
        
        log_message(f"  [{idx}/{total_students}] {student_name} ({student_id})")
        
        try:
            # Download photo from thispersondoesnotexist.com
            log_message(f"    Downloading new photo from thispersondoesnotexist.com...")
            response = requests.get("https://thispersondoesnotexist.com", timeout=30)
            
            if response.status_code == 200:
                # Save the photo
                with open(profile_photo_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = len(response.content) / 1024  # KB
                log_message(f"    ✓ Downloaded: {file_size:.2f} KB")
                success_count += 1
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
            else:
                log_message(f"    ✗ Failed: HTTP {response.status_code}", "ERROR")
                failed_count += 1
                
        except Exception as e:
            log_message(f"    ✗ Error: {str(e)}", "ERROR")
            failed_count += 1
    
    log_message(f"\nPhoto generation complete:")
    log_message(f"  ✓ Success: {success_count}/{total_students}")
    log_message(f"  ✗ Failed: {failed_count}/{total_students}")

def clean_orphaned_student_folders(valid_student_ids: List[str]):
    """Remove student folders that are not in the backup"""
    log_message("=" * 80)
    log_message("STEP 3: Cleaning Orphaned Student Folders")
    log_message("=" * 80)
    
    # Get all student folders on disk
    disk_folders = [d.name for d in PHOTOS_DIR.iterdir() if d.is_dir()]
    log_message(f"Found {len(disk_folders)} student folders on disk")
    log_message(f"Found {len(valid_student_ids)} valid students in backup")
    
    # Find orphaned folders
    orphaned = set(disk_folders) - set(valid_student_ids)
    
    if not orphaned:
        log_message("No orphaned folders found")
        return
    
    log_message(f"Found {len(orphaned)} orphaned folders to remove:")
    
    for folder_name in sorted(orphaned):
        folder_path = PHOTOS_DIR / folder_name
        try:
            # Remove the folder and all contents
            import shutil
            shutil.rmtree(folder_path)
            log_message(f"  ✓ Removed: {folder_name}")
        except Exception as e:
            log_message(f"  ✗ Failed to remove {folder_name}: {str(e)}", "ERROR")

def update_seed_backup(students_data: List[Dict]):
    """Update the main seed backup with correct photo paths"""
    log_message("=" * 80)
    log_message("STEP 4: Updating Main Seed Backup")
    log_message("=" * 80)
    
    log_message(f"Loading seed backup: {SEED_BACKUP_PATH.name}")
    data = load_json_file(SEED_BACKUP_PATH)
    
    # Create backup of original
    backup_path = SEED_BACKUP_PATH.with_suffix('.json.bak')
    if not backup_path.exists():
        log_message(f"Creating backup: {backup_path.name}")
        save_json_file(data, backup_path)
    
    # Update student photo paths
    students_in_backup = data.get("collections", {}).get("students", [])
    log_message(f"Updating {len(students_in_backup)} students")
    
    updated_count = 0
    for student in students_in_backup:
        student_id = student.get("student_id")
        if student_id:
            # Update photo_path
            expected_photo_path = f"backend/photos/students/{student_id}/profile.jpg"
            expected_attendance_path = f"backend/photos/students/{student_id}/attendance"
            
            if student.get("photo_path") != expected_photo_path:
                student["photo_path"] = expected_photo_path
                updated_count += 1
            
            if student.get("attendance_path") != expected_attendance_path:
                student["attendance_path"] = expected_attendance_path
                updated_count += 1
    
    log_message(f"Updated {updated_count} field values")
    
    # Save updated backup
    save_json_file(data, SEED_BACKUP_PATH)
    log_message(f"Saved updated seed backup")

def validate_structure():
    """Validate that the structure matches STRUCTURE_EXAMPLE.txt"""
    log_message("=" * 80)
    log_message("STEP 5: Validating Structure")
    log_message("=" * 80)
    
    # Load seed backup to get valid student list
    data = load_json_file(SEED_BACKUP_PATH)
    students = data.get("collections", {}).get("students", [])
    
    validation_results = {
        "total_students": len(students),
        "profile_photos_present": 0,
        "attendance_folders_present": 0,
        "missing_profile_photos": [],
        "missing_attendance_folders": []
    }
    
    for student in students:
        student_id = student.get("student_id")
        student_name = student.get("name", "Unknown")
        
        if not student_id:
            continue
        
        # Check profile photo
        profile_path = PHOTOS_DIR / student_id / "profile.jpg"
        if profile_path.exists():
            validation_results["profile_photos_present"] += 1
        else:
            validation_results["missing_profile_photos"].append(f"{student_name} ({student_id})")
        
        # Check attendance folder
        attendance_path = PHOTOS_DIR / student_id / "attendance"
        if attendance_path.exists() and attendance_path.is_dir():
            validation_results["attendance_folders_present"] += 1
        else:
            validation_results["missing_attendance_folders"].append(f"{student_name} ({student_id})")
    
    # Print validation report
    log_message("\n" + "=" * 80)
    log_message("VALIDATION REPORT")
    log_message("=" * 80)
    log_message(f"Total Students: {validation_results['total_students']}")
    log_message(f"Profile Photos Present: {validation_results['profile_photos_present']}/{validation_results['total_students']}")
    log_message(f"Attendance Folders Present: {validation_results['attendance_folders_present']}/{validation_results['total_students']}")
    
    if validation_results["missing_profile_photos"]:
        log_message(f"\nMissing Profile Photos ({len(validation_results['missing_profile_photos'])}):", "WARNING")
        for item in validation_results["missing_profile_photos"]:
            log_message(f"  - {item}", "WARNING")
    
    if validation_results["missing_attendance_folders"]:
        log_message(f"\nMissing Attendance Folders ({len(validation_results['missing_attendance_folders'])}):", "WARNING")
        for item in validation_results["missing_attendance_folders"]:
            log_message(f"  - {item}", "WARNING")
    
    # Check naming convention in attendance backup
    log_message("\nChecking Attendance Backup Naming Convention:")
    attendance_backups = sorted(ATTENDANCE_BACKUP_DIR.glob("attendance_backup_*.json"))
    if attendance_backups:
        latest_backup = attendance_backups[-1]
        backup_data = load_json_file(latest_backup)
        attendance_records = backup_data.get("collections", {}).get("attendance", [])
        
        incorrect_names = []
        for record in attendance_records:
            scan_photo = record.get("scan_photo", "")
            if scan_photo and re.search(r'_(green|yellow)\.jpg$', scan_photo):
                incorrect_names.append(scan_photo)
        
        if incorrect_names:
            log_message(f"  ✗ Found {len(incorrect_names)} records with incorrect naming", "ERROR")
            for name in incorrect_names[:5]:  # Show first 5
                log_message(f"    - {name}", "ERROR")
            if len(incorrect_names) > 5:
                log_message(f"    ... and {len(incorrect_names) - 5} more", "ERROR")
        else:
            log_message(f"  ✓ All {len(attendance_records)} records use correct naming convention")
    
    log_message("=" * 80)
    
    return validation_results

def main():
    """Main execution function"""
    log_message("\n\n")
    log_message("=" * 80)
    log_message("ATTENDANCE SYSTEM REFACTORING STARTED")
    log_message("=" * 80)
    log_message(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message(f"Backend Directory: {BACKEND_DIR}")
    log_message(f"Photos Directory: {PHOTOS_DIR}")
    log_message("=" * 80)
    
    try:
        # Step 1: Refactor attendance backup
        attendance_data = refactor_attendance_backup()
        
        # Load seed backup to get student list
        seed_data = load_json_file(SEED_BACKUP_PATH)
        students_data = seed_data.get("collections", {}).get("students", [])
        valid_student_ids = [s["student_id"] for s in students_data if "student_id" in s]
        
        # Step 2: Generate new profile photos
        generate_student_profile_photos(students_data)
        
        # Step 3: Clean orphaned folders
        clean_orphaned_student_folders(valid_student_ids)
        
        # Step 4: Update main seed backup
        update_seed_backup(students_data)
        
        # Step 5: Validate structure
        validation_results = validate_structure()
        
        log_message("\n" + "=" * 80)
        log_message("ATTENDANCE SYSTEM REFACTORING COMPLETED SUCCESSFULLY")
        log_message("=" * 80)
        log_message(f"Log file: {LOG_FILE}")
        
        return validation_results
        
    except Exception as e:
        log_message(f"\nFATAL ERROR: {str(e)}", "ERROR")
        import traceback
        log_message(traceback.format_exc(), "ERROR")
        raise

if __name__ == "__main__":
    main()
