# Pi Simulator Comparison Guide

## Overview

We have **3 different simulators** for testing the Raspberry Pi bus tracking system. Each serves a different purpose.

## Quick Comparison

| Feature | Real-Time Scanner | Batch Simulator | Device API Tester |
|---------|------------------|----------------|-------------------|
| **Mode** | Continuous thread | One-time batch | Interactive menu |
| **Setup** | Zero config | Manual config | Manual config |
| **Auto-registration** | ✅ Yes | ❌ No | ❌ No |
| **RFID simulation** | ✅ Yes | ❌ No | ❌ No |
| **Face recognition** | ✅ Yes | ✅ Yes | ❌ No |
| **Embedding comparison** | ✅ Yes | ✅ Yes | ❌ No |
| **Real-time delays** | ✅ Yes | ❌ No | ❌ No |
| **Photo saving** | ✅ Yes | ✅ Yes | ❌ No |
| **Best for** | Device testing | Bulk testing | API testing |

## Detailed Comparison

### 1. Pi Real-Time Scanner ⭐ RECOMMENDED

**File:** `pi_realtime_scanner.py`

**Purpose:** Simulates a real Raspberry Pi device with RFID scanner in real-time.

**When to use:**
- Testing the complete Pi device workflow
- Simulating actual boarding scenarios
- Testing face recognition in real-time
- Demonstrating the system to stakeholders
- Integration testing

**How it works:**
```
1. Automatically registers device
2. Starts continuous scanning thread
3. Simulates RFID scans (one student every 3 seconds)
4. For each scan:
   - Fetches student embedding from API (by RFID)
   - Generates embedding from photo
   - Compares embeddings
   - Sends verification result to backend
   - Saves to attendance folder
5. Automatically cycles AM → PM
```

**Usage:**
```bash
python3 pi_realtime_scanner.py
# That's it! No configuration needed.
```

**Output:**
```
📡 RFID Scan Detected
  RFID: RFID-1001
  Student: Emma Johnson
  
[1/6] Loading profile photo...
  ✓ Photo loaded: profile.jpg
[2/6] Generating embedding from photo...
  ✓ Embedding generated (shape: (128,))
[3/6] Fetching backend embedding via API...
  ✓ Backend embedding fetched
[4/6] Comparing embeddings...
  ✓ Similarity: 0.8765
  ✓ Verification: PASSED (>= 0.6)
[5/6] Converting photo to base64...
  ✓ Photo converted (542472 chars)
[6/6] Sending scan event to backend...
  ✓ Scan event sent successfully

✓ SCAN SUCCESSFUL
  Student: Emma Johnson
  Similarity: 0.8765
  Status: ✓ VERIFIED
  Attendance: YELLOW
```

**Pros:**
- ✅ Zero configuration required
- ✅ Most realistic simulation
- ✅ Automatic device registration
- ✅ Continuous scanning (like real device)
- ✅ Real-time delays between scans
- ✅ Perfect for demos

**Cons:**
- ⏱️ Takes longer (scans one by one)
- 🔄 Continuous (need to stop with Ctrl+C)

---

### 2. Pi Boarding Simulator (Batch)

**File:** `pi_simulator_boarding.py`

**Purpose:** Batch processing tool for testing multiple students at once.

**When to use:**
- Testing many students quickly
- Generating test data in bulk
- Performance testing
- Initial setup and data population
- Testing different scenarios (AM/PM)

**How it works:**
```
1. Loads all students from JSON file
2. Processes each student sequentially
3. For each student:
   - Loads profile photo (or downloads placeholder)
   - Generates embedding with DeepFace
   - Fetches backend embedding
   - Compares embeddings
   - Sends scan event
   - Saves to attendance folder
4. Prints summary table
```

**Usage:**
```bash
# Requires configuration in simulator_config.py first
python3 pi_simulator_boarding.py --scan-type AM
python3 pi_simulator_boarding.py --scan-type PM
```

**Output:**
```
🚌 Pi Boarding Simulator - AM Boarding

Processing: Emma Johnson (9afb783f-7952-476d-8626-0143fdbbc2a1)
1. Loading profile photo...
   ✓ Photo loaded: profile.jpg
2. Generating embedding with DeepFace...
   ✓ Embedding generated (shape: (128,))
3. Fetching backend embedding...
   ✓ Backend embedding fetched
... (repeats for all students)

📊 Simulation Summary
Student ID                               | Similarity | Verified | Upload
-----------------------------------------+------------+----------+-----------
9afb783f-7952-476d-8626-0143fdbbc2a1     | 0.8765     | ✓        | Success

Statistics:
   Total Students: 5
   Successful Uploads: 5
   Success Rate: 100.0%
```

**Pros:**
- ✅ Fast batch processing
- ✅ Summary table with statistics
- ✅ One-time run (no need to stop)
- ✅ Good for bulk testing

**Cons:**
- ⚙️ Requires manual configuration
- ❌ No RFID simulation
- ❌ Not real-time (sequential)

---

### 3. Local Device Simulator (API Tester)

**File:** `local_device_simulator.py`

**Purpose:** Interactive API testing tool for device endpoints.

**When to use:**
- Testing individual API endpoints
- Debugging API calls
- Verifying device authentication
- Testing without face recognition
- Quick API checks

**How it works:**
```
1. Interactive menu
2. Select test to run:
   - Get student embedding
   - Get student photo
   - Send yellow/green scan
   - Update GPS location
3. Manual test execution
```

**Usage:**
```bash
# Requires configuration in simulator_config.py first
python3 local_device_simulator.py

# Or non-interactive
python3 local_device_simulator.py --run-all
```

**Output:**
```
🚌 Bus Tracker - Device API Simulator

Test Menu:
   [1] Get Student Embedding
   [2] Get Student Photo
   [3] Send Yellow Scan (On Board)
   [4] Send Green Scan (Reached)
   [5] Update GPS Location
   [6] Run All Tests
   [0] Exit

Select option: 1

🔍 Testing: Get Student Embedding
✅ SUCCESS
   Student: Emma Johnson
   Has Embedding: false
```

**Pros:**
- ✅ Interactive menu
- ✅ Test individual endpoints
- ✅ Good for debugging
- ✅ Detailed logs

**Cons:**
- ❌ No face recognition
- ❌ No RFID simulation
- ❌ Manual operation
- ⚙️ Requires configuration

---

## Which Simulator to Use?

### Use Real-Time Scanner When:
- ✅ You want to see the system working **like a real device**
- ✅ You need to demonstrate to stakeholders
- ✅ You want zero-config quick testing
- ✅ You're testing the complete workflow
- ✅ You want realistic timing and delays

### Use Batch Simulator When:
- ✅ You need to test **many students quickly**
- ✅ You're generating bulk test data
- ✅ You want summary statistics
- ✅ You're doing performance testing
- ✅ You need to test specific scenarios (AM/PM)

### Use Device API Tester When:
- ✅ You're debugging **specific API endpoints**
- ✅ You want to test without face recognition
- ✅ You need interactive testing
- ✅ You're verifying device authentication
- ✅ You want detailed API logs

---

## Example Workflows

### Workflow 1: Initial Setup & Testing

**Goal:** Set up the system and verify everything works.

**Steps:**
1. Use **Real-Time Scanner** for first test:
   ```bash
   python3 pi_realtime_scanner.py
   ```
   - Automatically registers device
   - Tests complete workflow
   - Verifies face recognition

2. Check results in parent dashboard

3. If issues, use **Device API Tester** to debug:
   ```bash
   python3 local_device_simulator.py
   ```
   - Test individual endpoints
   - Check API responses

### Workflow 2: Bulk Data Generation

**Goal:** Create attendance records for many students.

**Steps:**
1. Configure `simulator_config.py` with device key
2. Update `students_boarding.json` with all students
3. Use **Batch Simulator** for bulk processing:
   ```bash
   python3 pi_simulator_boarding.py --scan-type AM
   python3 pi_simulator_boarding.py --scan-type PM
   ```
4. Verify summary statistics

### Workflow 3: Demo to Stakeholders

**Goal:** Show the system working in real-time.

**Steps:**
1. Use **Real-Time Scanner**:
   ```bash
   python3 pi_realtime_scanner.py
   ```
2. Show console output (color-coded, clear)
3. Show parent dashboard updating in real-time
4. Show attendance photos being saved

### Workflow 4: Debugging Issues

**Goal:** Fix a specific API or recognition issue.

**Steps:**
1. Use **Device API Tester** to isolate the problem:
   ```bash
   python3 local_device_simulator.py
   ```
2. Test specific endpoint that's failing
3. Check detailed logs
4. Fix the issue
5. Verify with **Real-Time Scanner**

---

## Feature Matrix

| Feature | Real-Time | Batch | API Tester |
|---------|-----------|-------|------------|
| Auto-registration | ✅ | ❌ | ❌ |
| Config-free | ✅ | ❌ | ❌ |
| RFID simulation | ✅ | ❌ | ❌ |
| Face recognition | ✅ | ✅ | ❌ |
| DeepFace embedding | ✅ | ✅ | ❌ |
| Cosine similarity | ✅ | ✅ | ❌ |
| Batch processing | ❌ | ✅ | ❌ |
| Interactive menu | ❌ | ❌ | ✅ |
| Real-time delays | ✅ | ❌ | ❌ |
| Summary statistics | ❌ | ✅ | ✅ |
| Continuous scanning | ✅ | ❌ | ❌ |
| AM/PM cycling | ✅ | ✅ | ✅ |
| Photo saving | ✅ | ✅ | ❌ |
| Device auth | ✅ | ✅ | ✅ |
| API testing | ✅ | ✅ | ✅ |

---

## Quick Start Commands

### Zero Config (Recommended)
```bash
# Real-time scanner - just run it!
python3 pi_realtime_scanner.py
```

### With Configuration
```bash
# 1. Configure simulator_config.py first
# 2. Then run:

# Batch processing
python3 pi_simulator_boarding.py --scan-type AM

# Interactive API testing
python3 local_device_simulator.py
```

---

## Summary

**🏆 Best for most cases:** Real-Time Scanner (`pi_realtime_scanner.py`)
- Zero configuration
- Most realistic
- Complete workflow
- Great for demos

**📦 Best for bulk testing:** Batch Simulator (`pi_simulator_boarding.py`)
- Fast processing
- Summary statistics
- Good for data generation

**🔧 Best for debugging:** Device API Tester (`local_device_simulator.py`)
- Interactive testing
- Detailed logs
- Endpoint-specific

---

**Choose based on your needs, or use all three for comprehensive testing!**
