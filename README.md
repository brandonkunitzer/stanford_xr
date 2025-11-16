## Stanford XR Overlay - README

### License
- This project is licensed under the MIT License. See `LICENSE`.

### Packages Used
- OpenCV (`opencv-python`)
- NumPy (`numpy`)

Optional/Helpful (not required by the current scripts):
- FFmpeg (device listing and media tooling)
- imagesnap (macOS camera listing via Homebrew)
- Ultralytics (`ultralytics`) for YOLO, if you later add IR detection

### Assets and Hardware
- Xreal glasses (black pixels appear transparent on display)
- IR camera (e.g., FLIR Boson or other UVC-compatible thermal camera)
- No media assets are committed to the repository

### AI Tools
- None currently integrated.
- Planned/optional: YOLO (via Ultralytics) for person/hotspot detection on IR frames.

### Notes
- Display resolution defaults to `1920x1080` for the overlay window. Adjust in the script if your system reports a different resolution for the Xreal display.
- Camera index on macOS may require AVFoundation and permissions:
  - System Settings → Privacy & Security → Camera → enable for Terminal/IDE.
  - List cameras (optional): `ffmpeg -f avfoundation -list_devices true -i ""`.


