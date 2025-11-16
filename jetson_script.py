# jetson_detect_server.py
import cv2
import json
import socket
import random
import numpy as np
import base64
import threading
import re
import time
import os
import glob
try:
    import serial  # pyserial
except ImportError:
    serial = None
import requests
from ultralytics import YOLO

JETSON_IP = "10.31.51.74"      # listen on all interfaces
# JETSON_IP = "192.168.55.1"
PORT = 5005                # pick any open port
CONF_THRESH = 0.1  #Threshold for YOLO

CAM_INDEX = 0     # Boson typically appears as /dev/video2
HEAT_THRESH = 200         # grayscale threshold (0-255) for hot regions
MIN_AREA = 1000             # min contour area (pixels) to keep



# model = YOLO("yolov8n.pt") 

cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_V4L2)
if not cap.isOpened():
    raise RuntimeError("Could not open IR camera")

def get_heart_rate(wait_seconds=0.5):
    if serial is None:
        raise RuntimeError("pyserial not installed. Install with: pip install pyserial")
    # Try to choose a likely serial device
    env_port = os.getenv("ESP_SERIAL_PORT")
    candidate_ports = []
    if env_port:
        candidate_ports.append(env_port)
    try:
        candidate_ports.extend(sorted(glob.glob("/dev/serial/by-id/*")))
    except Exception:
        pass
    candidate_ports.extend([
        "/dev/ttyUSB0",
        "/dev/ttyACM0",
    ])
    try:
        candidate_ports.extend(sorted(glob.glob("/dev/ttyUSB*")))
        candidate_ports.extend(sorted(glob.glob("/dev/ttyACM*")))
    except Exception:
        pass
    # Open first available port and read the next numeric value
    for dev in candidate_ports:
        if not os.path.exists(dev):
            continue
        try:
            ser = serial.Serial(dev, 115200, timeout=0.2)
        except Exception:
            continue
        try:
            end_time = time.time() + max(0.1, float(wait_seconds))
            while time.time() < end_time:
                try:
                    line_bytes = ser.readline()
                except Exception:
                    break
                if not line_bytes:
                    continue
                try:
                    line = line_bytes.decode("utf-8", errors="ignore").strip()
                except Exception:
                    continue
                m = re.search(r"(-?\d+(?:\.\d+)?)", line)
                if m:
                    val = m.group(1)
                    try:
                        return int(val) if "." not in val else float(val)
                    except Exception:
                        continue
        finally:
            try:
                ser.close()
            except Exception:
                pass
    return None
    
def get_geoloc():
    # Previous (invalid inside Python):
    # curl -X POST "https://www.googleapis.com/geolocation/v1/geolocate?key=YOUR_KEY" \
    #   -H "Content-Type: application/json" \
    #   -d '{ "considerIp": true }'
    try:
        url = "https://www.googleapis.com/geolocation/v1/geolocate"
        params = {
            "key": "AIzaSyAW_bSqKvV8sI4WcwLZef9trbR6rWiYvok"
        }
        # Minimal payload: let Google use IP; add wifiAccessPoints/cellTowers if desired
        payload = {
            "considerIp": True
        }
        resp = requests.post(url, params=params, json=payload, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        loc = data.get("location", {})
        return {
            "lat": loc.get("lat"),
            "lng": loc.get("lng"),
            "accuracy": data.get("accuracy")
        }
    except Exception as e:
        return {"error": str(e)}




# Simple TCP server
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind((JETSON_IP, PORT))
server_sock.listen(1)
print(f"Waiting for client on port {PORT}...")
conn, addr = server_sock.accept()
print(f"Client connected from {addr}")

iteration = 0
lon, lat, accuracy = 0,0,0
heart_rate = 0

while True:
    iteration += 1
    ret, frame = cap.read()
    if not ret:
        break



    h, w = frame.shape[:2]
    # YOLO path (commented per request)
    # results = model(frame, verbose=False)[0]
    # boxes_out = []
    # for box in results.boxes:
    #     cls = int(box.cls[0])
    #     conf = float(box.conf[0])
    #     if model.names[cls] != "person" or conf < CONF_THRESH:
    #         continue
    #     x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
    #     boxes_out.append({
    #         "x1": x1 / w,  # send normalized coords 0–1
    #         "y1": y1 / h,
    #         "x2": x2 / w,
    #         "y2": y2 / h,
    #         "conf": conf
    #     })

    # Heat-blob detection (threshold + contours)
    if len(frame.shape) == 2 or (len(frame.shape) == 3 and frame.shape[2] == 1):
        gray = frame if len(frame.shape) == 2 else frame[:, :, 0]
    else:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, mask = cv2.threshold(gray_blur, HEAT_THRESH, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes_out = []
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        area = cv2.contourArea(cnt)
        if area < MIN_AREA:
            continue
        roi = gray[y:y+bh, x:x+bw]
        conf = float(np.clip(roi.mean() / 255.0, 0.0, 1.0)) if roi.size else 0.0
        boxes_out.append({
            "x1": x / w,
            "y1": y / h,
            "x2": (x + bw) / w,
            "y2": (y + bh) / h,
            "conf": conf
        })

    if iteration <= 1 or iteration % 30 == 0:
        vals = get_geoloc()
        lon = vals.get("lng")
        lat = vals.get("lat")
        accuracy = vals.get("accuracy")
  
    heart_rate = get_heart_rate()
    msg = json.dumps({
        "boxes": boxes_out,
        "heart_rate": heart_rate,
        "lon": lon,
        "lat": lat,
        "accuracy": accuracy,
    }) + "\n"
    try:
        conn.sendall(msg.encode("utf-8"))
    except BrokenPipeError:
        print("Client disconnected")
        break

cap.release()
conn.close()
server_sock.close()
