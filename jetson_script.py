# jetson_detect_server.py
import cv2
import json
import socket
# from ultralytics import YOLO

JETSON_IP = "10.31.51.74"      # listen on all interfaces
PORT = 5005                # pick any open port
CONF_THRESH = 0.5

# model = YOLO("ir_person_yolov8n.engine")  # or .pt
# cap = cv2.VideoCapture(0)
# if not cap.isOpened():
#     raise RuntimeError("Could not open IR camera")

# Simple TCP server
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind((JETSON_IP, PORT))
server_sock.listen(1)
print(f"Waiting for client on port {PORT}...")
conn, addr = server_sock.accept()
print(f"Client connected from {addr}")

while True:
    # ret, frame = cap.read()
    # if not ret:
    #     break

    # h, w = frame.shape[:2]
    # results = model(frame, verbose=False)[0]
    # results = []

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
    heart_rate = random.randint(60, 100)
    boxes_out = [{"x1":0.3,"y1":0.3,"x2":0.6,"y2":0.7,"conf":0.9}]
    msg = json.dumps({"boxes": boxes_out, "heart_rate": heart_rate}) + "\n"
    try:
        conn.sendall(msg.encode("utf-8"))
    except BrokenPipeError:
        print("Client disconnected")
        break

cap.release()
conn.close()
server_sock.close()
