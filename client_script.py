# laptop_overlay_client.py
import cv2
import json
import numpy as np
import socket
import time
from typing import Tuple

# --- CHANGE THIS TO YOUR JETSON IP ---
JETSON_IP = ""
PORT = 5005

# Define Panel Colors & Accents
FONT = cv2.FONT_HERSHEY_DUPLEX
ACCENT_COLOR = (80, 220, 80)
PANEL_COLOR = (15, 15, 15)
TEXT_COLOR = (235, 235, 235)
HEART_PULSE_COLOR = (80, 220, 80)
# Set this to the Xreal resolution as macOS reports it (often 1920x1080)
DISPLAY_W, DISPLAY_H = 1920, 1080
EDGE_SHIFT, UP_SHIFT =-650, -700

# Connect to Jetson
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((JETSON_IP, PORT))
sock_file = sock.makefile("r")  # allows line-by-line reading 

window_name = "xreal_overlay"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
# Let macOS handle actual full-screen; we just make the window resizable

def _draw_rounded_rect(img: np.ndarray, top_left: Tuple[int, int], size: Tuple[int, int],
                       color: Tuple[int, int, int], radius: int, thickness: int):
    """Draws a rounded rectangle using rectangles + circles for consistent corners."""
    x, y = top_left
    w, h = size
    radius = max(0, min(radius, w // 2, h // 2))
    if radius == 0:
        cv2.rectangle(img, (x, y), (x + w, y + h), color, thickness, lineType=cv2.LINE_AA)
        return
    if thickness <= 0 or thickness == cv2.FILLED:
        cv2.rectangle(img, (x + radius, y), (x + w - radius, y + h), color, cv2.FILLED)
        cv2.rectangle(img, (x, y + radius), (x + w, y + h - radius), color, cv2.FILLED)
        for cx, cy in (
            (x + radius, y + radius),
            (x + w - radius, y + radius),
            (x + w - radius, y + h - radius),
            (x + radius, y + h - radius),
        ):
            cv2.circle(img, (cx, cy), radius, color, cv2.FILLED, lineType=cv2.LINE_AA)
    else:
        cv2.line(img, (x + radius, y), (x + w - radius, y), color, thickness, lineType=cv2.LINE_AA)
        cv2.line(img, (x + radius, y + h), (x + w - radius, y + h), color, thickness, lineType=cv2.LINE_AA)
        cv2.line(img, (x, y + radius), (x, y + h - radius), color, thickness, lineType=cv2.LINE_AA)
        cv2.line(img, (x + w, y + radius), (x + w, y + h - radius), color, thickness, lineType=cv2.LINE_AA)
        cv2.ellipse(img, (x + radius, y + radius), (radius, radius), 0, 180, 270, color, thickness, lineType=cv2.LINE_AA)
        cv2.ellipse(img, (x + w - radius, y + radius), (radius, radius), 0, 270, 360, color, thickness, lineType=cv2.LINE_AA)
        cv2.ellipse(img, (x + w - radius, y + h - radius), (radius, radius), 0, 0, 90, color, thickness, lineType=cv2.LINE_AA)
        cv2.ellipse(img, (x + radius, y + h - radius), (radius, radius), 0, 90, 180, color, thickness, lineType=cv2.LINE_AA)

def _blend_panel(canvas: np.ndarray, top_left: Tuple[int, int], size: Tuple[int, int], alpha=0.65, corner_radius=18):
    x, y = top_left
    w, h = size
    overlay = canvas.copy()
    _draw_rounded_rect(overlay, (x, y), (w, h), PANEL_COLOR, corner_radius, cv2.FILLED)
    cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)
    _draw_rounded_rect(canvas, (x, y), (w, h), (60, 60, 60), corner_radius, 1)
    return x, y, w, h

def _format_coord(value: float, axis: str) -> str:
    if value is None:
        return "--.--°"
    direction = "N" if axis == "lat" and value >= 0 else \
                "S" if axis == "lat" else \
                "E" if value >= 0 else "W"
    return f"{abs(value):.2f} {direction}"

def get_patient_status(hr: int):
    if hr <= 0: return "Awaiting vitals", "No confirmed pulse", (120,120,120)
    if hr < 45: return "Critical Condition", "Begin stabilization", (0,0,255)
    if hr < 50: return "Critical - Bradycardia", "Begin stabilization", (0,0,255)
    if hr < 60: return "Low", "Monitor closely", (0,140,255)
    if hr <= 100: return "Stable", "Maintain support", (50,200,120)
    if hr <= 120: return "Elevated", "Assess exertion", (0,165,255)
    return "Critical - Tachycardia", "Administer care", (0,0,255)

def _heartbeat_pulse_value(heart_rate: int) -> float:
    """
    Returns a normalized value [0,1] describing the current pulse magnitude
    for animating the heartbeat indicator.
    """
    if heart_rate <= 0:
        return 0.0
    # Convert BPM to Hz and use current time to keep animation in sync.
    freq_hz = heart_rate / 60.0
    phase = time.time() * freq_hz * 2 * np.pi
    return (np.sin(phase) + 1.0) / 2.0

def draw_gps_widget(canvas: np.ndarray, lat, lon):
    x, y, _, _ = _blend_panel(canvas, (40, 40), (380, 170))
    fix = "GPS LOCKED"
    # sats = gps.get("satellites", 8)

    cv2.putText(canvas, "SEARCH GPS", (x + 20, y + 35), FONT, 0.7, ACCENT_COLOR, 2, lineType=cv2.LINE_AA)
    # draw circular graphic
    icon_center = (x + 60, y + 90)
    cv2.circle(canvas, icon_center, 30, ACCENT_COLOR, 2, lineType=cv2.LINE_AA)
    cv2.circle(canvas, icon_center, 6, ACCENT_COLOR, cv2.FILLED, lineType=cv2.LINE_AA)
    cv2.line(canvas, (icon_center[0], icon_center[1] - 30), (icon_center[0], icon_center[1] + 30), ACCENT_COLOR, 1, lineType=cv2.LINE_AA)
    cv2.line(canvas, (icon_center[0] - 30, icon_center[1]), (icon_center[0] + 30, icon_center[1]), ACCENT_COLOR, 1, lineType=cv2.LINE_AA)

    cv2.putText(canvas, f"LAT  {_format_coord(lat, 'lat')}", (x + 120, y + 85), FONT, 0.6, TEXT_COLOR, 1, lineType=cv2.LINE_AA)
    cv2.putText(canvas, f"LON  {_format_coord(lon, 'lon')}", (x + 120, y + 115), FONT, 0.6, TEXT_COLOR, 1, lineType=cv2.LINE_AA)
    # cv2.putText(canvas, f"{fix} | {sats} SATS", (x + 20, y + 150), FONT, 0.55, (180, 180, 180), 1, lineType=cv2.LINE_AA)

def draw_heart_widget(canvas, heart_rate, top_left):
    x, y, _, _ = _blend_panel(canvas, top_left, (260, 140))
    cv2.putText(canvas, "HEART RATE", (x + 20, y + 35), FONT, 0.55, (180,180,180), 1, lineType=cv2.LINE_AA)
    cv2.putText(canvas, f"{heart_rate:>3} BPM", (x + 20, y + 90), FONT, 1, TEXT_COLOR, 2, lineType=cv2.LINE_AA)
    # pulse indicator circle
    pulse_value = _heartbeat_pulse_value(heart_rate)
    circle_center = (x + 200, y + 80)
    base_radius = 12
    pulse_radius = base_radius + int(8 * pulse_value)
    cv2.circle(canvas, circle_center, base_radius + 12, (70, 70, 70), 1, lineType=cv2.LINE_AA)
    cv2.circle(canvas, circle_center, pulse_radius, HEART_PULSE_COLOR, cv2.FILLED, lineType=cv2.LINE_AA)

def draw_status_widget(canvas, heart_rate, top_left):
    x, y, _, _ = _blend_panel(canvas, top_left, (260, 140))
    title, detail, color = get_patient_status(heart_rate)
    cv2.putText(canvas, "PATIENT STATUS", (x + 20, y + 35), FONT, 0.55, (180,180,180), 1, lineType=cv2.LINE_AA)
    cv2.putText(canvas, title.upper(), (x + 20, y + 80), FONT, 0.65, color, 2, lineType=cv2.LINE_AA)
    cv2.putText(canvas, detail, (x + 20, y + 115), FONT, 0.55, TEXT_COLOR, 1, lineType=cv2.LINE_AA)

while True:
    line = sock_file.readline()
    if not line:
        break  # Jetson closed connection

    try:
        data = json.loads(line.strip())
    except json.JSONDecodeError:
        continue

    boxes = data.get("boxes", [])
    
    # frame_b64 = data.get("frame", None)
    # if frame_b64:
    #     img_bytes = base64.b64decode(frame_b64)
    #     img_np = np.frombuffer(img_bytes, dtype=np.uint8)
    #     frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)  # or IMREAD_GRAYSCALE
        
    # if frame is not None:
    #     cv2.imshow(window_name, frame)
    #     if cv2.waitKey(1) & 0xFF == 27:
    #         break
   

    # 1) Make a PURE BLACK image (this is why the window is black)
    canvas = np.zeros((DISPLAY_H, DISPLAY_W, 3), dtype=np.uint8)
    
    # heart_rate = data.get("heart_rate", 0)
    # cv2.putText(canvas, f"Heart Rate: {heart_rate}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    lon = data.get("lon", 0)
    lat = data.get("lat", 0)
    heart_rate = data.get("heart_rate", 0)
    
    draw_gps_widget(canvas, lat, lon)
    right_x = DISPLAY_W - 300
    if heart_rate > 0:
        draw_status_widget(canvas, heart_rate, (right_x, 210))
        draw_heart_widget(canvas, heart_rate, (right_x, 40))
    else:
        draw_status_widget(canvas, heart_rate, (right_x, 40))

    # 2) Draw bright white boxes where people are
    for b in boxes:
        # coords are normalized [0,1]; scale up
        x1 = int(b["x1"] * DISPLAY_W) + EDGE_SHIFT
        y1 = int(b["y1"] * DISPLAY_H) + UP_SHIFT
        x2 = int(b["x2"] * DISPLAY_W) + EDGE_SHIFT
        y2 = int(b["y2"] * DISPLAY_H) + UP_SHIFT

        cv2.rectangle(canvas, (x1, y1), (x2, y2), (255, 255, 255), thickness=4)

    # 3) Show the canvas in the window
    cv2.imshow(window_name, canvas)

    # ESC to quit
    if cv2.waitKey(1) & 0xFF == 27:
        break

sock.close()
cv2.destroyAllWindows()
