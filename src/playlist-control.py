import os
import urllib.request
import cv2
import numpy as np
import mediapipe as mp
import time
import math
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from pynput.keyboard import Key, Controller

# --- 1. SETUP KEYBOARD EMULATION ---
keyboard = Controller()

# --- 2. SETUP MEDIAPIPE TASKS API ---
model_filename = 'hand_landmarker.task'
if not os.path.exists(model_filename):
    print("Downloading AI core vision model...")
    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/float16/1/hand_landmarker.task"
    urllib.request.urlretrieve(url, model_filename)

base_options = python.BaseOptions(model_asset_path=model_filename)
options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
detector = vision.HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)

# 3. ADVANCED TRANSITION VALIDATION COUNTERS
current_gesture = "NONE"
last_execution_time = 0

# Active frame persistence memory states
gesture_frame_counters = {
    "SNAP_PAUSE": 0,
    "POINTER_RIGHT": 0,
    "POINTER_LEFT": 0,
    "GUN_UP": 0,
    "GUN_DOWN": 0
}

# HOW MANY CONSECUTIVE FRAMES A GESTURE MUST BE HELD BEFORE IT FIRES
# Skips/Snaps need a safe hold buffer. Volume can remain lower for rapid response.
REQUIRED_HOLD_FRAMES = {
    "SNAP_PAUSE": 2,      # Fast activation for snappy response
    "POINTER_RIGHT": 4,   # 4 Frames (~0.13s) perfectly filters out the snap transition glitch!
    "POINTER_LEFT": 4,    # Filters out accidental left movements
    "GUN_UP": 2,          # Keep responsive for fast continuous scrolling
    "GUN_DOWN": 2
}

VOLUME_COOLDOWN = 0.15 
TRACK_COOLDOWN = 1.2   

print("\nValidation Hold Engine Active. Anti-glitch frame checks deployed.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    results = detector.detect(mp_image)
    
    hud_command = "GUARD ACTIVE (FILTERING INPUTS)"
    
    def draw_skeleton_tasks(image, landmarks):
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
            (0, 17), (17, 13), (13, 9), (9, 5), (17, 18), (18, 19), (19, 20),
            (13, 14), (14, 15), (15, 16), (9, 10), (10, 11), (11, 12)
        ]
        for conn in connections:
            cv2.line(image, (int(landmarks[conn[0]].x * w), int(landmarks[conn[0]].y * h)), 
                            (int(landmarks[conn[1]].x * w), int(landmarks[conn[1]].y * h)), (255, 255, 0), 2, cv2.LINE_AA)

    if results.hand_landmarks:
        hand_landmarks = results.hand_landmarks[0]
        draw_skeleton_tasks(frame, hand_landmarks)
        
        # --- EXTRACT CORE LANDMARKS ---
        t_tip, t_knuckle = hand_landmarks[4], hand_landmarks[2]
        i_tip, i_knuckle = hand_landmarks[8], hand_landmarks[6]
        m_tip, m_knuckle = hand_landmarks[12], hand_landmarks[10]
        
        index_extended  = hand_landmarks[8].y  < hand_landmarks[5].y
        middle_extended = hand_landmarks[12].y < hand_landmarks[9].y
        ring_folded     = hand_landmarks[16].y > hand_landmarks[14].y
        pinky_folded    = hand_landmarks[20].y > hand_landmarks[18].y
        
        dx = i_tip.x - i_knuckle.x
        dy = i_tip.y - i_knuckle.y
        index_angle = math.degrees(math.atan2(dy, dx))
        
        thumb_middle_dist = np.linalg.norm(np.array([t_tip.x, t_tip.y]) - np.array([m_tip.x, m_tip.y]))
        
        # Identify raw frame reading shape
        raw_detected_shape = "NONE"
        
        if thumb_middle_dist < 0.045 and ring_folded and pinky_folded:
            raw_detected_shape = "SNAP_PAUSE"
            
        elif index_extended and middle_extended and ring_folded and pinky_folded:
            if -40 <= index_angle <= 40:
                raw_detected_shape = "POINTER_RIGHT"
            elif index_angle >= 140 or index_angle <= -140:
                raw_detected_shape = "POINTER_LEFT"
                
        elif index_extended and not middle_extended and ring_folded and pinky_folded:
            if -130 <= index_angle <= -50:
                raw_detected_shape = "GUN_UP"
            elif 50 <= index_angle <= 130:
                raw_detected_shape = "GUN_DOWN"

        # --- FRAME ACCUMULATION AND ANOMALY WIPING ---
        validated_shape = "NONE"
        
        for shape_name in gesture_frame_counters.keys():
            if raw_detected_shape == shape_name:
                # Increment continuous frame counter for the active shape
                gesture_frame_counters[shape_name] += 1
                
                # Check if it has passed its specific hold threshold rule
                if gesture_frame_counters[shape_name] >= REQUIRED_HOLD_FRAMES[shape_name]:
                    validated_shape = shape_name
            else:
                # CRITICAL: Instantly drop counter back to zero if shape slips for even 1 frame
                gesture_frame_counters[shape_name] = 0

        # --- EXECUTION HANDLING ROUTINE ---
        current_time = time.time()
        active_cooldown = VOLUME_COOLDOWN if "GUN" in validated_shape else TRACK_COOLDOWN

        if validated_shape != "NONE":
            if validated_shape != current_gesture or (current_time - last_execution_time > active_cooldown):
                current_gesture = validated_shape
                last_execution_time = current_time
                
                if current_gesture == "SNAP_PAUSE":
                    hud_command = "FIRED: [PLAY/PAUSE TOGGLE]"
                    keyboard.press(Key.media_play_pause)
                    keyboard.release(Key.media_play_pause)
                    
                elif current_gesture == "POINTER_RIGHT":
                    hud_command = "FIRED: [MEDIA NEXT]"
                    keyboard.press(Key.media_next)
                    keyboard.release(Key.media_next)
                    
                elif current_gesture == "POINTER_LEFT":
                    hud_command = "FIRED: [MEDIA PREVIOUS]"
                    keyboard.press(Key.media_previous)
                    keyboard.release(Key.media_previous)
                    
                elif current_gesture == "GUN_UP":
                    hud_command = "VOLUME RAMP UP [+]"
                    keyboard.press(Key.media_volume_up)
                    keyboard.release(Key.media_volume_up)
                    
                elif current_gesture == "GUN_DOWN":
                    hud_command = "VOLUME RAMP DOWN [-]"
                    keyboard.press(Key.media_volume_down)
                    keyboard.release(Key.media_volume_down)
            else:
                hud_command = f"VALIDATED HOLDING: [{current_gesture}]"
        else:
            if raw_detected_shape != "NONE":
                hud_command = f"FILTERING TRANSITION: [{raw_detected_shape}] ({gesture_frame_counters[raw_detected_shape]}/{REQUIRED_HOLD_FRAMES[raw_detected_shape]})"

    else:
        current_gesture = "NONE"
        for shape_name in gesture_frame_counters.keys():
            gesture_frame_counters[shape_name] = 0

    # --- ADVANCED RADAR PANEL DISPLAY ---
    cv2.rectangle(frame, (10, h - 60), (470, h - 10), (15, 10, 5), -1)
    cv2.rectangle(frame, (10, h - 60), (470, h - 10), (0, 255, 255), 1)
    
    text_color = (0, 255, 0) if "FIRED" in hud_command or "RAMP" in hud_command else (0, 180, 255) if "FILTERING" in hud_command else (140, 140, 140)
    cv2.putText(frame, f"OS AUDIT CODES: {hud_command}", (25, h - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.40, text_color, 1, cv2.LINE_AA)

    cv2.imshow('Air-Gesture OS Controller v4.0 (Anti-Glitch Engine)', frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
detector.close()
cv2.destroyAllWindows()
