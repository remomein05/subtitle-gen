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

def get_download_root():
    return os.path.join(os.path.expanduser("~"), ".cache", "whisper-models")

def is_model_downloaded(model_size):
    """Check if the model files exist in the cache directory."""
    download_root = get_download_root()
    # Faster-whisper models are usually stored in directories named like 'models--Systran--faster-whisper-base'
    # but a simpler way is to check the specific subfolder if we knew the naming convention exactly.
    # However, WhisperModel handles this internally. We can just check if the root has content related to the model.
    # A more reliable check for 'faster-whisper' specifically:
    model_dir = os.path.join(download_root, f"models--Systran--faster-whisper-{model_size}")
    return os.path.exists(model_dir)

def transcribe(video_path, model_size="base"):
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

        log_progress("loading_model", progress=30, message=f"Loading Whisper model '{model_size}'...")
        
        cpu_cores = multiprocessing.cpu_count()
        physical_cores = cpu_cores // 2 if cpu_cores > 4 else cpu_cores
        
        try:
            model = WhisperModel(
                model_size, 
                device="cpu", 
                compute_type="float32",
                cpu_threads=physical_cores,
                num_workers=1,
                download_root=get_download_root()
            )
            log_progress("model_loaded", progress=45, message="new model loaded successfully")
        except Exception as load_error:
            log_progress("error", message=f"Model Load Error: {str(load_error)}")
            return

        log_progress("transcribing", progress=50, message="Transcribing...")
        
        segments, info = model.transcribe(
            TEMP_AUDIO_PATH, 
            beam_size=1, 
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        log_progress("processing", progress=70, message=f"Detected language '{info.language}'")

        with open(srt_path, "w", encoding="utf-8") as srt_file:
            for i, segment in enumerate(segments, start=1):
                start = format_timestamp(segment.start)
                end = format_timestamp(segment.end)
                srt_file.write(f"{i}\n{start} --> {end}\n{segment.text.strip()}\n\n")
                srt_file.flush()
                os.fsync(srt_file.fileno())

        log_progress("cleaning_up", progress=90, message="Cleaning up...")
        cleanup()

        log_progress("completed", progress=100, message=f"Subtitle saved to {srt_path}")

    except Exception as e:
        log_progress("error", message=str(e))
        cleanup()

if __name__ == "__main__":
    if sys.platform.startswith('linux'):
        try:
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            libc.prctl(1, 15)
        except Exception:
            pass

    multiprocessing.freeze_support()
    
    # New Argument Parsing Logic
    action = "transcribe"
    model_size = "base"
    video_path = None
    
    args = sys.argv[1:]
    
    # Check for specific flags
    if "--check" in args:
        action = "check"
        idx = args.index("--check")
        if idx + 1 < len(args):
            model_size = args[idx+1]
            downloaded = is_model_downloaded(model_size)
            print(json.dumps({"downloaded": downloaded}))
            sys.exit(0)

    # Legacy/Default behavior parsing
    for arg in args:
        if arg.startswith('--model'):
            parts = arg.split('=')
            if len(parts) > 1:
                model_size = parts[1]
        elif not arg.startswith('-') and not ("import" in arg or "main(" in arg) and os.path.exists(arg):
            video_path = arg
    
    if video_path:
        log_progress("started", message="Engine started successfully")
        transcribe(video_path, model_size)
    elif action != "check":
        # Check if we are a child process before logging error
        if len(sys.argv) > 1 and not ("import" in sys.argv[1] or "main(" in sys.argv[1]):
            log_progress("error", message="No valid video path provided.")
