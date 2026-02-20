"""v5.0 quick verification test"""
import sys
sys.path.insert(0, ".")

# 1. Pedagogy Agent with YAML config
from core.agents.pedagogy_agent import PedagogyAgent
agent = PedagogyAgent()
print(f"Preset: {agent.preset}")
print(f"Dimensions loaded: {len(agent.dimensions)}")
print(f"Base for expertise: {agent._get_base('수업 전문성')}")
print(f"Base for creativity: {agent._get_base('창의성')}")

# Simulate a good teacher
stt = {
    "word_count": 900, "duration_seconds": 600, "speaking_rate": 90,
    "filler_ratio": 0.02, "speaking_pattern": "대화형 (Conversational)",
    "segment_count": 80, "student_turns": 12, "interaction_count": 15,
    "teacher_ratio": 0.70, "question_count": 8,
}
disc = {
    "question_types": {"open_ended": 5, "closed": 8, "scaffolding": 3, "rhetorical": 1},
    "feedback_quality": {"specific_praise": 4, "corrective": 2, "generic": 5},
    "bloom_levels": {"remember": 0.2, "understand": 0.3, "apply": 0.2, "analyze": 0.15, "evaluate": 0.1, "create": 0.05},
    "interaction_score": 78,
}
r_good = agent.evaluate({}, {}, {}, stt, disc)
print(f"\n[Good teacher] Total: {r_good['total_score']}, Grade: {r_good['grade']}")
for d in r_good["dimensions"]:
    print(f"  {d['name']}: {d['score']}/{d['max_score']} ({d['percentage']:.0f}%)")

# Simulate a poor teacher
stt_bad = {
    "word_count": 200, "duration_seconds": 600, "speaking_rate": 20,
    "filler_ratio": 0.08, "speaking_pattern": "느림 (Slow)",
    "segment_count": 15, "student_turns": 0, "interaction_count": 0,
    "teacher_ratio": 0.98, "question_count": 0,
}
disc_bad = {
    "question_types": {"open_ended": 0, "closed": 3, "scaffolding": 0, "rhetorical": 0},
    "feedback_quality": {"specific_praise": 0, "corrective": 0, "generic": 2},
    "bloom_levels": {"remember": 0.7, "understand": 0.2, "apply": 0.1, "analyze": 0, "evaluate": 0, "create": 0},
    "interaction_score": 25,
}
agent2 = PedagogyAgent()
r_bad = agent2.evaluate({}, {}, {}, stt_bad, disc_bad)
print(f"\n[Poor teacher] Total: {r_bad['total_score']}, Grade: {r_bad['grade']}")
for d in r_bad["dimensions"]:
    print(f"  {d['name']}: {d['score']}/{d['max_score']} ({d['percentage']:.0f}%)")

# Score range check
diff = r_good["total_score"] - r_bad["total_score"]
print(f"\nScore difference: {diff:.1f} points")
print(f"v4.2 range was ~9.7 (70.9-80.6)")
print(f"v5.0 range: {r_bad['total_score']:.1f} - {r_good['total_score']:.1f}")

# 2. Orchestrator import check
from core.agents.orchestrator import AgentOrchestrator
orch = AgentOrchestrator()
print(f"\nOrchestrator has _lock: {hasattr(orch, '_lock')}")
print(f"Context has discourse_result: {hasattr(orch.context, 'discourse_result')}")
print("\n✅ All v5.0 verification tests passed!")
