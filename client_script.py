# laptop_overlay_client.py
import cv2
import json
import numpy as np
import socket

# --- CHANGE THIS TO YOUR JETSON IP ---
JETSON_IP = "10.31.51.74"   # example; use your actual Jetson IP
PORT = 5005

# Set this to the Xreal resolution as macOS reports it (often 1920x1080)
DISPLAY_W, DISPLAY_H = 1920, 1080

# Connect to Jetson
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((JETSON_IP, PORT))
sock_file = sock.makefile("r")  # allows line-by-line reading 

window_name = "xreal_overlay"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
# Let macOS handle actual full-screen; we just make the window resizable

while True:
    line = sock_file.readline()
    if not line:
        break  # Jetson closed connection

    try:
        data = json.loads(line.strip())
    except json.JSONDecodeError:
        continue

    boxes = data.get("boxes", [])

    # 1) Make a PURE BLACK image (this is why the window is black)
    canvas = np.zeros((DISPLAY_H, DISPLAY_W, 3), dtype=np.uint8)

    # 2) Draw bright white boxes where people are
    for b in boxes:
        # coords are normalized [0,1]; scale up
        x1 = int(b["x1"] * DISPLAY_W)
        y1 = int(b["y1"] * DISPLAY_H)
        x2 = int(b["x2"] * DISPLAY_W)
        y2 = int(b["y2"] * DISPLAY_H)

        cv2.rectangle(canvas, (x1, y1), (x2, y2), (255, 255, 255), thickness=4)

    # 3) Show the canvas in the window
    cv2.imshow(window_name, canvas)

    # ESC to quit
    if cv2.waitKey(1) & 0xFF == 27:
        break

sock.close()
cv2.destroyAllWindows()
