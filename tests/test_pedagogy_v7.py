"""
PedagogyAgent v7.0 Verification Tests
- Score range 25pt+ validation
- Deterministic scoring (same input -> same output)
- Confidence metadata validation
- Binning validation
- Dimension profile validation
"""
import sys
sys.path.insert(0, ".")

from core.agents.pedagogy_agent import PedagogyAgent, _bin

# ============================================================
# 테스트 데이터
# ============================================================

# 우수 교사 시나리오
VIS_GOOD = {
    "gesture_active_ratio": 0.65,
    "avg_gesture_score": 0.7,
    "eye_contact_ratio": 0.75,
    "face_detection_ratio": 0.9,
    "avg_expression_score": 72,
    "avg_body_openness": 0.8,
    "avg_motion_score": 28,
}
STT_GOOD = {
    "word_count": 1300, "duration_seconds": 600, "speaking_rate": 130,
    "filler_ratio": 0.01, "speaking_pattern": "Conversational",
    "segment_count": 120, "student_turns": 15, "interaction_count": 18,
    "teacher_ratio": 0.62, "question_count": 12,
}
CON_GOOD = {
    "slide_detected_ratio": 0.7, "speaker_visible_ratio": 0.85,
    "avg_color_contrast": 70, "avg_complexity": 14,
}
VIBE_GOOD = {
    "avg_silence_ratio": 0.22, "monotone_ratio": 0.12,
    "energy_distribution": {"low": 0.15, "normal": 0.5, "high": 0.35},
}
DISC_GOOD = {
    "question_types": {"open_ended": 8, "closed": 4, "scaffolding": 5, "rhetorical": 1},
    "feedback_quality": {"specific_praise": 7, "corrective": 4, "generic": 1},
    "bloom_levels": {"remember": 0.1, "understand": 0.2, "apply": 0.2, "analyze": 0.2, "evaluate": 0.15, "create": 0.15},
    "interaction_score": 88,
}

# 미흡 교사 시나리오
VIS_BAD = {
    "gesture_active_ratio": 0.05,
    "avg_gesture_score": 0.1,
    "eye_contact_ratio": 0.08,
    "face_detection_ratio": 0.6,
    "avg_expression_score": 20,
    "avg_body_openness": 0.2,
    "avg_motion_score": 2,
}
STT_BAD = {
    "word_count": 180, "duration_seconds": 600, "speaking_rate": 18,
    "filler_ratio": 0.09, "speaking_pattern": "느림 (Slow)",
    "segment_count": 12, "student_turns": 0, "interaction_count": 0,
    "teacher_ratio": 0.98, "question_count": 0,
}
CON_BAD = {
    "slide_detected_ratio": 0.05, "speaker_visible_ratio": 0.2,
    "avg_color_contrast": 8, "avg_complexity": 1,
}
VIBE_BAD = {
    "avg_silence_ratio": 0.6, "monotone_ratio": 0.75,
    "energy_distribution": {"low": 0.7, "normal": 0.25, "high": 0.05},
}
DISC_BAD = {
    "question_types": {"open_ended": 0, "closed": 1, "scaffolding": 0, "rhetorical": 0},
    "feedback_quality": {"specific_praise": 0, "corrective": 0, "generic": 1},
    "bloom_levels": {"remember": 0.85, "understand": 0.1, "apply": 0.05, "analyze": 0, "evaluate": 0, "create": 0},
    "interaction_score": 15,
}

# 일반 교사 시나리오
STT_TYP = {
    "word_count": 688, "duration_seconds": 605, "speaking_rate": 68.2,
    "filler_ratio": 0.061, "speaking_pattern": "느림 (Slow)",
    "segment_count": 153, "student_turns": 30, "interaction_count": 43,
    "teacher_ratio": 0.907, "question_count": 28,
}
DISC_TYP = {
    "question_types": {"open_ended": 1, "closed": 2, "scaffolding": 0, "rhetorical": 1},
    "feedback_quality": {"specific_praise": 1, "corrective": 1, "generic": 1},
    "bloom_levels": {"remember": 0.6, "understand": 0.3, "apply": 0.1, "analyze": 0.0, "evaluate": 0.0, "create": 0.0},
    "interaction_score": 65,
}


# ============================================================
# 테스트 실행
# ============================================================

print("=" * 65)
print("[TEST] PedagogyAgent v7.0 Verification Tests")
print("=" * 65)

# --- Test 1: 기본 로드 ---
print("\n[1] Test 1: Config Loading")
agent = PedagogyAgent()
print(f"  Preset: {agent.preset}")
print(f"  Dimensions: {len(agent.dimensions)}")
print(f"  Binning metrics: {len(agent.binning)}")
print(f"  Confidence weights: {agent.confidence_weights}")
assert len(agent.dimensions) == 7, f"Expected 7 dimensions, got {len(agent.dimensions)}"
assert len(agent.binning) > 0, "Binning config not loaded"
assert "vision" in agent.confidence_weights, "Confidence weights not loaded"
print("  ✅ Config loaded successfully")

# --- Test 2: 구간화(Binning) ---
print("\n[2] Test 2: Binning")
bins_gesture = agent.binning["gesture_active_ratio"]
assert _bin(0.05, bins_gesture) == "INACTIVE"
assert _bin(0.20, bins_gesture) == "LOW"
assert _bin(0.45, bins_gesture) == "MODERATE"
assert _bin(0.60, bins_gesture) == "ACTIVE"
# 경계값 테스트: 0.49 와 0.51은 같은 구간
assert _bin(0.49, bins_gesture) == "MODERATE"
assert _bin(0.51, bins_gesture) == "MODERATE"
print("  ✅ Binning works correctly (boundary consistency verified)")

# --- Test 3: 우수 교사 ---
print("\n[3] Test 3: Good Teacher")
r_good = agent.evaluate(VIS_GOOD, CON_GOOD, VIBE_GOOD, STT_GOOD, DISC_GOOD)
print(f"  Total: {r_good['total_score']}, Grade: {r_good['grade']}")
assert r_good.get("version") == "7.0", "Missing version"
for d in r_good["dimensions"]:
    print(f"    {d['name']}: {d['score']}/{d['max_score']} ({d['percentage']:.0f}%) [conf: {d['confidence']:.2f}]")
print(f"  Profile - Strengths: {r_good['profile_summary']['strengths']}")
print(f"  Profile - Improvements: {r_good['profile_summary']['improvements']}")
print(f"  Confidence: {r_good['confidence']['overall']:.3f}")

# --- Test 4: 미흡 교사 ---
print("\n[4] Test 4: Poor Teacher")
r_bad = PedagogyAgent().evaluate(VIS_BAD, CON_BAD, VIBE_BAD, STT_BAD, DISC_BAD)
print(f"  Total: {r_bad['total_score']}, Grade: {r_bad['grade']}")
for d in r_bad["dimensions"]:
    print(f"    {d['name']}: {d['score']}/{d['max_score']} ({d['percentage']:.0f}%) [conf: {d['confidence']:.2f}]")

# --- Test 5: 일반 교사 ---
print("\n[5] Test 5: Typical Teacher")
r_typ = PedagogyAgent().evaluate(VIS_GOOD, CON_GOOD, VIBE_GOOD, STT_TYP, DISC_TYP)
print(f"  Total: {r_typ['total_score']}, Grade: {r_typ['grade']}")
for d in r_typ["dimensions"]:
    print(f"    {d['name']}: {d['score']}/{d['max_score']} ({d['percentage']:.0f}%)")

# --- Test 6: 점수 범위 검증 ---
print("\n[6] Test 6: Score Range (Target: >=25pt)")
diff = r_good["total_score"] - r_bad["total_score"]
print(f"  Good: {r_good['total_score']}")
print(f"  Poor: {r_bad['total_score']}")
print(f"  Difference: {diff:.1f}pt")
assert diff >= 25, f"FAIL Score range too small: {diff:.1f} < 25"
print(f"  PASS Score range: {diff:.1f}pt >= 25pt")

# --- Test 7: 창의성 범위 ---
print("\n[7] Test 7: Creativity Range (Target: >=2.0)")
c_good = next(d['score'] for d in r_good['dimensions'] if d['name'] == '\ucc3d\uc758\uc131')
c_bad = next(d['score'] for d in r_bad['dimensions'] if d['name'] == '\ucc3d\uc758\uc131')
c_diff = c_good - c_bad
print(f"  Creativity Good: {c_good}, Poor: {c_bad}, Range: {c_diff:.1f}")
assert c_diff >= 2.0, f"FAIL Creativity range too narrow: {c_diff:.1f} < 2.0"
print(f"  PASS Creativity range: {c_diff:.1f} >= 2.0")

# --- Test 8: 결정론 검증 ---
print("\n[8] Test 8: Determinism (5 runs, identical input)")
scores = []
for i in range(5):
    a = PedagogyAgent()
    r = a.evaluate(VIS_GOOD, CON_GOOD, VIBE_GOOD, STT_GOOD, DISC_GOOD)
    scores.append(r["total_score"])
print(f"  Scores: {scores}")
assert len(set(scores)) == 1, f"FAIL Non-deterministic scores: {set(scores)}"
print(f"  PASS All 5 runs identical: {scores[0]}")

# --- Test 9: Confidence 메타데이터 검증 ---
print("\n[9] Test 9: Confidence Metadata")
assert "confidence" in r_good, "Missing 'confidence' in result"
assert "overall" in r_good["confidence"], "Missing 'overall' in confidence"
assert r_good["confidence"]["overall"] > 0, "Overall confidence should be > 0"
assert r_good["confidence"]["vision_available"] == True
assert r_good["confidence"]["stt_available"] == True
# 부분 데이터 테스트
r_partial = PedagogyAgent().evaluate({}, {}, {})
assert r_partial["confidence"]["overall"] < r_good["confidence"]["overall"], \
    f"Partial data confidence ({r_partial['confidence']['overall']}) should be < full data ({r_good['confidence']['overall']})"
print(f"  Full data confidence: {r_good['confidence']['overall']:.3f}")
print(f"  Partial data confidence: {r_partial['confidence']['overall']:.3f}")
print(f"  PASS Confidence metadata valid")

# --- Test 10: v7.0 메타데이터 ---
print("\n[10] Test 10: v7.0 Metadata")
assert r_good.get("version") == "7.0", f"Missing version 7.0"
assert r_good.get("is_supplementary") == True, "Missing is_supplementary flag"
assert "profile_summary" in r_good, "Missing profile_summary"
assert "top_dimension" in r_good["profile_summary"], "Missing top_dimension"
print(f"  Version: {r_good['version']}")
print(f"  Top dimension: {r_good['profile_summary']['top_dimension']}")
print(f"  Weakest dimension: {r_good['profile_summary']['weakest_dimension']}")
print(f"  PASS v7.0 metadata valid")

# --- 참여도 천장 제거 확인 ---
print("\n[11] Test 11: Participation ceiling check")
p_good = next(d['score'] for d in r_good['dimensions'] if d['name'] == '\ud559\uc0dd \ucc38\uc5ec')
p_typ = next(d['score'] for d in r_typ['dimensions'] if d['name'] == '\ud559\uc0dd \ucc38\uc5ec')
print(f"  Participation Good: {p_good}/15, Typical: {p_typ}/15")
assert p_good < 15, f"Participation ceiling NOT fixed: {p_good}"
print(f"  PASS No ceiling effect")

# ============================================================
# 최종 요약
# ============================================================
print("\n" + "=" * 65)
print(f"All v7.0 verification tests PASSED!")
print(f"   Score range: {diff:.1f}pt (target: >=25pt)")
print(f"   Good: {r_good['total_score']} ({r_good['grade']})")
print(f"   Typical: {r_typ['total_score']} ({r_typ['grade']})")
print(f"   Poor: {r_bad['total_score']} ({r_bad['grade']})")
print(f"   Deterministic: PASS")
print(f"   Confidence: PASS")
print(f"   Binning: PASS")
print("=" * 65)
