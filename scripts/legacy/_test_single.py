"""Quick single-video verification script"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\AI\GAIM_Lab')
sys.path.insert(0, r'D:\AI\GAIM_Lab\backend\app')
from dotenv import load_dotenv
load_dotenv(r'D:\AI\GAIM_Lab\.env')

from pathlib import Path
import importlib.util

def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

orch_mod = load_mod('orchestrator', r'D:\AI\GAIM_Lab\core\agents\orchestrator.py')
AgentOrchestrator = orch_mod.AgentOrchestrator

orch = AgentOrchestrator()

def on_event(event):
    etype = event['type']
    agent = event['agent']
    data = event.get('data', {})
    if etype == 'agent_start':
        print(f'  >> {agent} start...')
    elif etype == 'agent_done':
        elapsed = data.get('elapsed', 0)
        print(f'  << {agent} done ({elapsed:.2f}s)')
    elif etype == 'agent_error':
        err = data.get('error', 'unknown')
        print(f'  !! {agent} ERROR: {err[:100]}')

orch.on_event(on_event)

video = r'D:\AI\GAIM_Lab\video\20251209_100926.mp4'
out_dir = r'D:\AI\GAIM_Lab\output\_test_fix'
result = orch.run_pipeline(video, temp_dir=os.path.join(out_dir, 'cache'))

# Verification
print('\n' + '='*60)
print('=== VERIFICATION ===')
print('='*60)
n_frames = len(orch.context.extracted_frames)
print(f'Extracted frames: {n_frames}')
print(f'Audio path exists: {bool(orch.context.audio_path)}')

agents_info = result.get('agents', {})
for name in ['vision', 'content', 'vibe']:
    a = agents_info.get(name, {})
    el = a.get('elapsed_seconds', 0)
    err = a.get('error')
    print(f'{name}: elapsed={el:.2f}s, error={err}')

report = result.get('report', {})
vs = report.get('vision_summary', {})
cs = report.get('content_summary', {})
vbs = report.get('vibe_summary', {})
print(f'\nvision_summary keys: {list(vs.keys()) if vs else "EMPTY"}')
print(f'content_summary keys: {list(cs.keys()) if cs else "EMPTY"}')
print(f'vibe_summary keys: {list(vbs.keys()) if vbs else "EMPTY"}')

# Check vision has real data (not error)
if vs and 'error' not in vs:
    print(f'  vision: face_detection_ratio={vs.get("face_detection_ratio", "N/A")}')
    print(f'  vision: avg_motion_score={vs.get("avg_motion_score", "N/A")}')
else:
    print(f'  vision: ERROR - {vs.get("error", "no data")}')

if cs and 'error' not in cs:
    print(f'  content: slide_detected_ratio={cs.get("slide_detected_ratio", "N/A")}')
    print(f'  content: avg_text_density={cs.get("avg_text_density", "N/A")}')
else:
    print(f'  content: ERROR - {cs.get("error", "no data")}')

if vbs and 'error' not in vbs:
    print(f'  vibe: avg_pitch_mean={vbs.get("avg_pitch_mean", "N/A")}')
    print(f'  vibe: avg_silence_ratio={vbs.get("avg_silence_ratio", "N/A")}')
else:
    print(f'  vibe: ERROR - {vbs.get("error", "no data")}')

ped = report.get('pedagogy', {})
print(f'\ntotal_score: {ped.get("total_score")}, grade: {ped.get("grade")}')

# Save result
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, 'test_result.json'), 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f'\nResult saved to {out_dir}/test_result.json')
