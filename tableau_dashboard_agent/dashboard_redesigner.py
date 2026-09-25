"""Dashboard Redesign Engine.

Transforms legacy, cluttered, or floating Tableau dashboards into structured,
executive-grade dashboards with clean container hierarchies and interactivity.
"""

from __future__ import annotations

import copy
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any
from lxml import etree

from tableau_dashboard_agent.document_bridge import DocumentBridge
from tableau_dashboard_agent.visual_linter import VisualLinter, LintReport
from tableau_dashboard_agent.themes import DashboardTheme, get_theme
from tableau_dashboard_agent.layout_engine import LayoutBuilder, LayoutNode
from tableau_dashboard_agent.actions_manager import ActionsManager
from tableau_dashboard_agent.schema_validator import TableauSchemaValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class RedesignResult:
    input_file: str
    output_file: str
    pre_lint_report: LintReport
    post_lint_report: LintReport
    validation_result: ValidationResult
    dashboards_redesigned: list[str]
    theme_applied: str

    def summary(self) -> str:
        lines = [
            "===========================================================",
            "           TABLEAU DASHBOARD REDESIGN SUMMARY",
            "===========================================================",
            f"Input File:        {Path(self.input_file).name}",
            f"Output File:       {Path(self.output_file).name}",
            f"Theme Applied:     {self.theme_applied}",
            f"Redesigned Sheets: {', '.join(self.dashboards_redesigned)}",
            "",
            "--- Health Score Progression ---",
            f"Pre-Redesign Score:  {self.pre_lint_report.score}/100 ({len(self.pre_lint_report.findings)} issues)",
            f"Post-Redesign Score: {self.post_lint_report.score}/100 ({len(self.post_lint_report.findings)} issues)",
            "",
            "--- Schema Validation ---",
            f"Status:   {'VALID' if self.validation_result.valid else 'VALID WITH WARNINGS'}",
            f"Version:  {self.validation_result.schema_version}",
            "===========================================================",
        ]
        return "\n".join(lines)


class DashboardRedesigner:
    """Orchestrates comprehensive redesign of Tableau dashboards."""

    def __init__(self, theme_name: str = "executive-light"):
        self.theme: DashboardTheme = get_theme(theme_name)
        self.layout_builder = LayoutBuilder(theme=self.theme)
        self.validator = TableauSchemaValidator()

    def redesign_workbook(
        self,
        input_path: str | Path,
        output_path: Optional[str | Path] = None,
        target_dashboard: Optional[str] = None,
        canvas_width: int = 1440,
        canvas_height: int = 900,
        add_filter_actions: bool = True,
    ) -> RedesignResult:
        """Fully redesign one or all dashboards in a .twb or .twbx workbook."""
        in_p = Path(input_path).resolve()
        if not in_p.exists():
            raise FileNotFoundError(f"Input workbook not found: {in_p}")

        bridge = DocumentBridge(in_p)
        twb_path, temp_dir = bridge.extract_twb()

        # Step 1: Pre-redesign audit
        tree = etree.parse(str(twb_path))
        pre_linter = VisualLinter(copy.deepcopy(tree))
        pre_lint = pre_linter.lint_all(file_path_hint=in_p.name)

        root = tree.getroot()
        dashboards = root.findall(".//dashboards/dashboard")
        if not dashboards:
            # If no dashboard exists, create one from worksheets
            logger.info("No dashboard found. Creating new executive dashboard from worksheets.")
            new_db = self._create_dashboard_from_worksheets(root, "Executive Overview")
            dashboards = [new_db]

        redesigned_names: list[str] = []

        # Step 2: Redesign each targeted dashboard
        for db in dashboards:
            db_name = db.get("name", "Dashboard")
            if target_dashboard and db_name != target_dashboard:
                continue

            self._redesign_single_dashboard(
                root, db, db_name,
                canvas_width=canvas_width,
                canvas_height=canvas_height,
                add_actions=add_filter_actions,
            )
            redesigned_names.append(db_name)

        # Step 2.5: Apply Micro-Formatting & Visual Hygiene
        from tableau_dashboard_agent.micro_formatter import MicroFormatter
        MicroFormatter.apply_entire_view(root)
        for ws in root.findall(".//worksheets/worksheet"):
            MicroFormatter.clean_chartjunk(ws)

        # Step 3: Write modified XML back
        tree.write(str(twb_path), encoding="utf-8", xml_declaration=True)

        # Step 4: Validate against official schema
        val_result = self.validator.validate_xml_root(root)

        # Step 5: Post-redesign audit
        post_linter = VisualLinter(tree)
        post_lint = post_linter.lint_all(file_path_hint=in_p.name)

        # Step 6: Save output
        if output_path is None:
            stem = in_p.stem
            suffix = in_p.suffix
            out_p = in_p.parent / f"{stem}_Redesigned{suffix}"
        else:
            out_p = Path(output_path).resolve()

        if bridge.is_packaged:
            bridge.repack_twbx(temp_dir, out_p)
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            shutil.copy2(twb_path, out_p)

        return RedesignResult(
            input_file=str(in_p),
            output_file=str(out_p),
            pre_lint_report=pre_lint,
            post_lint_report=post_lint,
            validation_result=val_result,
            dashboards_redesigned=redesigned_names,
            theme_applied=self.theme.name,
        )

    def _redesign_single_dashboard(
        self,
        root: etree._Element,
        db: etree._Element,
        db_name: str,
        canvas_width: int,
        canvas_height: int,
        add_actions: bool,
    ):
        """Redesign an individual dashboard XML node."""
        # 1. Standardize Size
        size_el = db.find("size")
        if size_el is None:
            size_el = etree.SubElement(db, "size")
        size_el.set("maxheight", str(canvas_height))
        size_el.set("maxwidth", str(canvas_width))
        size_el.set("minheight", str(canvas_height))
        size_el.set("minwidth", str(canvas_width))

        # 2. Extract existing worksheets used in this dashboard
        used_worksheets: list[str] = []
        for zone in db.findall(".//zones//zone"):
            name = zone.get("name")
            if name and zone.get("type-v2") in ("widget", None):
                if name not in used_worksheets and not name.startswith("Title"):
                    used_worksheets.append(name)

        if not used_worksheets:
            # Fallback to workbook worksheets
            all_sheets = [ws.get("name") for ws in root.findall(".//worksheets/worksheet") if ws.get("name")]
            used_worksheets = all_sheets[:6]

        # 3. Classify worksheets into functional roles
        kpis, mains, details = self._classify_worksheets(used_worksheets, root)

        # 4. Generate structured layout
        layout_tree = self.layout_builder.create_executive_layout(
            title=f"{db_name}",
            subtitle="Executive Performance & Decision Support",
            kpi_sheets=kpis,
            main_sheets=mains,
            detail_sheets=details,
        )

        # 5. Inject compiled zones
        self.layout_builder.inject_layout_into_dashboard(db, layout_tree)

        # 6. Add Interactivity (Filter Actions)
        if add_actions and mains:
            source = mains[0]
            targets = [s for s in mains[1:] + details if s != source]
            if targets:
                ActionsManager.add_filter_action(
                    root_el=root,
                    dashboard_name=db_name,
                    source_sheet=source,
                    target_sheets=targets,
                    action_caption=f"Cross-Filter from {source}",
                )

    def _classify_worksheets(
        self,
        sheet_names: list[str],
        root: etree._Element,
    ) -> tuple[list[str], list[str], list[str]]:
        """Categorize sheets into KPI cards, Main charts, and Detail tables based on naming and marks."""
        kpis: list[str] = []
        mains: list[str] = []
        details: list[str] = []

        for name in sheet_names:
            lname = name.lower()
            if any(k in lname for k in ["kpi", "card", "metric", "total", "ban", "stat", "score"]):
                kpis.append(name)
            elif any(k in lname for k in ["detail", "table", "summary", "list", "grid"]):
                details.append(name)
            else:
                mains.append(name)

        # If everything fell into mains, balance them sensibly
        if not kpis and len(mains) > 4:
            kpis = mains[:2]
            mains = mains[2:]

        return kpis, mains, details

    def _create_dashboard_from_worksheets(self, root: etree._Element, dashboard_name: str) -> etree._Element:
        """Create a new dashboard element when none exists."""
        dashboards_el = root.find("dashboards")
        if dashboards_el is None:
            dashboards_el = etree.SubElement(root, "dashboards")

        db = etree.SubElement(dashboards_el, "dashboard")
        db.set("name", dashboard_name)
        return db
