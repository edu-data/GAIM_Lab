"""Debug: pyannote with soundfile backend"""
import os
os.environ["TORCHAUDIO_USE_BACKEND_DISPATCHER"] = "1"

import sys, traceback, time
sys.path.insert(0, r"d:\AI\GAIM_Lab")
from dotenv import load_dotenv
load_dotenv(r"d:\AI\GAIM_Lab\.env")

hf_token = os.getenv("HF_TOKEN", "")

# Check AudioDecoder issue
print("Checking torchaudio backends...")
try:
    import torchaudio
    print(f"torchaudio version: {torchaudio.__version__}")
    backends = torchaudio.list_audio_backends() if hasattr(torchaudio, 'list_audio_backends') else 'N/A'
    print(f"Available backends: {backends}")
except Exception as e:
    print(f"torchaudio error: {e}")

# Try loading pyannote pipeline
print("\nLoading pyannote pipeline...")
try:
    from pyannote.audio import Pipeline
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token,
    )
    print(f"Pipeline loaded: {type(pipeline).__name__}")

    # Test on actual audio
    temp_audio = os.path.join(os.environ.get("TEMP", "/tmp"), "pyannote_test.wav")
    if os.path.exists(temp_audio):
        print(f"\nRunning diarization on {temp_audio}...")
        t0 = time.time()
        diarization = pipeline(temp_audio, min_speakers=1, max_speakers=4)
        elapsed = time.time() - t0

        speakers = {}
        for segment, _, speaker in diarization.itertracks(yield_label=True):
            dur = segment.end - segment.start
            speakers[speaker] = speakers.get(speaker, 0) + dur

        print(f"Diarization complete in {elapsed:.1f}s")
        print(f"Speakers detected: {len(speakers)}")
        for spk, dur in sorted(speakers.items(), key=lambda x: -x[1]):
            print(f"  {spk}: {dur:.1f}s ({dur/sum(speakers.values())*100:.0f}%)")
    else:
        print(f"No test audio at {temp_audio} — extract first")

except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
    traceback.print_exc()
