#!/usr/bin/env python3
"""
Rename Attendance Photos
========================
This script renames all attendance photos to remove _green and _yellow suffixes.
Important: When a status changes from yellow to green, the same photo is kept.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
PHOTOS_DIR = Path("/app/backend/photos/students")
LOG_FILE = Path("/app/backend/logs/rename_attendance_photos.log")

# Ensure logs directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log_message(message: str, level: str = "INFO"):
    """Log a message to console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] [{level}] {message}"
    print(formatted_message)
    with open(LOG_FILE, "a") as f:
        f.write(formatted_message + "\n")

def rename_attendance_photos():
    """
    Rename all attendance photos to remove _green and _yellow suffixes.
    If both yellow and green versions exist for same date/time, keep only one.
    """
    log_message("=" * 80)
    log_message("RENAMING ATTENDANCE PHOTOS")
    log_message("=" * 80)
    
    total_renamed = 0
    total_removed = 0
    total_students = 0
    
    # Iterate through all student folders
    for student_dir in sorted(PHOTOS_DIR.iterdir()):
        if not student_dir.is_dir():
            continue
        
        total_students += 1
        attendance_dir = student_dir / "attendance"
        
        if not attendance_dir.exists() or not attendance_dir.is_dir():
            log_message(f"  Skipping {student_dir.name} - no attendance folder")
            continue
        
        student_name = student_dir.name
        log_message(f"\nProcessing student: {student_name}")
        
        # Get all attendance photos
        attendance_photos = sorted(attendance_dir.glob("*.jpg"))
        
        if not attendance_photos:
            log_message(f"  No attendance photos found")
            continue
        
        # Track which base filenames we've processed
        processed_base_names = set()
        
        for photo_path in attendance_photos:
            photo_name = photo_path.name
            
            # Check if this photo has a status suffix
            if '_green.jpg' in photo_name or '_yellow.jpg' in photo_name:
                # Extract base name (e.g., 2025-11-14_AM.jpg)
                base_name = photo_name.replace('_green.jpg', '.jpg').replace('_yellow.jpg', '.jpg')
                new_path = attendance_dir / base_name
                
                # If we've already processed this base name, remove this duplicate
                if base_name in processed_base_names:
                    log_message(f"  Removing duplicate: {photo_name}")
                    photo_path.unlink()
                    total_removed += 1
                else:
                    # If target already exists, remove it first
                    if new_path.exists():
                        log_message(f"  Removing existing: {new_path.name}")
                        new_path.unlink()
                        total_removed += 1
                    
                    # Rename the photo
                    log_message(f"  Renaming: {photo_name} -> {base_name}")
                    photo_path.rename(new_path)
                    total_renamed += 1
                    processed_base_names.add(base_name)
    
    log_message("\n" + "=" * 80)
    log_message("SUMMARY")
    log_message("=" * 80)
    log_message(f"Total Students Processed: {total_students}")
    log_message(f"Photos Renamed: {total_renamed}")
    log_message(f"Duplicate Photos Removed: {total_removed}")
    log_message("=" * 80)

def verify_naming():
    """Verify that all photos follow correct naming convention"""
    log_message("\n" + "=" * 80)
    log_message("VERIFICATION")
    log_message("=" * 80)
    
    incorrect_count = 0
    total_photos = 0
    
    for student_dir in sorted(PHOTOS_DIR.iterdir()):
        if not student_dir.is_dir():
            continue
        
        attendance_dir = student_dir / "attendance"
        if not attendance_dir.exists():
            continue
        
        for photo_path in attendance_dir.glob("*.jpg"):
            total_photos += 1
            photo_name = photo_path.name
            
            if '_green.jpg' in photo_name or '_yellow.jpg' in photo_name:
                log_message(f"  ✗ Incorrect: {student_dir.name}/{photo_name}", "ERROR")
                incorrect_count += 1
    
    if incorrect_count == 0:
        log_message(f"  ✓ All {total_photos} attendance photos use correct naming convention")
    else:
        log_message(f"  ✗ Found {incorrect_count} photos with incorrect naming", "ERROR")
    
    log_message("=" * 80)

def main():
    log_message("\n\n")
    log_message("=" * 80)
    log_message("ATTENDANCE PHOTO RENAMING STARTED")
    log_message("=" * 80)
    log_message(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message(f"Photos Directory: {PHOTOS_DIR}")
    log_message("=" * 80)
    
    try:
        # Rename all photos
        rename_attendance_photos()
        
        # Verify the results
        verify_naming()
        
        log_message("\n" + "=" * 80)
        log_message("ATTENDANCE PHOTO RENAMING COMPLETED SUCCESSFULLY")
        log_message("=" * 80)
        log_message(f"Log file: {LOG_FILE}")
        
    except Exception as e:
        log_message(f"\nFATAL ERROR: {str(e)}", "ERROR")
        import traceback
        log_message(traceback.format_exc(), "ERROR")
        raise

if __name__ == "__main__":
    main()
