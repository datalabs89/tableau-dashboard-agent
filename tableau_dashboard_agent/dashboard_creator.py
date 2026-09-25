"""Dashboard Creator Engine.

Creates new Tableau dashboards and workbooks with executive layouts,
proper container hierarchies, and interactivity.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any
from lxml import etree

import cwtwb.gallery as gallery
from tableau_dashboard_agent.themes import DashboardTheme, get_theme
from tableau_dashboard_agent.layout_engine import LayoutBuilder, LayoutNode
from tableau_dashboard_agent.actions_manager import ActionsManager
from tableau_dashboard_agent.schema_validator import TableauSchemaValidator, ValidationResult
from tableau_dashboard_agent.visual_linter import VisualLinter, LintReport

logger = logging.getLogger(__name__)


@dataclass
class DashboardSpec:
    title: str
    subtitle: str = "Executive Performance Overview"
    theme: str = "executive-light"
    template: str = "executive-summary"
    kpi_worksheets: list[str] = field(default_factory=list)
    chart_worksheets: list[str] = field(default_factory=list)
    detail_worksheets: list[str] = field(default_factory=list)
    width: int = 1440
    height: int = 900
    enable_filter_actions: bool = True


@dataclass
class CreationResult:
    dashboard_name: str
    output_file: str
    template_used: str
    theme_applied: str
    worksheets_included: list[str]
    validation_result: ValidationResult
    lint_report: LintReport

    def summary(self) -> str:
        lines = [
            "===========================================================",
            "           TABLEAU DASHBOARD CREATION SUMMARY",
            "===========================================================",
            f"Dashboard Name:      {self.dashboard_name}",
            f"Output File:         {Path(self.output_file).name}",
            f"Template:            {self.template_used}",
            f"Theme:               {self.theme_applied}",
            f"Included Sheets:     {', '.join(self.worksheets_included)}",
            f"Health Score:        {self.lint_report.score}/100",
            f"Schema Validation:   {'VALID' if self.validation_result.valid else 'VALID WITH WARNINGS'} ({self.validation_result.schema_version})",
            "===========================================================",
        ]
        return "\n".join(lines)


class DashboardCreator:
    """Builds new executive dashboards in new or existing Tableau workbooks."""

    def __init__(self):
        self.validator = TableauSchemaValidator()

    def recommend_templates(
        self,
        kpi_count: int,
        chart_count: int,
        primary_intent: str = "overview",
        has_temporal: bool = False,
        has_geographic: bool = False,
    ) -> list[dict[str, Any]]:
        """Recommend best layout templates based on user requirements."""
        req = gallery.DashboardRequirements(
            kpi_count=kpi_count,
            chart_count=chart_count,
            primary_intent=primary_intent,
            has_temporal_data=has_temporal,
            has_geographic_data=has_geographic,
        )
        recs = gallery.recommend_gallery_templates(req)
        return [
            {
                "template": r.template,
                "title": r.title,
                "score": r.score,
                "matches": list(r.matched),
            }
            for r in recs
        ]

    def create_dashboard_in_workbook(
        self,
        workbook_path: str | Path,
        spec: DashboardSpec,
        output_path: Optional[str | Path] = None,
    ) -> CreationResult:
        """Create a new dashboard inside an existing workbook (.twb or .twbx)."""
        from tableau_dashboard_agent.document_bridge import DocumentBridge
        in_p = Path(workbook_path).resolve()
        bridge = DocumentBridge(in_p)
        twb_path, temp_dir = bridge.extract_twb()

        tree = etree.parse(str(twb_path))
        root = tree.getroot()

        # Find or create <dashboards> element
        dashboards_el = root.find("dashboards")
        if dashboards_el is None:
            # Place after worksheets if exists
            ws_el = root.find("worksheets")
            if ws_el is not None:
                dashboards_el = etree.Element("dashboards")
                root.insert(root.index(ws_el) + 1, dashboards_el)
            else:
                dashboards_el = etree.SubElement(root, "dashboards")

        # Create new <dashboard>
        db_el = etree.SubElement(dashboards_el, "dashboard")
        db_el.set("name", spec.title)

        # Set size
        size_el = etree.SubElement(db_el, "size")
        size_el.set("maxheight", str(spec.height))
        size_el.set("maxwidth", str(spec.width))
        size_el.set("minheight", str(spec.height))
        size_el.set("minwidth", str(spec.width))

        # Build layout using LayoutBuilder
        theme = get_theme(spec.theme)
        builder = LayoutBuilder(theme=theme, width=spec.width, height=spec.height)

        layout_tree = builder.create_executive_layout(
            title=spec.title,
            subtitle=spec.subtitle,
            kpi_sheets=spec.kpi_worksheets,
            main_sheets=spec.chart_worksheets,
            detail_sheets=spec.detail_worksheets,
        )

        builder.inject_layout_into_dashboard(db_el, layout_tree)

        # Add cross-filtering actions
        if spec.enable_filter_actions and spec.chart_worksheets:
            source = spec.chart_worksheets[0]
            targets = [s for s in spec.chart_worksheets[1:] + spec.detail_worksheets if s != source]
            if targets:
                ActionsManager.add_filter_action(
                    root_el=root,
                    dashboard_name=spec.title,
                    source_sheet=source,
                    target_sheets=targets,
                    action_caption=f"Cross-Filter from {source}",
                )

        # Apply Micro-Formatting & Visual Hygiene
        from tableau_dashboard_agent.micro_formatter import MicroFormatter
        MicroFormatter.apply_entire_view(root, spec.kpi_worksheets + spec.chart_worksheets + spec.detail_worksheets)
        for ws in root.findall(".//worksheets/worksheet"):
            MicroFormatter.clean_chartjunk(ws)

        # Save XML
        tree.write(str(twb_path), encoding="utf-8", xml_declaration=True)

        # Validate schema
        val_result = self.validator.validate_xml_root(root)

        # Lint
        linter = VisualLinter(tree)
        lint_report = linter.lint_all(file_path_hint=in_p.name)

        # Finalize output file
        out_p = Path(output_path).resolve() if output_path else in_p.parent / f"{in_p.stem}_with_{spec.title.replace(' ', '_')}{in_p.suffix}"
        if bridge.is_packaged:
            bridge.repack_twbx(temp_dir, out_p)
            if temp_dir and temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            import shutil
            shutil.copy2(twb_path, out_p)

        all_sheets = spec.kpi_worksheets + spec.chart_worksheets + spec.detail_worksheets
        return CreationResult(
            dashboard_name=spec.title,
            output_file=str(out_p),
            template_used=spec.template,
            theme_applied=theme.name,
            worksheets_included=all_sheets,
            validation_result=val_result,
            lint_report=lint_report,
        )
