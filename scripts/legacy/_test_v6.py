"""v6.0 quick verification test"""
import sys
sys.path.insert(0, ".")

# 1. Vision Agent — MediaPipe Tasks API
print("=== VisionAgent v6.0 ===")
from core.agents.vision_agent import VisionAgent
va = VisionAgent()
engine = "mediapipe_tasks" if va.use_mediapipe else "opencv"
print(f"  Engine: {engine}")
print(f"  Has face_landmarker: {hasattr(va, 'face_landmarker')}")
print(f"  Has pose_landmarker: {hasattr(va, 'pose_landmarker')}")

# 2. Pedagogy Agent with adjust_range clamping
print("\n=== PedagogyAgent v6.0 ===")
from core.agents.pedagogy_agent import PedagogyAgent
agent = PedagogyAgent()
print(f"  Preset: {agent.preset}")
print(f"  Base expertise: {agent._get_base('수업 전문성')}")
print(f"  Range expertise: {agent._get_adjust_range('수업 전문성')}")
print(f"  Base creativity: {agent._get_base('창의성')}")
print(f"  Range creativity: {agent._get_adjust_range('창의성')}")

# 3. Simulate a GOOD teacher
print("\n=== Good Teacher ===")
vis_good = {
    "gesture_active_ratio": 0.65,
    "avg_gesture_score": 0.7,
    "eye_contact_ratio": 0.75,
    "face_detection_ratio": 0.9,
    "avg_expression_score": 72,
    "avg_body_openness": 0.8,
    "avg_motion_score": 28,
}
stt_good = {
    "word_count": 900, "duration_seconds": 600, "speaking_rate": 90,
    "filler_ratio": 0.02, "speaking_pattern": "대화형 (Conversational)",
    "segment_count": 80, "student_turns": 12, "interaction_count": 15,
    "teacher_ratio": 0.65, "question_count": 12,
}
disc_good = {
    "question_types": {"open_ended": 6, "closed": 5, "scaffolding": 4, "rhetorical": 1},
    "feedback_quality": {"specific_praise": 6, "corrective": 3, "generic": 2},
    "bloom_levels": {"remember": 0.15, "understand": 0.25, "apply": 0.2, "analyze": 0.2, "evaluate": 0.1, "create": 0.1},
    "interaction_score": 82,
}
r_good = agent.evaluate(vis_good, {"slide_detected_ratio": 0.6, "speaker_visible_ratio": 0.85, "avg_color_contrast": 65, "avg_complexity": 12}, {"avg_silence_ratio": 0.22, "monotone_ratio": 0.15, "energy_distribution": {"low": 0.2, "normal": 0.5, "high": 0.3}}, stt_good, disc_good)
print(f"  Total: {r_good['total_score']}, Grade: {r_good['grade']}")
for d in r_good["dimensions"]:
    print(f"    {d['name']}: {d['score']}/{d['max_score']} ({d['percentage']:.0f}%)")

# 4. Simulate a POOR teacher
print("\n=== Poor Teacher ===")
vis_bad = {
    "gesture_active_ratio": 0.05,
    "avg_gesture_score": 0.1,
    "eye_contact_ratio": 0.1,
    "face_detection_ratio": 0.6,
    "avg_expression_score": 25,
    "avg_body_openness": 0.2,
    "avg_motion_score": 2,
}
stt_bad = {
    "word_count": 200, "duration_seconds": 600, "speaking_rate": 20,
    "filler_ratio": 0.08, "speaking_pattern": "느림 (Slow)",
    "segment_count": 15, "student_turns": 0, "interaction_count": 0,
    "teacher_ratio": 0.98, "question_count": 0,
}
disc_bad = {
    "question_types": {"open_ended": 0, "closed": 2, "scaffolding": 0, "rhetorical": 0},
    "feedback_quality": {"specific_praise": 0, "corrective": 0, "generic": 1},
    "bloom_levels": {"remember": 0.8, "understand": 0.15, "apply": 0.05, "analyze": 0, "evaluate": 0, "create": 0},
    "interaction_score": 20,
}
agent2 = PedagogyAgent()
r_bad = agent2.evaluate(vis_bad, {"slide_detected_ratio": 0.1, "speaker_visible_ratio": 0.3, "avg_color_contrast": 10, "avg_complexity": 2}, {"avg_silence_ratio": 0.55, "monotone_ratio": 0.65, "energy_distribution": {"low": 0.6, "normal": 0.35, "high": 0.05}}, stt_bad, disc_bad)
print(f"  Total: {r_bad['total_score']}, Grade: {r_bad['grade']}")
for d in r_bad["dimensions"]:
    print(f"    {d['name']}: {d['score']}/{d['max_score']} ({d['percentage']:.0f}%)")

# 5. Simulate a TYPICAL teacher (like v5.0 batch data)
print("\n=== Typical Teacher (v5.0-like data) ===")
stt_typ = {
    "word_count": 688, "duration_seconds": 605, "speaking_rate": 68.2,
    "filler_ratio": 0.061, "speaking_pattern": "느림 (Slow)",
    "segment_count": 153, "student_turns": 30, "interaction_count": 43,
    "teacher_ratio": 0.907, "question_count": 28,
}
disc_typ = {
    "question_types": {"open_ended": 1, "closed": 2, "scaffolding": 0, "rhetorical": 1},
    "feedback_quality": {"specific_praise": 1, "corrective": 1, "generic": 1},
    "bloom_levels": {"remember": 0.6, "understand": 0.3, "apply": 0.1, "analyze": 0.0, "evaluate": 0.0, "create": 0.0},
    "interaction_score": 65,
}
agent3 = PedagogyAgent()
r_typ = agent3.evaluate(vis_good, {"slide_detected_ratio": 1.0, "speaker_visible_ratio": 0.71, "avg_color_contrast": 0, "avg_complexity": 6.3}, {"avg_silence_ratio": 0.365, "monotone_ratio": 0.082, "energy_distribution": {"low": 0.34, "normal": 0.62, "high": 0.03}}, stt_typ, disc_typ)
print(f"  Total: {r_typ['total_score']}, Grade: {r_typ['grade']}")
for d in r_typ["dimensions"]:
    print(f"    {d['name']}: {d['score']}/{d['max_score']} ({d['percentage']:.0f}%)")

# 6. Score analysis
print("\n=== Score Analysis ===")
diff = r_good["total_score"] - r_bad["total_score"]
print(f"  Good teacher: {r_good['total_score']}")
print(f"  Poor teacher: {r_bad['total_score']}")
print(f"  Difference: {diff:.1f} pts")
print(f"  Typical teacher: {r_typ['total_score']}")

# Check student participation is NOT at ceiling
participation_good = next(d['score'] for d in r_good['dimensions'] if d['name'] == '학생 참여')
participation_typ = next(d['score'] for d in r_typ['dimensions'] if d['name'] == '학생 참여')
print(f"\n  Participation - Good: {participation_good}/15 (NOT 15 = ceiling fix)")
print(f"  Participation - Typical: {participation_typ}/15")

# Check creativity range
creativity_good = next(d['score'] for d in r_good['dimensions'] if d['name'] == '창의성')
creativity_bad = next(d['score'] for d in r_bad['dimensions'] if d['name'] == '창의성')
creativity_typ = next(d['score'] for d in r_typ['dimensions'] if d['name'] == '창의성')
print(f"  Creativity range: {creativity_bad} ~ {creativity_good} (typical: {creativity_typ})")

# Assertions
assert diff > 20, f"Score difference too small: {diff}"
assert participation_good < 15, f"Participation ceiling NOT fixed: {participation_good}"
assert participation_typ < 15, f"Typical teacher participation still at ceiling: {participation_typ}"
assert creativity_good - creativity_bad >= 1.5, f"Creativity range too narrow: {creativity_good - creativity_bad}"

print("\n✅ All v6.0 verification tests PASSED!")
