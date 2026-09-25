"""Unit and integration tests for Tableau Dashboard Agent."""

import pytest
from pathlib import Path
from tableau_dashboard_agent.agent import TableauDashboardAgent
from tableau_dashboard_agent.themes import get_theme, THEMES
from tableau_dashboard_agent.dashboard_creator import DashboardSpec


@pytest.fixture
def agent():
    return TableauDashboardAgent()


def test_themes():
    assert "executive-light" in THEMES
    assert "executive-dark" in THEMES
    theme = get_theme("executive-dark")
    assert theme.card_bg == "#151D2F"
    assert theme.get_zone_style(is_card=True)["border-width"] == 1


def test_inspect_and_lint(agent):
    sample_file = Path(r"C:\Users\User\Downloads\BKPM.twb")
    if sample_file.exists():
        meta = agent.inspect_workbook(sample_file)
        assert len(meta.worksheets) >= 1
        assert meta.is_packaged is False

        lint = agent.lint_workbook(sample_file)
        assert lint.score >= 0


def test_redesign(agent, tmp_path):
    sample_file = Path(r"C:\Users\User\Downloads\BKPM.twb")
    if sample_file.exists():
        out_file = tmp_path / "BKPM_Redesigned.twb"
        res = agent.redesign_dashboard(
            file_path=sample_file,
            output_path=out_file,
            theme="executive-light",
        )
        assert out_file.exists()
        assert len(res.dashboards_redesigned) >= 1
