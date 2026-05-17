import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { open } from "@tauri-apps/plugin-dialog";
import { motion, AnimatePresence } from "framer-motion";
import { FileVideo, CheckCircle2, AlertCircle, Loader2, Upload } from "lucide-react";

interface StatusUpdate {
  status: string;
  progress: number;
  message: string;
}

export default function App() {
  const [videoPath, setVideoPath] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [complete, setComplete] = useState(false);

  useEffect(() => {
    const unlisten = listen<string>("engine-status", (event) => {
      console.log("Raw engine event:", event);
      try {
        // The sidecar output might contain extra whitespace/newlines
        const cleanPayload = event.payload.trim();
        if (!cleanPayload) return;

        const data: StatusUpdate = JSON.parse(cleanPayload);
        setProgress(data.progress);
        setStatusMessage(data.message);
        
        if (data.status === "completed") {
          setProcessing(false);
          setComplete(true);
        } else if (data.status === "error") {
          setProcessing(false);
          setError(data.message);
        }
      } catch (e) {
        console.error("Failed to parse engine status:", e, "Payload:", event.payload);
      }
    });

    return () => {
      unlisten.then((f) => f());
    };
  }, []);

  const handleSelectFile = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{
          name: 'Video',
          extensions: ['mp4', 'mkv', 'avi', 'mov', 'webm']
        }]
      });
      if (selected && typeof selected === 'string') {
        setVideoPath(selected);
      }
    } catch (e) {
      console.error("Failed to open dialog:", e);
    }
  };

  const handleProcess = async () => {
    if (!videoPath) return;

    setProcessing(true);
    setError(null);
    setComplete(false);
    setProgress(0);
    setStatusMessage("Initializing...");

    try {
      await invoke("process_video", { videoPath });
    } catch (e) {
      setError(String(e));
      setProcessing(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen w-screen p-8 bg-neutral-900/50 backdrop-blur-xl text-neutral-100 font-sans selection:bg-blue-500/30">
      <div className="w-full max-w-md bg-neutral-800/40 border border-neutral-700/50 rounded-3xl shadow-2xl overflow-hidden backdrop-blur-2xl">
        <div className="p-8 flex flex-col items-center gap-6">
          <div className="flex items-center justify-center w-20 h-20 rounded-2xl bg-blue-500/10 border border-blue-500/20 shadow-inner">
            <FileVideo className="w-10 h-10 text-blue-400" />
          </div>

          <div className="text-center space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight">Subtitle Gen</h1>
            <p className="text-neutral-400 text-sm">Local AI-powered video transcription</p>
          </div>

          {!videoPath && !processing && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="w-full"
            >
              <button 
                onClick={handleSelectFile}
                className="w-full h-40 border-2 border-dashed border-neutral-700/50 rounded-2xl flex flex-col items-center justify-center gap-3 hover:border-blue-500/50 hover:bg-blue-500/5 transition-all duration-300 group"
              >
                <Upload className="w-8 h-8 text-neutral-500 group-hover:text-blue-400 transition-colors" />
                <div className="text-center">
                  <p className="text-sm font-medium">Select Video File</p>
                  <p className="text-xs text-neutral-500 mt-1">MP4, MKV, AVI, MOV, WEBM</p>
                </div>
              </button>
            </motion.div>
          )}

          {videoPath && !processing && !complete && (
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="w-full space-y-4"
            >
              <div className="p-4 bg-neutral-900/50 border border-neutral-700/50 rounded-2xl flex items-center gap-3">
                <FileVideo className="w-5 h-5 text-blue-400" />
                <span className="text-sm truncate font-medium">{videoPath}</span>
              </div>
              <button
                onClick={handleProcess}
                className="w-full py-4 bg-blue-600 hover:bg-blue-500 active:scale-[0.98] text-white rounded-2xl font-medium transition-all shadow-lg shadow-blue-900/20"
              >
                Generate Subtitles
              </button>
              <button
                onClick={() => setVideoPath(null)}
                className="w-full py-2 text-neutral-500 hover:text-neutral-300 text-sm transition-colors"
              >
                Change video
              </button>
            </motion.div>
          )}

          {processing && (
            <div className="w-full space-y-6">
              <div className="space-y-3">
                <div className="flex justify-between text-xs font-medium uppercase tracking-wider text-neutral-500">
                  <span>{statusMessage || "Processing..."}</span>
                  <span>{progress}%</span>
                </div>
                <div className="h-2 w-full bg-neutral-700/30 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    className="h-full bg-blue-500 shadow-[0_0_12px_rgba(59,130,246,0.5)]"
                  />
                </div>
              </div>
              <div className="flex items-center justify-center gap-3 py-2">
                <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                <span className="text-sm text-neutral-400">This may take a few minutes</span>
              </div>
            </div>
          )}

          <AnimatePresence>
            {complete && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex flex-col items-center gap-3 text-emerald-400"
              >
                <CheckCircle2 className="w-8 h-8" />
                <div className="text-center">
                  <p className="font-semibold">Transcription Complete!</p>
                  <p className="text-xs opacity-80 mt-1">SRT file created next to your video</p>
                </div>
                <button
                  onClick={() => {
                    setComplete(false);
                    setVideoPath(null);
                  }}
                  className="mt-2 px-6 py-2 bg-emerald-500/20 hover:bg-emerald-500/30 rounded-xl text-sm font-medium transition-colors"
                >
                  Process Another
                </button>
              </motion.div>
            )}

            {error && (
              <motion.div 
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="w-full p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center gap-3 text-red-400"
              >
                <AlertCircle className="w-5 h-5 shrink-0" />
                <span className="text-sm font-medium">{error}</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
      
      <p className="mt-8 text-neutral-600 text-xs tracking-widest uppercase">
        Local Processing • Privacy Guaranteed
      </p>
    </div>
  );
}
