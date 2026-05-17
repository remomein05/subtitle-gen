# Subtitle Gen 🎥 📝

An AI-powered, local-first video transcription tool that generates SRT subtitles directly on your machine. No cloud, no uploads, total privacy.

## ✨ Features
- **Local AI Processing:** Uses `faster-whisper` (Ctranslate2) for high-efficiency transcription.
- **Multilingual Support:** Works with 99+ languages, including Tamil, English, Spanish, etc.
- **Optimized for CPU:** Fine-tuned thread allocation and Greedy Search for fast performance on standard processors.
- **Privacy Guaranteed:** Your videos never leave your computer.
- **Modern UI:** Built with Tauri, React, and Tailwind CSS 4 for a smooth, "macOS-like" aesthetic with blurred backgrounds and animations.
- **Real-time Feedback:** Watch the `.srt` file grow in your folder as the AI transcribes.

---

## 🛠️ Technical Overview
- **Frontend:** React 19, TypeScript, Tailwind CSS 4, Framer Motion, Lucide Icons.
- **Backend (App):** Tauri v2 (Rust) manages the windowing and sidecar communication.
- **Engine (AI):** Python-based sidecar using `faster-whisper`.
- **Optimization:** 
  - **VAD (Voice Activity Detection):** Automatically skips silent parts of the video to save CPU cycles.
  - **Greedy Search:** Uses `beam_size=1` for maximum speed without significant accuracy loss on clear audio.
  - **Process Safety:** Implements `PR_SET_PDEATHSIG` (Linux) and stdin monitoring to ensure the AI engine exits if the app crashes.

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

1.  **Rust & Cargo:** Required for building the Tauri app. [Install Rust](https://rustup.rs/).
2.  **Node.js (v18+):** Required for the frontend.
3.  **Python (3.9 - 3.12):** Required to build/run the AI engine.
4.  **FFmpeg:** Essential for the audio extraction process.
    - **Linux:** `sudo pacman -S ffmpeg` (Arch) or `sudo apt install ffmpeg` (Ubuntu).
    - **macOS:** `brew install ffmpeg`.
    - **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

---

## 🚀 Getting Started

### 1. Set up the Engine (AI Sidecar)
```bash
cd engine
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
# To build the binary used as a sidecar:
pyinstaller engine.spec --clean
```

### 2. Set up the UI
```bash
cd ../ui
npm install
```

### 3. Launch the App
```bash
npm run tauri dev
```

---

## 🐧 OS Specific Notes

### Arch Linux / NVIDIA Users (Wayland)
If you encounter a blank window or protocol errors on Arch with NVIDIA, use the following launch command:
```bash
WEBKIT_DISABLE_DMABUF_RENDERER=1 GDK_BACKEND=x11 npm run tauri dev
```

### Windows
Ensure that **C++ Build Tools** are installed via the Visual Studio Installer, as they are required for both Rust and some Python wheels.

### macOS
The app supports both Intel and Apple Silicon. Ensure you have granted "Full Disk Access" or "Accessibility" permissions if the file dialog doesn't appear.

---

## 📝 License
MIT License - Feel free to use and modify for your own projects!
