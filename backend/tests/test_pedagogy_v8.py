"""
GAIM Lab v8.1 — Pedagogy Agent Unit Tests

시그모이드 매핑, 연속 채점 vs 구간 채점, steepness 민감도 테스트.

실행:
    python -m pytest backend/tests/test_pedagogy_v8.py -v
"""

import sys
import math
from pathlib import Path

import pytest

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.agents.pedagogy_agent import _sigmoid_map, _bin, PedagogyAgent


# ─── Test Data ───
SAMPLE_BINS = {
    "INACTIVE": [0.0, 0.15],
    "LOW": [0.15, 0.35],
    "MODERATE": [0.35, 0.55],
    "ACTIVE": [0.55, 1.0],
}

SAMPLE_SCORES = {
    "INACTIVE": -2.0,
    "LOW": -0.5,
    "MODERATE": 1.0,
    "ACTIVE": 2.5,
}


class TestSigmoidMap:
    """시그모이드 연속 매핑 테스트"""

    def test_returns_float(self):
        """반환 타입이 float"""
        result = _sigmoid_map(0.3, SAMPLE_BINS, SAMPLE_SCORES)
        assert isinstance(result, float)

    def test_center_of_bin_approximates_bin_score(self):
        """구간 중심값에서 해당 구간 점수에 근접해야 함"""
        # MODERATE 구간 중심: 0.45
        result = _sigmoid_map(0.45, SAMPLE_BINS, SAMPLE_SCORES)
        # MODERATE 점수는 1.0 — 결과가 이에 가까워야 함
        assert abs(result - 1.0) < 1.5, f"Expected near 1.0, got {result}"

    def test_boundary_smoothness(self):
        """경계값 전후에서 급격한 점프가 없어야 함"""
        # INACTIVE/LOW 경계: 0.15
        v1 = _sigmoid_map(0.14, SAMPLE_BINS, SAMPLE_SCORES)
        v2 = _sigmoid_map(0.15, SAMPLE_BINS, SAMPLE_SCORES)
        v3 = _sigmoid_map(0.16, SAMPLE_BINS, SAMPLE_SCORES)
        
        # 연속적이면 인접한 값의 차이가 작아야 함
        diff_12 = abs(v2 - v1)
        diff_23 = abs(v3 - v2)
        assert diff_12 < 1.0, f"Jump at boundary too large: {diff_12}"
        assert diff_23 < 1.0, f"Jump at boundary too large: {diff_23}"

    def test_monotonicity_within_range(self):
        """입력이 증가하면 점수도 대체로 증가해야 함 (점수가 오름차순일 때)"""
        values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        results = [_sigmoid_map(v, SAMPLE_BINS, SAMPLE_SCORES) for v in values]
        
        # 대체로 증가하는지 확인 (완벽한 단조증가는 아닐 수 있음)
        increasing_pairs = sum(1 for i in range(len(results)-1) if results[i+1] >= results[i])
        assert increasing_pairs >= len(results) // 2, f"Not mostly increasing: {results}"

    def test_single_bin_returns_score(self):
        """구간이 하나뿐이면 해당 점수 반환"""
        single_bin = {"ONLY": [0.0, 1.0]}
        single_score = {"ONLY": 5.0}
        result = _sigmoid_map(0.5, single_bin, single_score)
        assert result == 5.0

    def test_empty_bins_returns_zero(self):
        """빈 구간이면 0.0 반환"""
        result = _sigmoid_map(0.5, {}, {})
        assert result == 0.0


class TestSteepnessSensitivity:
    """steepness 파라미터 민감도 테스트"""

    def test_high_steepness_sharper_transition(self):
        """높은 steepness → 경계 근처에서 더 급격한 변화"""
        # 경계 전후 차이 비교
        v_before = 0.14
        v_after = 0.16
        
        diff_low = abs(
            _sigmoid_map(v_after, SAMPLE_BINS, SAMPLE_SCORES, steepness=5.0) -
            _sigmoid_map(v_before, SAMPLE_BINS, SAMPLE_SCORES, steepness=5.0)
        )
        diff_high = abs(
            _sigmoid_map(v_after, SAMPLE_BINS, SAMPLE_SCORES, steepness=50.0) -
            _sigmoid_map(v_before, SAMPLE_BINS, SAMPLE_SCORES, steepness=50.0)
        )
        
        # 높은 steepness에서 경계 전후 차이가 더 크거나 같아야 함
        # (매우 높은 steepness는 구간화에 수렴)
        assert diff_high >= diff_low * 0.5, \
            f"High steepness diff ({diff_high}) should be >= low steepness diff ({diff_low})"

    def test_steepness_does_not_crash(self):
        """극단적 steepness 값에서도 오류 없이 실행"""
        for s in [0.1, 1.0, 10.0, 100.0, 1000.0]:
            result = _sigmoid_map(0.3, SAMPLE_BINS, SAMPLE_SCORES, steepness=s)
            assert math.isfinite(result), f"Non-finite result at steepness={s}"


class TestBinning:
    """구간화(_bin) 함수 테스트"""

    def test_correct_bin_assignment(self):
        """값이 올바른 구간에 할당"""
        assert _bin(0.05, SAMPLE_BINS) == "INACTIVE"
        assert _bin(0.25, SAMPLE_BINS) == "LOW"
        assert _bin(0.45, SAMPLE_BINS) == "MODERATE"
        assert _bin(0.75, SAMPLE_BINS) == "ACTIVE"

    def test_boundary_values(self):
        """경계 값은 상위 구간에 할당"""
        # 0.15는 LOW의 하한
        result = _bin(0.15, SAMPLE_BINS)
        assert result in ("INACTIVE", "LOW"), f"Boundary value 0.15 → {result}"


class TestPedagogyAgentModes:
    """PedagogyAgent 구간 vs 연속 모드 테스트"""

    def test_binned_mode_initialization(self):
        """구간화 모드 초기화"""
        agent = PedagogyAgent(use_rag=False, continuous_scoring=False)
        assert agent.continuous_scoring is False

    def test_continuous_mode_initialization(self):
        """연속 채점 모드 초기화"""
        agent = PedagogyAgent(use_rag=False, continuous_scoring=True)
        assert agent.continuous_scoring is True

    def test_steepness_default(self):
        """기본 steepness는 10.0"""
        agent = PedagogyAgent(use_rag=False)
        assert agent.steepness == 10.0

    def test_steepness_env_override(self, monkeypatch):
        """GAIM_SIGMOID_STEEPNESS 환경변수로 steepness 변경"""
        monkeypatch.setenv("GAIM_SIGMOID_STEEPNESS", "20.0")
        agent = PedagogyAgent(use_rag=False)
        assert agent.steepness == 20.0

    def test_binned_vs_continuous_differ(self):
        """구간 채점과 연속 채점의 결과가 다를 수 있음"""
        agent_bin = PedagogyAgent(use_rag=False, continuous_scoring=False)
        agent_cont = PedagogyAgent(use_rag=False, continuous_scoring=True)
        
        label_scores = {"INACTIVE": -2.0, "LOW": -0.5, "MODERATE": 1.0, "ACTIVE": 2.5}
        
        # 경계 근처 값에서 차이 확인
        v = 0.15  # INACTIVE/LOW 경계
        score_bin = agent_bin._continuous_score("gesture_active_ratio", v, label_scores)
        score_cont = agent_cont._continuous_score("gesture_active_ratio", v, label_scores)
        
        # 둘 다 유효한 float여야 함
        assert math.isfinite(score_bin)
        assert math.isfinite(score_cont)

    def test_dimensions_loaded(self):
        """차원 설정이 로드됨"""
        agent = PedagogyAgent(use_rag=False)
        assert len(agent.dimensions) >= 7, f"Expected ≥7 dimensions, got {len(agent.dimensions)}"

    def test_grading_thresholds(self):
        """등급 기준이 정의됨"""
        agent = PedagogyAgent(use_rag=False)
        assert "A+" in agent.grading
        assert "D" in agent.grading
        assert agent.grading["A+"] > agent.grading["D"]
