import cv2
import numpy as np
import mediapipe as mp
import pyautogui
import time
import sys

# --- 1. TIZIM YO'LLARI ---
anaconda_path = r'C:\Users\avazb\anaconda3\Lib\site-packages'
if anaconda_path not in sys.path:
    sys.path.insert(0, anaconda_path)

# --- 2. MEDIAPIPE SOZLAMALARI ---
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7)

# --- 3. EKRAN VA DINAMIK TEZLIK ---
SCREEN_W, SCREEN_H = pyautogui.size()
SMOOTH_FACTOR = 0.4  # Silliq harakat
prev_x, prev_y = SCREEN_W // 2, SCREEN_H // 2

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

# --- 4. CLICK LOGIKASI (MUKAMMAL) ---
last_click_time = 0
click_count = 0
DOUBLE_CLICK_DELAY = 0.4 # Ikki click orasidagi maksimal vaqt
pinch_active = False    # Barmoqlar hozir yopiqmi?

last_alt_tab_time = 0
last_win_tab_time = 0

def get_dist(p1, p2):
    return np.hypot(p1.x - p2.x, p1.y - p2.y)

def count_fingers(hand_lms):
    fingers = []
    if hand_lms.landmark[4].x < hand_lms.landmark[3].x: fingers.append(1)
    else: fingers.append(0)
    tips = [8, 12, 16, 20]
    for tip in tips:
        if hand_lms.landmark[tip].y < hand_lms.landmark[tip - 2].y: fingers.append(1)
        else: fingers.append(0)
    return sum(fingers)

# --- 5. ASOSIY SIKL ---
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Double Click optimallashtirilgan tizim ishga tushdi.")

while cap.isOpened():
    success, frame = cap.read()
    if not success: break
    
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    current_time = time.time()
    hands_count = 0
    total_fingers = 0

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            hands_count += 1
            f_count = count_fingers(hand_lms)
            total_fingers += f_count
            mp_draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)

            if hands_count == 1:
                thumb = hand_lms.landmark[4]
                index = hand_lms.landmark[8]
                middle = hand_lms.landmark[12]
                ring = hand_lms.landmark[16]
                pinky = hand_lms.landmark[20]

                # A. WIN + TAB (Bosh + Nomsiz)
                if get_dist(thumb, ring) < 0.045:
                    if (current_time - last_win_tab_time) > 1.0:
                        pyautogui.hotkey('win', 'tab')
                        last_win_tab_time = current_time
                    continue

                # B. ALT + TAB (Bosh + O'rta)
                if get_dist(thumb, middle) < 0.045:
                    if (current_time - last_alt_tab_time) > 0.8:
                        pyautogui.hotkey('alt', 'tab')
                        last_alt_tab_time = current_time
                    continue

                # C. DOUBLE CLICK VA SINGLE CLICK (Bosh + Ko'rsatkich)
                dist_pinch = get_dist(thumb, index)
                
                # Barmoqlar bir-biriga tegdi (Pinch boshlandi)
                if dist_pinch < 0.040:
                    if not pinch_active:
                        pinch_active = True
                
                # Barmoqlar ochildi (Click event sodir bo'ldi)
                elif dist_pinch > 0.055:
                    if pinch_active:
                        pinch_active = False
                        
                        # Double clickni tekshirish
                        if (current_time - last_click_time) < DOUBLE_CLICK_DELAY:
                            pyautogui.doubleClick()
                            cv2.putText(frame, "DOUBLE CLICK", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
                            last_click_time = 0 # Double clickdan so'ng vaqtni nolga tushirish
                        else:
                            pyautogui.click()
                            cv2.putText(frame, "CLICK", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            last_click_time = current_time

                # D. HARAKAT (Faqat barmoqlar ochiq bo'lganda)
                # [0.35, 0.65] oralig'i - juda sezgir (kichik harakatda katta masofa)
                if f_count >= 4:
                    tx = np.interp(index.x, [0.35, 0.65], [0, SCREEN_W])
                    ty = np.interp(index.y, [0.35, 0.65], [0, SCREEN_H])
                    
                    curr_x = prev_x + (tx - prev_x) * SMOOTH_FACTOR
                    curr_y = prev_y + (ty - prev_y) * SMOOTH_FACTOR
                    
                    pyautogui.moveTo(curr_x, curr_y)
                    prev_x, prev_y = curr_x, curr_y

                # E. O'NG TUGMA (Bosh + Jimjiloq)
                if get_dist(thumb, pinky) < 0.045:
                    pyautogui.rightClick()
                    time.sleep(0.3)

                # F. SCROLL (Musht)
                if f_count <= 1:
                    if index.y < 0.5: pyautogui.scroll(80)
                    else: pyautogui.scroll(-80)

        # G. DESKTOP (Ikkala qo'l)
        if hands_count == 2 and total_fingers >= 9:
            pyautogui.hotkey('win', 'd')
            time.sleep(1)

    cv2.imshow('Avazbek Ultimate Control v6.0', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()