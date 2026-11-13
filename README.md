# Video Compressor Pro 🚀
**أداة ضغط المحاضرات الاحترافية**

Developed by: **Eng. Fares Kuliab** © 2026

Video Compressor Pro is a powerful, user-friendly Windows application built with Python and `CustomTkinter`. It utilizes the power of `FFmpeg` to compress, edit, merge, and process video files efficiently. It is specifically optimized for educational lectures, offering massive file size reduction without losing text clarity.

---

## ✨ Features (المميزات)
* **Bilingual UI**: Fully supports Arabic (RTL) and English languages.
* **Drag & Drop**: Easily add multiple videos by dragging them into the app.
* **Smart Compression Modes**: 
  * *Balanced Mode*: For standard video lectures.
  * *Board Mode*: Extreme compression optimized for whiteboards/text.
  * *Audio Extraction*: Convert video directly to MP3.
* **Hardware Acceleration**: Supports CPU, NVIDIA (NVENC), and AMD (AMF) for lightning-fast processing.
* **Advanced Editing Tools**:
  * Trim start/end times.
  * Cut out middle sections.
  * Crop video frame edges.
  * Add custom Text and Image Watermarks with positioning.
  * Rotate videos.
* **Video Merging**: Ultra-fast video merging using FFmpeg concat demuxer.
* **Post-Processing Actions**: Automatically put the PC to sleep or shut it down after tasks are finished.

---

## 🛠️ Requirements & Installation (المتطلبات والتثبيت للمطورين)

If you want to run the source code directly, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YourUsername/Video-Compressor-Pro.git
   cd Video-Compressor-Pro
   ```

2. **Install Python dependencies:**
   ```bash
   pip install customtkinter tkinterdnd2 psutil arabic-reshaper python-bidi
   ```

3. **FFmpeg Setup:**
   * Download `ffmpeg.exe` and `ffprobe.exe` for Windows.
   * Place both `.exe` files in the root directory of this project (next to `main.py`).

4. **Run the App:**
   ```bash
   python main.py
   ```

---

## 📦 Building the Executable (تحويل الكود إلى برنامج Windows)

To build the standalone `.exe` using PyInstaller, run:
```bash
pyinstaller --noconsole --onedir --windowed --icon=app_icon.ico --add-data "ffmpeg.exe;." --add-data "ffprobe.exe;." --add-data "app_icon.ico;." --collect-all tkinterdnd2 --collect-all customtkinter main.py
```
After building, you can use **Inno Setup** with the included `.iss` script to create a professional installer (`Setup.exe`).

---

## 📄 License (الرخصة)
This software is developed by Eng. Fares Kuliab. All rights reserved. 
For contact: +967 772626216 - +967 738689628 (Yemen).
