import sys
import os
import json
import ffmpeg
from faster_whisper import WhisperModel
import datetime
import multiprocessing
import signal
import time

# Global state for cleanup
TEMP_AUDIO_PATH = None

def format_timestamp(seconds: float):
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def log_progress(status, progress=0, message=""):
    print(json.dumps({"status": status, "progress": progress, "message": message}), flush=True)

def cleanup():
    global TEMP_AUDIO_PATH
    if TEMP_AUDIO_PATH and os.path.exists(TEMP_AUDIO_PATH):
        try:
            os.remove(TEMP_AUDIO_PATH)
        except:
            pass

def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def transcribe(video_path):
    global TEMP_AUDIO_PATH
    try:
        if not os.path.exists(video_path):
            log_progress("error", message=f"File not found: {video_path}")
            return

        base_path = os.path.splitext(video_path)[0]
        TEMP_AUDIO_PATH = base_path + ".temp.wav"
        srt_path = base_path + ".srt"

        log_progress("extracting_audio", progress=10, message="Extracting audio...")
        
        # Extract audio using ffmpeg
        (
            ffmpeg
            .input(video_path)
            .output(TEMP_AUDIO_PATH, ac=1, ar='16k')
            .overwrite_output()
            .run(quiet=True)
        )

        log_progress("loading_model", progress=30, message="Loading Whisper model...")
        
        cpu_cores = multiprocessing.cpu_count()
        physical_cores = cpu_cores // 2 if cpu_cores > 4 else cpu_cores
        
        try:
            model_size = "base"
            model = WhisperModel(
                model_size, 
                device="cpu", 
                compute_type="float32",
                cpu_threads=physical_cores,
                num_workers=1,
                download_root=os.path.join(os.path.expanduser("~"), ".cache", "whisper-models")
            )
        except Exception as load_error:
            log_progress("error", message=f"Model Load Error: {str(load_error)}")
            return

        log_progress("transcribing", progress=50, message="Transcribing...")
        
        # Generator for transcription segments
        segments, info = model.transcribe(
            TEMP_AUDIO_PATH, 
            beam_size=1, 
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        log_progress("processing", progress=70, message=f"Detected language '{info.language}'")

        # Open file and write/flush every segment for real-time visibility
        with open(srt_path, "w", encoding="utf-8") as srt_file:
            for i, segment in enumerate(segments, start=1):
                start = format_timestamp(segment.start)
                end = format_timestamp(segment.end)
                srt_file.write(f"{i}\n{start} --> {end}\n{segment.text.strip()}\n\n")
                srt_file.flush() # Force write to disk so user sees growth
                os.fsync(srt_file.fileno()) # Ensure OS flushes buffer

        log_progress("cleaning_up", progress=90, message="Cleaning up...")
        cleanup()

        log_progress("completed", progress=100, message=f"Subtitle saved to {srt_path}")

    except Exception as e:
        log_progress("error", message=str(e))
        cleanup()

if __name__ == "__main__":
    # Handle parent death on Linux
    if sys.platform.startswith('linux'):
        try:
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            libc.prctl(1, 15)
        except Exception:
            pass

    multiprocessing.freeze_support()
    
    video_path = None
    for arg in sys.argv[1:]:
        if not arg.startswith('-') and not ("import" in arg or "main(" in arg) and os.path.exists(arg):
            video_path = arg
            break
    
    if video_path:
        log_progress("started", message="Engine started successfully")
        transcribe(video_path)
    elif len(sys.argv) > 1 and not ("import" in sys.argv[1] or "main(" in sys.argv[1]):
        pass
