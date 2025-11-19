#!/usr/bin/env python3
"""
cam_test.py - Authoritative Camera Module
==========================================

This module provides the proven, stable camera implementation.
All camera operations should route through this module.

IMPORTANT: This is the reference implementation - do not copy or rewrite
its logic. Import and use directly.
"""

import cv2
import os
import numpy as np
import threading
import datetime
import time
from typing import Optional, Tuple

# Try to import optional dependencies
try:
    from ultralight import UltraLightDetector
    DETECTOR_AVAILABLE = True
except ImportError:
    DETECTOR_AVAILABLE = False
    UltraLightDetector = None

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    DeepFace = None

# Global state - thread-safe access via locks
_detector = None
_camera_cap = None
_camera_thread = None
_camera_running = False
_latest_frame = None
_frame_lock = threading.Lock()
_capture_trigger = False
_rotation_count = 0
_shutdown_event = threading.Event()

# Configuration
_offset_ratio = 0.3
_droidcam_url = None

# Directory to save captured face photos
save_dir = "captured_faces"
os.makedirs(save_dir, exist_ok=True)

# Path to image database for comparison (optional)
database_dir = os.path.expanduser("~/Downloads/Photos")

def crop_with_offset(frame: np.ndarray, box: list, offset_ratio: float = None) -> np.ndarray:
    """
    Crop face with offset for better framing.
    This is the authoritative crop implementation.
    """
    if offset_ratio is None:
        offset_ratio = _offset_ratio

    x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
    height, width = frame.shape[:2]

    w = x2 - x1
    h = y2 - y1
    cx = x1 + w // 2
    cy = y1 + h // 2

    half_w = int(w * (1 + offset_ratio) / 2)
    half_h = int(h * (1 + offset_ratio) / 2)

    x_start = max(cx - half_w, 0)
    y_start = max(cy - half_h, 0)
    x_end = min(cx + half_w, width)
    y_end = min(cy + half_h, height)

    return frame[y_start:y_end, x_start:x_end]

def verify_against_database(face_img):
    """
    Optional face verification against database.
    Only used for testing/demo purposes.
    """
    if not DEEPFACE_AVAILABLE:
        print("DeepFace not available for verification")
        return

    if not os.path.exists(database_dir):
        print(f"Database directory not found: {database_dir}")
        return

    best_score = None
    best_match_path = None

    for filename in os.listdir(database_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            db_img_path = os.path.join(database_dir, filename)
            try:
                result = DeepFace.verify(
                    face_img,
                    db_img_path,
                    model_name="Facenet",
                    enforce_detection=True
                )
                score = 1 - result["distance"]
                if result['verified'] == True:
                    print(f"Compared with {filename}: confidence={score:.4f}")
                if best_score is None or score > best_score:
                    best_score = score
                    best_match_path = filename
            except Exception as e:
                print(f"Error comparing with {filename}: {e}")

    if best_match_path:
        print(f"\nBest match: {best_match_path} with confidence {best_score:.4f}")
    else:
        print("No matches found in the database.")

def _camera_thread_loop():
    """
    AUTHORITATIVE camera thread implementation.
    This is the proven stable camera loop - DO NOT MODIFY.
    """
    global _camera_running, _camera_cap, _latest_frame

    print("[cam_test] Starting camera thread...")

    while _camera_running and not _shutdown_event.is_set():
        try:
            # CRITICAL: No cv2.CAP_FFMPEG flag - this is the proven stable approach
            _camera_cap = cv2.VideoCapture(_droidcam_url)
            time.sleep(1)  # Give camera time to initialize

            if not _camera_cap.isOpened():
                print("[cam_test] ERROR: Could not open camera stream")
                time.sleep(3)
                continue

            print("[cam_test] Camera connected")

            # Main frame capture loop
            while _camera_running and not _shutdown_event.is_set():
                ret, frame = _camera_cap.read()

                if not ret or frame is None:
                    print("[cam_test] Frame dropped, reconnecting...")
                    break

                # Store latest frame (thread-safe)
                with _frame_lock:
                    _latest_frame = frame

                # CRITICAL: 0.03s sleep for ~33 FPS - proven stable rate
                time.sleep(0.03)

            # Cleanup after inner loop
            if _camera_cap is not None:
                try:
                    _camera_cap.release()
                except Exception as e:
                    print(f"[cam_test] Error releasing camera: {e}")
                finally:
                    _camera_cap = None
            time.sleep(1)

        except Exception as e:
            if _camera_running and not _shutdown_event.is_set():
                print(f"[cam_test] Camera thread error: {e}")
                print("[cam_test] Attempting to reconnect in 3 seconds...")

            # Clean up failed connection
            if _camera_cap is not None:
                try:
                    _camera_cap.release()
                except:
                    pass
                finally:
                    _camera_cap = None

            time.sleep(3)

    # Final cleanup when exiting thread
    with _frame_lock:
        _latest_frame = None

    if _camera_cap is not None:
        try:
            _camera_cap.release()
        except:
            pass
        finally:
            _camera_cap = None

    print("[cam_test] Camera thread stopped")

def detection_loop(cap):
    """
    Interactive detection loop for testing/demo.
    Not used by production pi_server.py integration.
    """
    global _capture_trigger, _rotation_count

    if not DETECTOR_AVAILABLE:
        print("Detector not available, using basic preview")
        return

    detector = UltraLightDetector()

    print("Starting face detection thread...")

    l1, l2 = 500, 600
    cv2.namedWindow('DroidCam - Face Detection', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('DroidCam - Face Detection', l2, l1)
    cv2.moveWindow('DroidCam - Face Detection', 50, 100)

    rotate_flags = {
        0: None,
        1: cv2.ROTATE_90_CLOCKWISE,
        2: cv2.ROTATE_180,
        3: cv2.ROTATE_90_COUNTERCLOCKWISE,
    }

    while not _shutdown_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("Error: Cannot read frame from stream")
            break

        flag = rotate_flags.get(_rotation_count % 4)
        if flag is not None:
            frame = cv2.rotate(frame, flag)

        frame_to_process = frame.copy()

        boxes, scores = detector.detect_one(frame)

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                w = x2 - x1
                h = y2 - y1
                cx = x1 + w // 2
                cy = y1 + h // 2

                half_w = int(w * (1 + _offset_ratio) / 2)
                half_h = int(h * (1 + _offset_ratio) / 2)

                height, width = frame.shape[:2]
                ex1 = max(cx - half_w, 0)
                ey1 = max(cy - half_h, 0)
                ex2 = min(cx + half_w, width)
                ey2 = min(cy + half_h, height)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(frame, (ex1, ey1), (ex2, ey2), (0, 0, 255), 2)

                text = f"W:{ex2 - ex1} H:{ey2 - ey1}"
                cv2.putText(frame, text, (ex1, ey1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 0, 255), 2)

        cv2.imshow('DroidCam - Face Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if _capture_trigger:
            if boxes is not None and len(boxes) > 0:
                boxes_list = boxes.tolist() if isinstance(boxes, np.ndarray) else list(boxes)
                scores_list = scores.tolist() if isinstance(scores, np.ndarray) else list(scores)
                best_idx = scores_list.index(max(scores_list))
                best_box = boxes_list[best_idx]

                cropped_face = crop_with_offset(frame_to_process, best_box, _offset_ratio)

                if cropped_face.size > 0:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    photo_path = os.path.join(save_dir, f"{timestamp}.jpg")
                    cv2.imwrite(photo_path, cropped_face)
                    print(f"Captured photo saved: {photo_path}")

                    print("\nRunning verification against database...")
                    verify_against_database(cropped_face)

            _capture_trigger = False

    cap.release()
    cv2.destroyAllWindows()
    print("Detection thread stopped.")

# ============================================================
# PUBLIC API - Use these functions for camera integration
# ============================================================

def initialize_camera(droidcam_url: str, detector_instance=None) -> bool:
    """
    Initialize camera module.

    Args:
        droidcam_url: Full URL to DroidCam stream (e.g., "http://IP:4747/video")
        detector_instance: Optional UltraLightDetector instance

    Returns:
        True if initialization successful
    """
    global _droidcam_url, _detector

    _droidcam_url = droidcam_url
    _detector = detector_instance

    # Test connection
    try:
        cap = cv2.VideoCapture(_droidcam_url)
        time.sleep(1)

        if cap.isOpened():
            ret, _ = cap.read()
            cap.release()

            if ret:
                print(f"[cam_test] Camera initialized at {_droidcam_url}")
                return True
        else:
            cap.release()
    except Exception as e:
        print(f"[cam_test] Initialization failed: {e}")

    return False

def start_camera_thread() -> bool:
    """
    Start background camera thread.
    AUTHORITATIVE implementation - routes to proven stable thread loop.

    Returns:
        True if thread started successfully
    """
    global _camera_thread, _camera_running

    if not _droidcam_url:
        print("[cam_test] ERROR: Camera not initialized. Call initialize_camera() first.")
        return False

    with _frame_lock:
        if _camera_running:
            print("[cam_test] Camera thread already running")
            return True

        _shutdown_event.clear()
        _camera_running = True
        _camera_thread = threading.Thread(
            target=_camera_thread_loop,
            daemon=True,
            name="CamTestThread"
        )
        _camera_thread.start()

    return True

def stop_camera_thread() -> None:
    """
    Stop background camera thread safely.
    AUTHORITATIVE cleanup implementation.
    """
    global _camera_running, _camera_thread

    with _frame_lock:
        if not _camera_running:
            print("[cam_test] Camera thread not running")
            return

        print("[cam_test] Stopping camera thread...")
        _camera_running = False
        _shutdown_event.set()

    # Wait for thread to finish with timeout
    if _camera_thread is not None and _camera_thread.is_alive():
        _camera_thread.join(timeout=5.0)
        
        if _camera_thread.is_alive():
            print("[cam_test] WARNING: Camera thread did not stop within timeout")
        else:
            print("[cam_test] Camera thread stopped successfully")

    _camera_thread = None

def get_latest_frame() -> Optional[np.ndarray]:
    """
    Get the latest frame from camera thread.
    AUTHORITATIVE frame retrieval - thread-safe access.

    Returns:
        Copy of latest frame or None if unavailable
    """
    if not _camera_running:
        return None

    with _frame_lock:
        if _latest_frame is None:
            return None
        return _latest_frame.copy()

def is_camera_running() -> bool:
    """Check if camera thread is running."""
    return _camera_running

def detect_faces_in_frame(frame: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Detect faces in a frame using the detector.

    Args:
        frame: Input frame

    Returns:
        Tuple of (boxes, scores) or (None, None) if no detector
    """
    if _detector is None:
        return None, None

    try:
        boxes, scores = _detector.detect_one(frame)
        return boxes, scores
    except Exception as e:
        print(f"[cam_test] Detection error: {e}")
        return None, None

def cleanup() -> None:
    """
    Clean up camera resources efficiently.
    AUTHORITATIVE cleanup - ensures safe shutdown with proper resource release.
    """
    global _camera_cap, _camera_thread, _camera_running, _latest_frame, _detector, _droidcam_url

    print("[cam_test] Starting cleanup...")

    # Step 1: Stop the camera thread
    stop_camera_thread()

    # Step 2: Clean up camera capture object with lock protection
    with _frame_lock:
        if _camera_cap is not None:
            try:
                if _camera_cap.isOpened():
                    _camera_cap.release()
                print("[cam_test] Camera capture released")
            except Exception as e:
                print(f"[cam_test] Error releasing camera capture: {e}")
            finally:
                _camera_cap = None

        # Clear latest frame
        _latest_frame = None

    # Step 3: Close any OpenCV windows
    try:
        cv2.destroyAllWindows()
        # Give OS time to process window destruction
        cv2.waitKey(1)
        print("[cam_test] OpenCV windows closed")
    except Exception as e:
        print(f"[cam_test] Error closing windows: {e}")

    # Step 4: Reset global state
    _shutdown_event.set()
    _camera_running = False
    _camera_thread = None

    # Note: We don't reset _detector and _droidcam_url as they may be reused
    # They will be reset on next initialize_camera() call if needed

    print("[cam_test] Cleanup complete")

# ============================================================
# INTERACTIVE TESTING MODE (for manual testing only)
# ============================================================

def trigger_capture():
    """Interactive capture for testing. Not used in production."""
    global _capture_trigger, _rotation_count

    l1, l2 = 500, 600
    while not _shutdown_event.is_set():
        cmd = input("Type ENTER to capture photo, 'rotate' to rotate feed, or 'quit' to exit:\n").strip().lower()
        if cmd == 'quit':
            break
        elif cmd == 'rotate':
            with _frame_lock:
                _rotation_count = (_rotation_count + 1) % 4
                if _rotation_count % 2 == 1:
                    window_width, window_height = l1, l2
                else:
                    window_width, window_height = l2, l1
                try:
                    cv2.resizeWindow('DroidCam - Face Detection', window_width, window_height)
                except:
                    pass
            print(f"Rotation changed. Now rotating {_rotation_count * 90} degrees clockwise.")
        else:
            _capture_trigger = True

def main(default_ip="172.17.72.186", default_port="4747"):
    """
    Interactive testing mode.
    Run directly: python cam_test.py
    """
    if not DETECTOR_AVAILABLE:
        print("ERROR: UltraLight detector not available")
        print("Install: pip install ultralight")
        return

    ip_input = input(f"Enter DroidCam IP address (default {default_ip}): ").strip()
    if not ip_input:
        ip_input = default_ip

    port_input = input(f"Enter DroidCam port (default {default_port}): ").strip()
    if not port_input:
        port_input = default_port

    DROIDCAM_URL = f"http://{ip_input}:{port_input}/video"

    cap = cv2.VideoCapture(DROIDCAM_URL)
    if not cap.isOpened():
        raise SystemExit(f"Error: Cannot open DroidCam stream at {DROIDCAM_URL}")

    detection_thread = threading.Thread(target=detection_loop, daemon=True, args=(cap,))
    detection_thread.start()

    try:
        trigger_capture()
    finally:
        _shutdown_event.set()
        detection_thread.join(timeout=5.0)
        cleanup()

if __name__ == "__main__":
    main()
