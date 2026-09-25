"""Visual and structural dashboard linter inspired by tableau/Visualization-Linting.

Detects visual deception, structural flaws, anti-patterns, and layout issues
in Tableau workbooks (.twb / .twbx).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any
from lxml import etree

logger = logging.getLogger(__name__)


@dataclass
class LintFinding:
    rule_id: str
    rule_name: str
    severity: str  # "ERROR", "WARNING", "SUGGESTION"
    target: str  # Dashboard or Worksheet name
    message: str
    recommendation: str


@dataclass
class LintReport:
    target_file: str
    dashboards_analyzed: list[str]
    worksheets_analyzed: list[str]
    findings: list[LintFinding] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(f.severity == "ERROR" for f in self.findings)

    @property
    def score(self) -> int:
        """Heuristic design quality score (0 - 100)."""
        score = 100
        for f in self.findings:
            if f.severity == "ERROR":
                score -= 15
            elif f.severity == "WARNING":
                score -= 8
            elif f.severity == "SUGGESTION":
                score -= 3
        return max(0, score)

    def summary(self) -> str:
        lines = [
            f"=== Visual & Structural Lint Report: {Path(self.target_file).name} ===",
            f"Health Score: {self.score}/100",
            f"Dashboards: {', '.join(self.dashboards_analyzed) or 'None'}",
            f"Worksheets: {', '.join(self.worksheets_analyzed) or 'None'}",
            f"Total Findings: {len(self.findings)}",
            "",
        ]
        if not self.findings:
            lines.append("[PASS] Clean! No visual or structural anti-patterns detected.")
            return "\n".join(lines)

        for f in sorted(self.findings, key=lambda x: (x.severity != "ERROR", x.severity != "WARNING")):
            tag = f"[{f.severity}]"
            lines.append(f"{tag:<12} {f.rule_name} on <{f.target}>")
            lines.append(f"             Issue: {f.message}")
            lines.append(f"             Fix:   {f.recommendation}")
            lines.append("")
        return "\n".join(lines)


class VisualLinter:
    """Lints Tableau workbooks for visual integrity, responsiveness, and clean container layout."""

    def __init__(self, twb_tree: Optional[etree._ElementTree] = None):
        self.tree = twb_tree

    @classmethod
    def from_file(cls, file_path: str | Path) -> VisualLinter:
        from tableau_dashboard_agent.document_bridge import DocumentBridge
        bridge = DocumentBridge(file_path)
        twb_path, temp_dir = bridge.extract_twb()
        tree = etree.parse(str(twb_path))
        return cls(tree)

    def lint_all(self, file_path_hint: str = "workbook.twb") -> LintReport:
        if self.tree is None:
            raise ValueError("No XML tree loaded into VisualLinter.")

        root = self.tree.getroot()
        dashboards = [d.get("name", "Unnamed") for d in root.findall(".//dashboards/dashboard")]
        worksheets = [w.get("name", "Unnamed") for w in root.findall(".//worksheets/worksheet")]

        findings: list[LintFinding] = []

        # 1. Lint Worksheets
        for ws in root.findall(".//worksheets/worksheet"):
            ws_name = ws.get("name", "Unknown Sheet")
            self._lint_worksheet_scales(ws, ws_name, findings)
            self._lint_worksheet_encodings(ws, ws_name, findings)

        # 2. Lint Dashboards
        for db in root.findall(".//dashboards/dashboard"):
            db_name = db.get("name", "Unknown Dashboard")
            self._lint_dashboard_layout(db, db_name, findings)
            self._lint_dashboard_actions(db, db_name, findings)

        return LintReport(
            target_file=file_path_hint,
            dashboards_analyzed=dashboards,
            worksheets_analyzed=worksheets,
            findings=findings,
        )

    def _lint_worksheet_scales(self, ws: etree._Element, sheet_name: str, findings: list[LintFinding]):
        """Detect truncated axes or non-zero baselines on bar charts (Visualization-Linting)."""
        mark_el = ws.find(".//pane/mark")
        mark_class = mark_el.get("class", "").lower() if mark_el is not None else ""

        # Check for bar charts
        is_bar = "bar" in mark_class
        if is_bar:
            # Check custom range axes
            for axis in ws.findall(".//axes/axis"):
                custom_range = axis.find(".//customized-range")
                if custom_range is not None:
                    min_val = custom_range.get("min")
                    if min_val and float(min_val) > 0:
                        findings.append(
                            LintFinding(
                                rule_id="VL001",
                                rule_name="Bar Chart Must Start At Zero",
                                severity="ERROR",
                                target=sheet_name,
                                message=f"Bar chart axis has truncated baseline starting at {min_val} instead of 0.",
                                recommendation="Reset axis range to include 0 to avoid visual distortion of relative proportions.",
                            )
                        )

            # Check reversed axes
            for axis in ws.findall(".//axes/axis"):
                if axis.get("reversed", "").lower() == "true":
                    findings.append(
                        LintFinding(
                            rule_id="VL002",
                            rule_name="Reversed Axis Detected",
                            severity="WARNING",
                            target=sheet_name,
                            message="Continuous axis direction is reversed.",
                            recommendation="Avoid reversed axes unless standard convention demands it (e.g. golf scores, ranking tables).",
                        )
                    )

    def _lint_worksheet_encodings(self, ws: etree._Element, sheet_name: str, findings: list[LintFinding]):
        """Check for color clutter and overcrowded marks."""
        color_enc = ws.findall(".//encodings/color")
        for c in color_enc:
            column = c.get("column", "")
            # If color is assigned to a high-cardinality dimension
            if "ID" in column or "Name" in column or "Key" in column:
                findings.append(
                    LintFinding(
                        rule_id="VL003",
                        rule_name="Potential Color Over-Encoding",
                        severity="WARNING",
                        target=sheet_name,
                        message=f"Color shelf is mapped to high-cardinality dimension '{column}'.",
                        recommendation="Use color selectively for highlights or group into fewer than 7 distinct categories.",
                    )
                )

    def _lint_dashboard_layout(self, db: etree._Element, db_name: str, findings: list[LintFinding]):
        """Check for chaotic floating zones and missing container hierarchy."""
        zones = db.findall(".//zones/zone")
        if not zones:
            findings.append(
                LintFinding(
                    rule_id="DL001",
                    rule_name="Empty Dashboard",
                    severity="ERROR",
                    target=db_name,
                    message="Dashboard contains no zones or views.",
                    recommendation="Add worksheets inside structured layout containers.",
                )
            )
            return

        # Check for floating zones
        floating_zones = [z for z in zones if z.get("is-floating", "").lower() == "true" or z.get("type-v2") == "floating"]
        if len(floating_zones) > 3:
            findings.append(
                LintFinding(
                    rule_id="DL002",
                    rule_name="Excessive Floating Zones",
                    severity="WARNING",
                    target=db_name,
                    message=f"Dashboard has {len(floating_zones)} floating zones. Floating objects break across different screen resolutions and mobile layouts.",
                    recommendation="Redesign using nested Horizontal and Vertical Layout Containers with explicit padding and alignment.",
                )
            )

        # Check layout size
        size_el = db.find(".//size")
        if size_el is not None:
            max_h = size_el.get("maxheight")
            max_w = size_el.get("maxwidth")
            if max_w and int(max_w) > 1920:
                findings.append(
                    LintFinding(
                        rule_id="DL003",
                        rule_name="Excessive Canvas Width",
                        severity="SUGGESTION",
                        target=db_name,
                        message=f"Dashboard canvas width is {max_w}px, which exceeds standard 1080p executive display widths.",
                        recommendation="Use responsive Range (min 1200x800, max 1600x900) or fixed 1366x768 / 1440x900.",
                    )
                )

        # Check for header/title container
        all_zones = db.findall(".//zone")
        has_title = any(z.get("type-v2") in ("text", "title") or z.get("name") in ("Title", "Header") for z in all_zones)
        if not has_title:
            findings.append(
                LintFinding(
                    rule_id="DL004",
                    rule_name="Missing Dashboard Header Banner",
                    severity="SUGGESTION",
                    target=db_name,
                    message="No top-level title or executive header found.",
                    recommendation="Add a standardized executive header zone with Title, Subtitle, and Data Refresh timestamp.",
                )
            )

    def _lint_dashboard_actions(self, db: etree._Element, db_name: str, findings: list[LintFinding]):
        """Check for interactivity (Filter & Highlight Actions)."""
        actions = db.findall(".//actions/action")
        # Also check root actions referencing this dashboard
        root = db.getroottree().getroot()
        root_actions = [
            a for a in root.findall(".//actions/action")
            if a.find(".//source") is not None and a.find(".//source").get("dashboard") == db_name
            or db_name.lower() in etree.tostring(a).decode("utf-8", errors="ignore").lower()
        ]
        if not actions and not root_actions:
            findings.append(
                LintFinding(
                    rule_id="DL005",
                    rule_name="Lack of Dashboard Interactivity",
                    severity="SUGGESTION",
                    target=db_name,
                    message="No interactive Filter or Highlight actions configured.",
                    recommendation="Add Cross-Filtering actions so selecting data in top charts filters downstream detail views.",
                )
            )
