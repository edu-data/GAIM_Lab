"""Quick test: pyannote.audio speaker diarization"""
import sys, os, json, time
sys.path.insert(0, r"d:\AI\GAIM_Lab")
from dotenv import load_dotenv
load_dotenv(r"d:\AI\GAIM_Lab\.env")

from core.agents.stt_agent import STTAgent, HAS_PYANNOTE
print(f"HAS_PYANNOTE: {HAS_PYANNOTE}")

hf = os.getenv("HF_TOKEN", "")
print(f"HF_TOKEN: {hf[:10]}..." if hf else "HF_TOKEN: NOT SET")

agent = STTAgent()
video = r"d:\AI\GAIM_Lab\video\20251209_100926.mp4"

print("Extracting audio...")
import subprocess, tempfile
temp_audio = os.path.join(tempfile.gettempdir(), "pyannote_test.wav")
subprocess.run(
    ["ffmpeg", "-y", "-i", video, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", temp_audio],
    capture_output=True, timeout=120
)

print("Running STT analysis...")
t0 = time.time()
result = agent.analyze(temp_audio)
elapsed = time.time() - t0

print(f"Method: {result.get('method', '?')}")
print(f"Diarization: {result.get('diarization_method', '?')}")
print(f"Teacher ratio: {result.get('teacher_ratio', 0):.1%}")
print(f"Student turns: {result.get('student_turns', 0)}")
print(f"Interactions: {result.get('interaction_count', 0)}")
print(f"Time: {elapsed:.1f}s")
