## Stanford XR Overlay - README

### License
- This project is licensed under the MIT License. See `LICENSE`.

### Packages Used
- OpenCV (`opencv-python`)
- NumPy (`numpy`)

Optional/Helpful (not required by the current scripts):
- Ultralytics (`ultralytics`) for YOLO which is integrated, but not actively used.

### Assets and Hardware
- Xreal glasses (black pixels appear transparent on display)
- IR camera (e.g., FLIR Boson or other UVC-compatible thermal camera)
- No media assets are committed to the repository

### Networking Configuration
- The system establishes a TCP connection between the Jetson (server) and the client laptop.
- **Port**: Default port is `5005` (can be changed in both scripts).
- **IP Address Setup**:
  - Both `jetson_script.py` and `client_script.py` need the Jetson's IP address configured.
  - Update `JETSON_IP` in both files to match the Jetson's network IP.

- **Network Requirements**:
  - Both devices must be on the same network (WiFi or Ethernet).
  - Make sure firewall rules allow TCP connections on port 5005.
  - The Jetson hosts the server (`jetson_script.py`) and waits for the client to connect.
  - The client laptop (`client_script.py`) connects to the Jetson server.
  - 
### AI Tools
- None currently integrated.

### Notes
- Display resolution defaults to `1920x1080` for the overlay window. Adjust in the script if your system reports a different resolution for the Xreal display.


