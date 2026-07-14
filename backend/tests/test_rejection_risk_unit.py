"""Unit tests for rejection-risk scoring semantics."""

import pytest

from src.services.rejection_risk import (
    CONTRADICTORY_PAIRS,
    RejectionRiskEngine,
    RiskLevel,
)


@pytest.mark.parametrize(
    ("assess_kwargs", "expected_score", "expected_level"),
    [
        ({}, 0, RiskLevel.LOW),
        (
            {
                "drg_result": {"avg_los": 7},
                "patient_info": {"days_of_stay": 14},
            },
            10,
            RiskLevel.LOW,
        ),
        (
            {
                "drg_result": {"weight": 1.0},
                "hospital_cost": 16_800,
            },
            30,
            RiskLevel.MEDIUM,
        ),
        (
            {
                "drg_result": {"weight": 1.0},
                "hospital_cost": 24_000,
            },
            60,
            RiskLevel.HIGH,
        ),
    ],
)
def test_assess_score_increases_with_risk_severity(
    assess_kwargs: dict,
    expected_score: int,
    expected_level: RiskLevel,
) -> None:
    report = RejectionRiskEngine().assess(
        primary_diag={},
        secondary_diags=[],
        procedures=[],
        **assess_kwargs,
    )

    assert report.risk_score == expected_score
    assert report.overall_risk == expected_level


def test_assess_does_not_mutate_contradictory_rules() -> None:
    def snapshot_rules() -> tuple[tuple[frozenset[str], frozenset[str], str], ...]:
        return tuple(
            (frozenset(left), frozenset(right), reason)
            for left, right, reason in CONTRADICTORY_PAIRS
        )

    initial_rules = snapshot_rules()
    left_term = next(iter(CONTRADICTORY_PAIRS[0][0]))
    right_term = next(iter(CONTRADICTORY_PAIRS[0][1]))
    diagnoses = [{"name": left_term}, {"name": right_term}]
    engine = RejectionRiskEngine()

    first_report = engine.assess(
        primary_diag={},
        secondary_diags=diagnoses,
        procedures=[],
    )
    second_report = engine.assess(
        primary_diag={},
        secondary_diags=diagnoses,
        procedures=[],
    )

    first_contradictions = [risk for risk in first_report.risks if risk.rule_id == "RR-003"]
    second_contradictions = [risk for risk in second_report.risks if risk.rule_id == "RR-003"]

    assert snapshot_rules() == initial_rules
    assert len(first_contradictions) == 1
    assert len(second_contradictions) == 1
