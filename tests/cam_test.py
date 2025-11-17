import cv2
from ultralight import UltraLightDetector
import os
import numpy as np
import threading
import datetime
from deepface import DeepFace

# Initialize the face detector
detector = UltraLightDetector()

# Directory to save captured face photos
save_dir = "captured_faces"
os.makedirs(save_dir, exist_ok=True)

# Path to image database for comparison
database_dir = os.path.expanduser("~/Downloads/Photos")
l1 = 500
l2 = 600
capture_trigger = False
frame_to_process = None
lock = threading.Lock()
offset_ratio = 0.3
rotation_count = 0  # global rotation state

def crop_with_offset(frame, box, offset_ratio=offset_ratio):
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


def detection_loop(cap):
    global capture_trigger, frame_to_process, rotation_count

    print("Starting face detection thread...")

    cv2.namedWindow('DroidCam - Face Detection', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('DroidCam - Face Detection', l2, l1)
    cv2.moveWindow('DroidCam - Face Detection', 50, 100)

    rotate_flags = {
        0: None,
        1: cv2.ROTATE_90_CLOCKWISE,
        2: cv2.ROTATE_180,
        3: cv2.ROTATE_90_COUNTERCLOCKWISE,
    }

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Cannot read frame from stream")
            break

        flag = rotate_flags.get(rotation_count % 4)
        if flag is not None:
            frame = cv2.rotate(frame, flag)

        with lock:
            frame_to_process = frame.copy()

        boxes, scores = detector.detect_one(frame)

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                w = x2 - x1
                h = y2 - y1
                cx = x1 + w // 2
                cy = y1 + h // 2

                half_w = int(w * (1 + offset_ratio) / 2)
                half_h = int(h * (1 + offset_ratio) / 2)

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

        if capture_trigger:
            if boxes is not None and len(boxes) > 0:
                boxes_list = boxes.tolist() if isinstance(boxes, np.ndarray) else list(boxes)
                scores_list = scores.tolist() if isinstance(scores, np.ndarray) else list(scores)
                best_idx = scores_list.index(max(scores_list))
                best_box = boxes_list[best_idx]

                with lock:
                    cropped_face = crop_with_offset(frame_to_process, best_box, offset_ratio)

                if cropped_face.size > 0:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    photo_path = os.path.join(save_dir, f"{timestamp}.jpg")
                    cv2.imwrite(photo_path, cropped_face)
                    print(f"Captured photo saved: {photo_path}")

                    print("\nRunning verification against database...")
                    verify_against_database(cropped_face)

            capture_trigger = False

    cap.release()
    cv2.destroyAllWindows()
    print("Detection thread stopped.")


def trigger_capture():
    global capture_trigger, rotation_count

    while True:
        cmd = input("Type ENTER to capture photo, 'rotate' to rotate feed, or 'quit' to exit:\n").strip().lower()
        if cmd == 'quit':
            break
        elif cmd == 'rotate':
            with lock:
                rotation_count = (rotation_count + 1) % 4
                if rotation_count % 2 == 1:
                    window_width, window_height = l1, l2
                else:
                    window_width, window_height = l2, l1
                cv2.resizeWindow('DroidCam - Face Detection', window_width, window_height)
            print(f"Rotation changed. Now rotating {rotation_count * 90} degrees clockwise.")
        else:
            with lock:
                capture_trigger = True

def main(default_ip="172.17.72.186", default_port="4747"):
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

    trigger_capture()

if __name__ == "__main__":
    main()
