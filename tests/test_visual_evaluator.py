"""Unit tests for VisualEvaluator."""

from pathlib import Path
from tableau_dashboard_agent.visual_evaluator import VisualEvaluator


def test_visual_scorecard():
    sample_wb = Path(r"C:\Users\User\Documents\Superstore_Modern_Executive_Dashboard.twbx")
    if sample_wb.exists():
        scorecard = VisualEvaluator.evaluate_dashboard(sample_wb)
        assert scorecard.overall_score >= 80
        assert len(scorecard.metrics) >= 3
        summary = scorecard.summary()
        assert "VISUAL DESIGN SCORECARD" in summary
