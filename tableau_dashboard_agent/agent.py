"""Tableau Dashboard Agent Core.

Provides high-level autonomous orchestration for inspecting, linting,
creating, and redesigning Tableau workbooks and dashboards.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any

from tableau_dashboard_agent.document_bridge import DocumentBridge, WorkbookMetadata
from tableau_dashboard_agent.schema_validator import TableauSchemaValidator, ValidationResult
from tableau_dashboard_agent.visual_linter import VisualLinter, LintReport
from tableau_dashboard_agent.dashboard_redesigner import DashboardRedesigner, RedesignResult
from tableau_dashboard_agent.dashboard_creator import DashboardCreator, DashboardSpec, CreationResult
from tableau_dashboard_agent.themes import get_theme, THEMES

logger = logging.getLogger(__name__)


class TableauDashboardAgent:
    """Agent specialized in creating, auditing, and redesigning Tableau dashboards."""

    def __init__(self, default_theme: str = "executive-light"):
        self.default_theme = default_theme
        self.validator = TableauSchemaValidator()
        self.creator = DashboardCreator()
        self.redesigner = DashboardRedesigner(theme_name=default_theme)

    def inspect_workbook(self, file_path: str | Path) -> WorkbookMetadata:
        """Inspect datasources, connections, worksheets, and dashboards."""
        bridge = DocumentBridge(file_path)
        return bridge.inspect()

    def lint_workbook(self, file_path: str | Path) -> LintReport:
        """Run visual, analytical, and structural linting (Visualization-Linting rules)."""
        linter = VisualLinter.from_file(file_path)
        return linter.lint_all(file_path_hint=Path(file_path).name)

    def validate_schema(self, file_path: str | Path) -> ValidationResult:
        """Validate workbook XML against official Tableau Document Schemas."""
        bridge = DocumentBridge(file_path)
        twb_path, _ = bridge.extract_twb()
        return self.validator.validate_file(twb_path)

    def redesign_dashboard(
        self,
        file_path: str | Path,
        output_path: Optional[str | Path] = None,
        target_dashboard: Optional[str] = None,
        theme: Optional[str] = None,
        canvas_width: int = 1440,
        canvas_height: int = 900,
        add_filter_actions: bool = True,
    ) -> RedesignResult:
        """Redesign one or all dashboards in a workbook into executive layouts."""
        active_theme = theme or self.default_theme
        redesigner = DashboardRedesigner(theme_name=active_theme)
        return redesigner.redesign_workbook(
            input_path=file_path,
            output_path=output_path,
            target_dashboard=target_dashboard,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            add_filter_actions=add_filter_actions,
        )

    def create_dashboard(
        self,
        file_path: str | Path,
        title: str,
        kpis: list[str] = (),
        charts: list[str] = (),
        details: list[str] = (),
        subtitle: str = "Executive Performance Overview",
        theme: Optional[str] = None,
        output_path: Optional[str | Path] = None,
        width: int = 1440,
        height: int = 900,
    ) -> CreationResult:
        """Create a new dashboard inside an existing workbook."""
        spec = DashboardSpec(
            title=title,
            subtitle=subtitle,
            theme=theme or self.default_theme,
            kpi_worksheets=list(kpis),
            chart_worksheets=list(charts),
            detail_worksheets=list(details),
            width=width,
            height=height,
        )
        return self.creator.create_dashboard_in_workbook(
            workbook_path=file_path,
            spec=spec,
            output_path=output_path,
        )

    def swap_datasource_connection(
        self,
        file_path: str | Path,
        server: Optional[str] = None,
        dbname: Optional[str] = None,
        username: Optional[str] = None,
        port: Optional[str] = None,
        datasource_name: Optional[str] = None,
        output_path: Optional[str | Path] = None,
    ) -> Path:
        """Update connection parameters using tableau/document-api-python."""
        bridge = DocumentBridge(file_path)
        return bridge.update_connection(
            datasource_name=datasource_name,
            server=server,
            dbname=dbname,
            username=username,
            port=port,
            output_path=output_path,
        )

    def apply_theme(
        self,
        file_path: str | Path,
        theme_name: str,
        output_path: Optional[str | Path] = None,
        data_file_path: Optional[str | Path] = None,
    ) -> Path:
        """Apply an executive theme (executive-light, executive-dark, minimalist-slate) to a workbook."""
        from tableau_dashboard_agent.theme_styler import ThemeStyler
        styler = ThemeStyler(theme_name)
        return styler.style_workbook_file(file_path, output_file=output_path, data_file_path=data_file_path)

    def learn_from_reference(self, source: str, update_skill: bool = True) -> Any:
        """Autonomously ingest and learn patterns from Tableau Public URL or local .twbx."""
        from tableau_dashboard_agent.reference_learner import ReferenceLearner
        learner = ReferenceLearner()
        return learner.learn(source, update_skill_docs=update_skill)

    def execute_request(self, command: str, file_path: str | Path, **kwargs) -> Any:
        """Natural instruction router for autonomous tasks."""
        cmd = command.lower().strip()
        if "learn" in cmd or "ingest" in cmd or "absorb" in cmd:
            update_docs = kwargs.get("update_skill", True)
            return self.learn_from_reference(str(file_path), update_skill=update_docs)
        elif "theme" in cmd or "dark" in cmd or "slate" in cmd:
            theme = kwargs.get("theme", "executive-dark")
            out = kwargs.get("output_path")
            return self.apply_theme(file_path, theme_name=theme, output_path=out)
        elif "redesign" in cmd or "layout" in cmd or "rebuild" in cmd:
            theme = kwargs.get("theme", self.default_theme)
            target = kwargs.get("target_dashboard")
            out = kwargs.get("output_path")
            return self.redesign_dashboard(file_path, output_path=out, target_dashboard=target, theme=theme)
        elif "lint" in cmd or "audit" in cmd or "check" in cmd:
            return self.lint_workbook(file_path)
        elif "validate" in cmd or "schema" in cmd:
            return self.validate_schema(file_path)
        elif "inspect" in cmd or "metadata" in cmd:
            return self.inspect_workbook(file_path)
        elif "swap" in cmd or "connection" in cmd:
            return self.swap_datasource_connection(file_path, **kwargs)
        else:
            raise ValueError(f"Unknown agent command '{command}'. Supported: learn, redesign, lint, validate, inspect, swap, theme.")
