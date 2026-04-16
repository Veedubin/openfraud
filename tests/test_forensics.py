"""
Tests for OpenFraud core forensic functions.
"""

import numpy as np
import pandas as pd
import pytest

from openfraud.core import (
    calculate_benford_ssd,
    calculate_z_score,
    calculate_velocity_score,
    detect_frozen_ledger,
    calculate_peer_deviation,
    calculate_composite_risk_score,
    VIOLATION_RULES,
)
from openfraud.utils import add_peer_group_stats, split_temporal


class TestBenfordsLaw:
    def test_natural_distribution_low_ssd(self):
        np.random.seed(42)
        amounts = np.random.lognormal(mean=3.0, sigma=1.5, size=5000)
        ssd = calculate_benford_ssd(amounts)
        assert ssd < 0.05

    def test_uniform_distribution_high_ssd(self):
        amounts = np.random.uniform(1, 100000, size=5000)
        ssd = calculate_benford_ssd(amounts)
        assert ssd > 0.1

    def test_insufficient_data_returns_zero(self):
        amounts = np.array([1.0, 2.0, 3.0])
        ssd = calculate_benford_ssd(amounts)
        assert ssd == 0.0


class TestZScore:
    def test_standard_cases(self):
        assert calculate_z_score(10.0, 5.0, 2.5) == pytest.approx(2.0)
        assert calculate_z_score(5.0, 5.0, 2.5) == pytest.approx(0.0)
        assert calculate_z_score(0.0, 5.0, 2.5) == pytest.approx(-2.0)

    def test_zero_std_returns_zero(self):
        assert calculate_z_score(10.0, 5.0, 0.0) == 0.0


class TestVelocityScore:
    def test_no_violation(self):
        events = np.array([5, 8, 3, 7])
        assert calculate_velocity_score(events, expected_max=10.0) == 0.0

    def test_violation(self):
        events = np.array([5, 8, 15, 7])
        score = calculate_velocity_score(events, expected_max=10.0)
        assert score == pytest.approx(0.5)


class TestFrozenLedger:
    def test_detected(self):
        amounts = np.array([100.0, 100.0, 100.0, 200.0])
        assert detect_frozen_ledger(amounts, min_consecutive=3) is True

    def test_not_detected(self):
        amounts = np.array([100.0, 100.0, 200.0, 200.0])
        assert detect_frozen_ledger(amounts, min_consecutive=3) is False

    def test_too_short(self):
        amounts = np.array([100.0, 100.0])
        assert detect_frozen_ledger(amounts, min_consecutive=3) is False


class TestPeerDeviation:
    def test_zscore_method(self):
        peers = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        score = calculate_peer_deviation(5.0, peers, method="zscore")
        assert score > 0

    def test_ratio_method(self):
        peers = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        score = calculate_peer_deviation(10.0, peers, method="ratio")
        assert score == pytest.approx(2.0)

    def test_invalid_method_raises(self):
        with pytest.raises(ValueError):
            calculate_peer_deviation(1.0, np.array([1.0]), method="invalid")


class TestCompositeRiskScore:
    def test_default_weights(self):
        score = calculate_composite_risk_score(
            z_score=3.0,
            benford_score=0.05,
            velocity_score=0.5,
            network_risk=0.2,
        )
        assert 0.0 <= score <= 1.0

    def test_custom_weights(self):
        weights = {"z_score": 0.5, "benford": 0.1, "velocity": 0.2, "network": 0.2}
        score = calculate_composite_risk_score(
            z_score=6.0,
            benford_score=0.2,
            velocity_score=1.0,
            network_risk=0.5,
            weights=weights,
        )
        assert 0.0 <= score <= 1.0


class TestViolationRules:
    def test_rules_exist(self):
        assert "IMPOSSIBLE_VELOCITY" in VIOLATION_RULES
        assert "FROZEN_LEDGER" in VIOLATION_RULES
        assert "EXTREME_Z_SCORE" in VIOLATION_RULES
        assert "BENFORD_VIOLATION" in VIOLATION_RULES


class TestDataUtils:
    def test_add_peer_group_stats(self):
        df = pd.DataFrame(
            {
                "group": ["A", "A", "A", "B", "B"],
                "value": [10, 20, 30, 100, 200],
            }
        )
        result = add_peer_group_stats(df, group_col="group", value_col="value")
        assert "peer_mean" in result.columns
        assert "peer_z_score" in result.columns

    def test_split_temporal(self):
        df = pd.DataFrame(
            {
                "date": pd.date_range("2020-01-01", periods=100),
                "value": range(100),
            }
        )
        train, val, test = split_temporal(df, date_col="date")
        assert len(train) > len(val)
        assert len(val) > 0
        assert len(test) > 0
