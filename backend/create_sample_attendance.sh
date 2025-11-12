#!/bin/bash
# Create sample attendance photo files to demonstrate structure

# Get one student directory as example
STUDENT_DIR=$(ls -d /app/backend/photos/students/*/ | head -1)

if [ -n "$STUDENT_DIR" ]; then
    ATTENDANCE_DIR="${STUDENT_DIR}attendance/"
    
    # Create sample attendance filenames (empty files for demo)
    echo "Creating sample attendance photo structure..."
    
    # Create sample files for different dates
    touch "${ATTENDANCE_DIR}2025-11-14_AM.jpg"
    touch "${ATTENDANCE_DIR}2025-11-14_PM.jpg"
    touch "${ATTENDANCE_DIR}2025-11-13_AM.jpg"
    touch "${ATTENDANCE_DIR}2025-11-13_PM.jpg"
    touch "${ATTENDANCE_DIR}2025-11-12_AM.jpg"
    touch "${ATTENDANCE_DIR}2025-11-12_PM.jpg"
    
    echo "✓ Created sample attendance photos in: ${ATTENDANCE_DIR}"
    echo ""
    echo "Sample structure:"
    ls -lh "${ATTENDANCE_DIR}" | tail -6
else
    echo "Error: No student directories found"
    exit 1
fi
