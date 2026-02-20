import json

with open('output/batch_agents_20260218_145847/20251209_100926/agent_result.json', encoding='utf-8') as f:
    r = json.load(f)
    vis = r['agents']['vision']
    print('Vision status:', vis['status'])
    print('Vision time:', vis['elapsed_seconds'], 's')
    print('Vision error:', vis.get('error'))
    vs = r.get('vision_summary', {})
    print('Vision engine:', vs.get('analysis_engine', 'N/A'))
    print('Frames analyzed:', vs.get('total_frames_analyzed', 0))
    print('Eye contact ratio:', vs.get('eye_contact_ratio', 'N/A'))
    print('Gesture active:', vs.get('gesture_active_ratio', 'N/A'))
    print('Face detection:', vs.get('face_detection_ratio', 'N/A'))
    print()
    ped = r.get('pedagogy', {})
    for d in ped.get('dimensions', []):
        n = d['name']
        s = d['score']
        m = d['max_score']
        print(f"  {n}: {s}/{m}")
    print(f"\n  Total: {ped.get('total_score')}, Grade: {ped.get('grade')}")
