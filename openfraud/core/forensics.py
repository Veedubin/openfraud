"""
openfraud/core/forensics.py - Forensic Accounting Functions
===========================================================
Pure mathematical functions for fraud detection forensics.
Framework-agnostic - works with any transactional dataset.
"""

import numpy as np
from typing import Union, Dict, Optional


def calculate_benford_ssd(amounts: np.ndarray) -> float:
    """
    Calculate Sum of Squared Deviations (SSD) from Benford's Law.

    Benford's Law states that in naturally occurring datasets, the leading
    digits follow a logarithmic distribution. Significant deviation suggests
    data manipulation or synthetic data generation.

    Args:
        amounts: Array of numeric amounts (e.g., transactions, invoices)

    Returns:
        SSD score - higher values indicate greater deviation from expected

    Interpretation:
        - SSD < 0.01: Natural distribution
        - SSD 0.01-0.05: Mild deviation
        - SSD 0.05-0.10: Moderate deviation
        - SSD > 0.10: Significant deviation (possible manipulation)
    """
    # Benford's Law expected probabilities for digits 1-9
    benford_probs = np.log10(1 + 1 / np.arange(1, 10))

    # Filter positive amounts
    positive_amounts = amounts[amounts > 0]

    if len(positive_amounts) < 20:
        # Not enough data for statistical significance
        return 0.0

    # Extract first digits
    digits = np.array([int(str(abs(x))[0]) for x in positive_amounts])

    # Calculate observed distribution
    observed, _ = np.histogram(digits, bins=np.arange(1, 11), density=True)

    # Calculate Sum of Squared Deviations
    ssd = float(np.sum((observed - benford_probs) ** 2))

    return ssd


def calculate_z_score(
    value: float, population_mean: float, population_std: float
) -> float:
    """
    Calculate Z-score for a value relative to a population.

    Args:
        value: The observed value
        population_mean: Mean of the comparison population
        population_std: Standard deviation of the comparison population

    Returns:
        Z-score indicating how many standard deviations from the mean

    Interpretation:
        - |Z| < 2: Normal variation (95% of data)
        - |Z| 2-3: Moderate outlier (95-99.7% of data)
        - |Z| > 3: Extreme outlier (<0.3% of data) - investigation warranted
        - |Z| > 5: Confirmed anomaly - very suspicious
    """
    if population_std == 0:
        return 0.0
    return (value - population_mean) / population_std


def calculate_velocity_score(
    events_per_period: np.ndarray, expected_max: float
) -> float:
    """
    Calculate velocity violation score based on impossible frequency.

    Args:
        events_per_period: Array of events per time period
        expected_max: Maximum physically possible events per period

    Returns:
        Velocity violation score (0 = normal, >1 = violation)
    """
    max_observed = np.max(events_per_period)
    return max(0.0, (max_observed - expected_max) / expected_max)


def detect_frozen_ledger(amounts: np.ndarray, min_consecutive: int = 3) -> bool:
    """
    Detect "Frozen Ledger" pattern - identical amounts over consecutive periods.

    This can indicate:
    - Replay attacks (copying previous period's data)
    - Systematic fraud (billing identical amounts)
    - Data quality issues

    Args:
        amounts: Array of total amounts per period (chronological order)
        min_consecutive: Minimum consecutive identical periods to flag

    Returns:
        True if frozen ledger pattern detected
    """
    if len(amounts) < min_consecutive:
        return False

    consecutive_count = 1
    for i in range(1, len(amounts)):
        if amounts[i] == amounts[i - 1]:
            consecutive_count += 1
            if consecutive_count >= min_consecutive:
                return True
        else:
            consecutive_count = 1

    return False


def calculate_outlier_percentile(
    scores: np.ndarray, threshold_percentile: float = 99.5
) -> tuple[float, np.ndarray]:
    """
    Calculate percentile-based outlier threshold.

    Args:
        scores: Array of risk scores
        threshold_percentile: Percentile threshold (e.g., 99.5 for top 0.5%)

    Returns:
        Tuple of (threshold_value, outlier_mask)
    """
    threshold = np.percentile(scores, threshold_percentile)
    mask = scores >= threshold
    return threshold, mask


def flag_impossible_ratios(
    values: np.ndarray, theoretical_max: float, flag_threshold: float = 1.0
) -> np.ndarray:
    """
    Flag entities with physically impossible ratios.

    Args:
        values: Array of ratio values
        theoretical_max: Maximum physically possible value
        flag_threshold: Multiplier threshold for flagging

    Returns:
        Boolean array of flagged indices
    """
    return values > (theoretical_max * flag_threshold)


def calculate_peer_deviation(
    entity_value: float, peer_values: np.ndarray, method: str = "zscore"
) -> float:
    """
    Calculate how much an entity deviates from their peer group.

    Args:
        entity_value: The entity's metric value
        peer_values: Array of peer group values
        method: "zscore" or "ratio"

    Returns:
        Deviation score
    """
    if method == "zscore":
        mean = np.mean(peer_values)
        std = np.std(peer_values)
        return calculate_z_score(entity_value, mean, std)
    elif method == "ratio":
        median = np.median(peer_values)
        if median == 0:
            return 0.0
        return entity_value / median
    else:
        raise ValueError(f"Unknown method: {method}")


def calculate_composite_risk_score(
    z_score: float,
    benford_score: float,
    velocity_score: float,
    network_risk: float = 0.0,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Calculate composite risk score from multiple forensic indicators.

    Args:
        z_score: Peer deviation Z-score
        benford_score: Benford deviation score
        velocity_score: Velocity violation score (0-1)
        network_risk: Network anomaly score (0-1)
        weights: Optional custom weights for each component

    Returns:
        Composite risk score (0-1)
    """
    if weights is None:
        weights = {"z_score": 0.35, "benford": 0.15, "velocity": 0.30, "network": 0.20}

    # Normalize z_score (sigmoid to 0-1 range)
    z_normalized = 1 / (1 + np.exp(-z_score / 3))

    # Normalize benford (cap at 1)
    benford_normalized = min(benford_score * 10, 1.0)

    composite = (
        weights["z_score"] * z_normalized
        + weights["benford"] * benford_normalized
        + weights["velocity"] * velocity_score
        + weights["network"] * network_risk
    )

    return min(composite, 1.0)


# =============================================================================
# HARD VIOLATION FLAGS (Deterministic Rules)
# =============================================================================

VIOLATION_RULES = {
    "IMPOSSIBLE_VELOCITY": {
        "description": "Events exceed physically possible rate",
        "severity": "CRITICAL",
    },
    "FROZEN_LEDGER": {
        "description": "Identical amounts for 3+ consecutive periods",
        "min_consecutive": 3,
        "severity": "MEDIUM",
    },
    "EXTREME_Z_SCORE": {
        "description": "Z-score > 5.0 (extreme peer deviation)",
        "threshold": 5.0,
        "severity": "HIGH",
    },
    "BENFORD_VIOLATION": {
        "description": "Benford SSD > 0.1 (possible data manipulation)",
        "threshold": 0.1,
        "severity": "MEDIUM",
    },
}


def calculate_violation_score(
    flags: Dict[str, bool], severities: Optional[Dict[str, int]] = None
) -> int:
    """
    Calculate aggregate violation score from multiple flags.

    Args:
        flags: Dictionary of rule_name -> is_triggered
        severities: Optional mapping of severity -> score

    Returns:
        Aggregate violation score (0-100)
    """
    if severities is None:
        severities = {"CRITICAL": 50, "HIGH": 25, "MEDIUM": 10, "LOW": 5}

    score = 0
    for rule_name, triggered in flags.items():
        if triggered and rule_name in VIOLATION_RULES:
            severity = VIOLATION_RULES[rule_name].get("severity", "LOW")
            score += severities.get(severity, 5)

    return min(score, 100)
