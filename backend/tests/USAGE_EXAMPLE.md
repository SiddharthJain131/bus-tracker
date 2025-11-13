# Pi Boarding Simulator - Usage Examples

## Prerequisites

1. **Install Dependencies** (done automatically on first run):
```bash
pip install deepface tf-keras tensorflow opencv-python
```

2. **Configure Device API Key**:
   - Register a device via admin dashboard or API
   - Update `DEVICE_API_KEY` in `simulator_config.py`
   - Update `BUS_ID` in `simulator_config.py`

3. **Prepare Student Data**:
   - Edit `students_boarding.json` with your student IDs
   - Format:
     ```json
     [
       {
         "student_id": "uuid-here",
         "rfid": "RFID-1001",
         "class": "5",
         "section": "A",
         "name": "Student Name"
       }
     ]
     ```

## Basic Usage

### Example 1: Morning Boarding (AM)

```bash
cd /app/backend/tests
python3 pi_simulator_boarding.py --scan-type AM
```

**What happens:**
- Loads all students from `students_boarding.json`
- For each student:
  - Loads profile photo from `backend/photos/students/<id>/profile.jpg`
  - If missing, downloads placeholder and saves it
  - Generates face embedding using DeepFace Facenet
  - Fetches backend embedding via API
  - Compares embeddings with cosine similarity
  - Sends scan event with `scan_type="yellow"` (On Board status)
  - Converts photo to base64 and includes in event
  - Saves photo to `attendance/YYYY-MM-DD_AM.jpg`

**Expected Output:**
```
======================================================================
🚌 Pi Boarding Simulator - yellow Boarding
======================================================================

Checking dependencies...
✓ DeepFace is already installed

Loading students...
✓ Loaded 5 students from JSON

Starting boarding simulation...

[1/5]
Processing: Emma Johnson (9afb783f-7952-476d-8626-0143fdbbc2a1)
1. Loading profile photo...
   ✓ Photo loaded: profile.jpg
2. Generating embedding with DeepFace...
   ✓ Embedding generated (shape: (128,))
3. Fetching backend embedding...
   ⚠ Backend embedding not available, using local only
4. Comparing embeddings...
   ✓ Similarity: 1.0000 (Threshold: 0.6)
   ✓ Verification: PASSED
5. Converting photo to base64...
   ✓ Photo converted (542472 chars)
6. Sending scan event to backend...
   ✓ Scan event uploaded: Success
7. Saving photo to attendance folder...
   ✓ Photo saved: 2025-01-15_AM.jpg

... (repeats for each student)

======================================================================
📊 Simulation Summary
======================================================================

Student ID                               | Similarity | Verified | Upload
-----------------------------------------+------------+----------+-----------
9afb783f-7952-476d-8626-0143fdbbc2a1     | 1.0000     | ✓        | Success
   Photo: /app/backend/photos/students/9afb783f-.../attendance/2025-01-15_AM.jpg

Statistics:
   Total Students: 5
   Successful Uploads: 5
   Verified: 5
   Failed: 0
   Success Rate: 100.0%
   Verification Rate: 100.0%
```

### Example 2: Afternoon Boarding (PM)

```bash
python3 pi_simulator_boarding.py --scan-type PM
```

**Difference from AM:**
- Sends `scan_type="green"` (Reached status)
- Saves photo as `YYYY-MM-DD_PM.jpg`

### Example 3: Using Status Colors Directly

```bash
# Yellow status (On Board)
python3 pi_simulator_boarding.py --scan-type yellow

# Green status (Reached)
python3 pi_simulator_boarding.py --scan-type green
```

## Advanced Scenarios

### Scenario 1: Test with Missing Photos

To test placeholder photo generation:

```bash
# Remove a student's profile photo
rm /app/backend/photos/students/9afb783f-7952-476d-8626-0143fdbbc2a1/profile.jpg

# Run simulator
python3 pi_simulator_boarding.py --scan-type AM
```

**Expected behavior:**
```
1. Loading profile photo...
   ⚠ Downloading placeholder photo...
   ✓ Placeholder photo saved
```

The simulator will:
1. Detect missing photo
2. Download from thispersondoesnotexist.com
3. Save as `profile.jpg`
4. Use it for embedding generation
5. Continue normally

### Scenario 2: Test Embedding Comparison

To test similarity scoring:

1. **High Similarity (Same Person):**
   - Use actual profile photo
   - Expected similarity: 0.8-1.0
   - Verification: PASSED

2. **Low Similarity (Different Person):**
   ```bash
   # Replace a student's photo with different person
   cp /path/to/different/photo.jpg \
      /app/backend/photos/students/<student_id>/profile.jpg
   
   # Run simulator
   python3 pi_simulator_boarding.py
   ```
   - Expected similarity: 0.0-0.5
   - Verification: FAILED (if below threshold)

3. **No Backend Embedding:**
   - Backend embedding doesn't exist yet
   - Simulator uses local embedding only
   - Similarity: 1.0 (assumes perfect match)
   - Verification: PASSED

### Scenario 3: Custom Student List

Create a custom student JSON file:

```bash
# Create custom file
cat > custom_students.json << 'EOF'
[
  {
    "student_id": "student-uuid-1",
    "rfid": "RFID-2001",
    "class": "6",
    "section": "B",
    "name": "John Doe"
  },
  {
    "student_id": "student-uuid-2",
    "rfid": "RFID-2002",
    "class": "6",
    "section": "B",
    "name": "Jane Smith"
  }
]
EOF

# Modify simulator to use custom file
# Edit pi_simulator_boarding.py:
# STUDENTS_JSON_FILE = Path(__file__).parent / "custom_students.json"
```

## Output Details

### Console Output Sections

1. **Header**: Shows scan type and configuration
2. **Dependencies Check**: Verifies DeepFace installation
3. **Student Loading**: Confirms JSON file loaded
4. **Processing Loop**: Details for each student (7 steps)
5. **Summary Table**: Student-by-student results
6. **Statistics**: Overall success/failure rates

### Saved Files

For each successful boarding:

```
/app/backend/photos/students/<student_id>/
├── profile.jpg                    # Profile photo (source)
└── attendance/
    ├── 2025-01-15_AM.jpg         # Morning boarding
    └── 2025-01-15_PM.jpg         # Afternoon boarding
```

### Backend Records

Each scan event creates:
1. **Attendance Record**: In `attendance` collection
   - student_id
   - scan_type: "yellow" or "green"
   - attendance_status: "yellow" or "green"
   - timestamp
   - GPS coordinates
   - confidence score (embedding similarity)

2. **Notification** (if verified=false):
   - Identity mismatch alert to parent
   - Shows photo and similarity score

## Verification Thresholds

Default threshold: **0.6** (60% similarity)

### Adjusting Threshold

Edit `pi_simulator_boarding.py`:

```python
SIMILARITY_THRESHOLD = 0.7  # Stricter (70%)
# or
SIMILARITY_THRESHOLD = 0.5  # More lenient (50%)
```

**Recommended values:**
- **0.8-0.9**: Very strict (high security, more false negatives)
- **0.6-0.7**: Balanced (recommended for production)
- **0.4-0.5**: Lenient (fewer false negatives, more false positives)

## Integration Testing

### Full Workflow Test

Test the complete boarding workflow:

```bash
# 1. Register device
curl -X POST http://localhost:8001/api/device/register \
  -H 'Cookie: session=<admin_session>' \
  -H 'Content-Type: application/json' \
  -d '{"bus_id":"<BUS_ID>","device_name":"Test Device"}'

# 2. Update simulator_config.py with API key

# 3. Run AM boarding
python3 pi_simulator_boarding.py --scan-type AM

# 4. Verify in parent dashboard
# - Login as parent
# - Check attendance grid shows yellow status for today
# - Check notifications for any identity mismatches

# 5. Run PM boarding
python3 pi_simulator_boarding.py --scan-type PM

# 6. Verify in parent dashboard
# - Attendance grid should show green status for today
```

### Batch Testing

Test multiple boarding cycles:

```bash
# Morning boarding for multiple days
for day in {1..5}; do
  echo "Day $day - Morning Boarding"
  python3 pi_simulator_boarding.py --scan-type AM
  sleep 2
done

# Afternoon boarding
for day in {1..5}; do
  echo "Day $day - Afternoon Boarding"
  python3 pi_simulator_boarding.py --scan-type PM
  sleep 2
done
```

## Common Issues & Solutions

### Issue 1: "Device API Key not configured"
**Solution**: Update `DEVICE_API_KEY` in `simulator_config.py`

### Issue 2: "Backend embedding fetch failed: 403"
**Solution**: 
- Verify device is registered for the bus
- Check API key is correct
- Ensure device has access to the bus

### Issue 3: "Embedding generation failed"
**Solution**:
- Check photo file is valid (JPEG/PNG)
- Verify photo contains a face
- Wait for DeepFace model download (first run)

### Issue 4: "Photo not available"
**Solution**:
- Ensure student directory exists
- Check internet connection (for placeholder download)
- Verify student ID is correct

### Issue 5: Low similarity scores
**Solution**:
- Verify profile photo is of correct student
- Check photo quality (clear face, good lighting)
- Consider adjusting similarity threshold
- Ensure backend embedding is from same photo

## Performance Optimization

### Tip 1: Pre-download Models

First run downloads DeepFace models (~100MB). Pre-download:

```python
from deepface import DeepFace
DeepFace.build_model('Facenet')
```

### Tip 2: Batch Processing

Process multiple students in parallel:

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_student, students))
```

### Tip 3: Cache Embeddings

Store generated embeddings to avoid regeneration:

```python
import pickle

# Save embedding
with open('embedding_cache.pkl', 'wb') as f:
    pickle.dump(embedding, f)

# Load embedding
with open('embedding_cache.pkl', 'rb') as f:
    embedding = pickle.load(f)
```

## Next Steps

1. ✅ Run basic AM boarding simulation
2. ✅ Verify attendance records in dashboard
3. ✅ Test PM boarding simulation
4. ✅ Test with missing photos (placeholder generation)
5. ✅ Test embedding comparison accuracy
6. ✅ Review attendance photos in attendance folder
7. ✅ Check notifications for identity mismatches

## Related Documentation

- [Complete Boarding Simulator Guide](./PI_BOARDING_SIMULATOR_README.md)
- [Device API Testing](./README.md)
- [Raspberry Pi Integration](../../docs/RASPBERRY_PI_INTEGRATION.md)
- [Photo Organization](../../docs/PHOTO_ORGANIZATION.md)

---

**Ready to test!** Run your first simulation:
```bash
cd /app/backend/tests
python3 pi_simulator_boarding.py --scan-type AM
```
