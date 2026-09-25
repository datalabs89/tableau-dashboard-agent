"""Reference Learner and Ingestion Pipeline for Tableau Public and Local Workbooks.

Enables the agent to autonomously digest, decompile, and learn from real-world
elite Tableau dashboards:
- Downloads .twbx from Tableau Public URLs
- Dissects container layout architecture
- Mines color palettes, borders, fonts -> auto-creates new DashboardThemes
- Extracts advanced business calculations (LODs, period offsets, parameter switchers)
- Catalogs interactive actions (De-highlight tricks, parameter actions, cross-filters)
- Automatically updates the agent's SKILL.md reference catalog
"""

from __future__ import annotations

import collections
import io
import json
import logging
import os
import re
import shutil
import tempfile
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any
from lxml import etree

from tableau_dashboard_agent.themes import DashboardTheme, THEMES, register_custom_theme

logger = logging.getLogger(__name__)


@dataclass
class LearnedCalculatedField:
    name: str
    formula: str
    category: str  # "LOD", "Period/Date", "Dynamic Metric", "Table Calc", "Measure"
    datatype: Optional[str] = None


@dataclass
class LearnedPalette:
    canvas_bg: str = "#F8FAFC"
    card_bg: str = "#FFFFFF"
    card_border: str = "#E2E8F0"
    text_primary: str = "#0F172A"
    text_secondary: str = "#475569"
    accent_primary: str = "#2563EB"
    positive_color: str = "#10B981"
    negative_color: str = "#EF4444"
    font_family: str = "Tableau Bold"


@dataclass
class LearnedPatternSummary:
    source_name: str
    source_type: str  # "Tableau Public" or "Local File"
    dashboards: list[str]
    dimensions: str
    palette: LearnedPalette
    theme_registered: str
    total_calculations: int
    advanced_calculations: list[LearnedCalculatedField]
    actions_found: list[str]
    skill_updated: bool
    storage_dir: str

    def summary(self) -> str:
        lines = [
            "===========================================================",
            f"       TABLEAU LEARNER REPORT: {self.source_name}",
            "===========================================================",
            f"Source Type:         {self.source_type}",
            f"Dashboards ({len(self.dashboards)}):     {', '.join(self.dashboards)}",
            f"Dimensions:          {self.dimensions}",
            "",
            "--- Extracted Design Palette ---",
            f"  * Canvas Background: {self.palette.canvas_bg}",
            f"  * Card Background:   {self.palette.card_bg}",
            f"  * Card Border:       {self.palette.card_border}",
            f"  * Primary Accent:    {self.palette.accent_primary}",
            f"  * Positive Delta:    {self.palette.positive_color}",
            f"  * Negative Delta:    {self.palette.negative_color}",
            f"  * Font Family:       {self.palette.font_family}",
            f"  --> Registered Theme: '{self.theme_registered}'",
            "",
            f"--- Business Calculations ({self.total_calculations} total, {len(self.advanced_calculations)} key patterns) ---",
        ]
        for c in self.advanced_calculations[:6]:
            clean_f = c.formula.replace("\n", " ").strip()
            clean_f = clean_f.encode("ascii", "replace").decode("ascii")
            clean_name = c.name.encode("ascii", "replace").decode("ascii")
            if len(clean_f) > 75:
                clean_f = clean_f[:72] + "..."
            lines.append(f"  * [{c.category}] {clean_name:<24} = {clean_f}")

        if self.actions_found:
            lines.append("")
            lines.append(f"--- Interactive Actions ({len(self.actions_found)}) ---")
            for a in self.actions_found[:5]:
                clean_a = a.encode("ascii", "replace").decode("ascii")
                lines.append(f"  * {clean_a}")

        lines.append("")
        lines.append(f"Skill Catalog Updated: {'YES (C:/Users/User/.agents/skills/tableau-dashboard-designer/SKILL.md)' if self.skill_updated else 'NO'}")
        lines.append(f"Knowledge Vault Saved: {self.storage_dir}")
        lines.append("===========================================================")
        return "\n".join(lines)


class ReferenceLearner:
    """Ingests and learns patterns from Tableau Public links or local workbooks."""

    def __init__(self, vault_dir: Optional[str | Path] = None):
        if vault_dir:
            self.vault_dir = Path(vault_dir).resolve()
        else:
            self.vault_dir = Path(__file__).parent.parent / "references"
        self.vault_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def resolve_source(cls, source: str) -> tuple[str, str, Path]:
        """Resolves URL or local path to (name, source_type, local_file_path)."""
        src = source.strip()
        if src.startswith("http://") or src.startswith("https://"):
            parsed = urllib.parse.urlparse(src)
            match = re.search(r"/views/([^/?&#]+)/([^/?&#]+)", parsed.path)
            if not match:
                raise ValueError(f"Could not parse Tableau Public view URL: {src}")

            wb_name, view_name = match.groups()
            download_url = f"https://public.tableau.com/workbooks/{wb_name}.twb"
            logger.info("Downloading Tableau Public workbook from %s ...", download_url)

            req = urllib.request.Request(download_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            try:
                with urllib.request.urlopen(req) as resp:
                    data = resp.read()
            except Exception as e:
                raise RuntimeError(f"Failed to download workbook from {download_url}: {e}")

            is_zip = zipfile.is_zipfile(io.BytesIO(data))
            ext = ".twbx" if is_zip else ".twb"

            temp_file = Path(tempfile.gettempdir()) / f"{wb_name}{ext}"
            temp_file.write_bytes(data)
            return wb_name, "Tableau Public", temp_file
        else:
            p = Path(src).resolve()
            if not p.exists():
                raise FileNotFoundError(f"Local file not found: {p}")
            return p.stem, "Local File", p

    def learn(self, source: str, update_skill_docs: bool = True) -> LearnedPatternSummary:
        """Main entry point to learn patterns from a workbook or URL."""
        source_name, source_type, local_path = self.resolve_source(source)
        slug = re.sub(r"[^a-zA-Z0-9_-]", "_", source_name).lower()
        target_vault = self.vault_dir / slug
        target_vault.mkdir(parents=True, exist_ok=True)

        # 1. Extract XML and images
        is_zip = zipfile.is_zipfile(str(local_path))
        twb_xml: bytes
        images_dir = target_vault / "images"
        images_dir.mkdir(exist_ok=True)

        if is_zip:
            with zipfile.ZipFile(str(local_path), "r") as zf:
                twb_names = [n for n in zf.namelist() if n.endswith(".twb")]
                if not twb_names:
                    raise ValueError(f"No .twb found in .twbx archive: {local_path}")
                twb_xml = zf.read(twb_names[0])

                # Extract images
                for name in zf.namelist():
                    if "image" in name.lower() or name.lower().endswith((".png", ".jpg", ".jpeg", ".svg")):
                        try:
                            clean_filename = Path(name).name
                            (images_dir / clean_filename).write_bytes(zf.read(name))
                        except Exception:
                            pass
        else:
            twb_xml = local_path.read_bytes()

        # Parse XML
        tree = etree.fromstring(twb_xml)

        # 2. Extract Dashboards & Dimensions
        dashboards: list[str] = [d.get("name", "Dashboard") for d in tree.findall(".//dashboards/dashboard")]
        size_el = tree.find(".//dashboards/dashboard/size")
        dim_str = "1440x900 (Default)"
        if size_el is not None:
            w = size_el.get("maxwidth") or size_el.get("minwidth")
            h = size_el.get("maxheight") or size_el.get("minheight")
            if w and h:
                dim_str = f"{w}x{h}"

        # 3. Mine Color Palette & Aesthetics
        palette = self._mine_palette(tree)

        # 4. Register as a custom theme
        theme_slug = f"learned-{slug[:20].strip('_')}"
        new_theme = DashboardTheme(
            name=f"Learned: {source_name[:25]}",
            description=f"Auto-mined theme from {source_type} ({source_name}).",
            canvas_bg=palette.canvas_bg,
            card_bg=palette.card_bg,
            card_border=palette.card_border,
            card_border_width=1,
            card_padding=8,
            text_primary=palette.text_primary,
            text_secondary=palette.text_secondary,
            text_muted="#888888",
            accent_primary=palette.accent_primary,
            accent_secondary="#3B82F6",
            positive_color=palette.positive_color,
            negative_color=palette.negative_color,
            font_family=palette.font_family,
            title_font_size=18,
            subtitle_font_size=11,
            kpi_number_font_size=26,
            body_font_size=10,
        )
        register_custom_theme(theme_slug, new_theme)

        # 5. Mine Calculated Fields
        all_calcs, advanced_calcs = self._mine_calculations(tree)

        # 6. Mine Interactive Actions
        actions = self._mine_actions(tree)

        # Save extracted knowledge to JSON
        vault_metadata = {
            "source_name": source_name,
            "source_type": source_type,
            "dashboards": dashboards,
            "dimensions": dim_str,
            "palette": palette.__dict__,
            "theme_registered": theme_slug,
            "calculations_count": len(all_calcs),
            "advanced_calculations": [c.__dict__ for c in advanced_calcs],
            "actions": actions,
        }
        (target_vault / "learned_knowledge.json").write_text(json.dumps(vault_metadata, indent=2), encoding="utf-8")

        # 7. Update SKILL.md
        skill_updated = False
        if update_skill_docs:
            skill_updated = self._update_skill_docs(source_name, source_type, dim_str, palette, advanced_calcs, actions)

        return LearnedPatternSummary(
            source_name=source_name,
            source_type=source_type,
            dashboards=dashboards,
            dimensions=dim_str,
            palette=palette,
            theme_registered=theme_slug,
            total_calculations=len(all_calcs),
            advanced_calculations=advanced_calcs,
            actions_found=actions,
            skill_updated=skill_updated,
            storage_dir=str(target_vault),
        )

    def _mine_palette(self, tree: etree._Element) -> LearnedPalette:
        """Extract hex colors and typography from workbook XML."""
        colors_seen: collections.Counter[str] = collections.Counter()
        fonts_seen: collections.Counter[str] = collections.Counter()

        # Canvas backgrounds
        for fmt in tree.findall(".//dashboards/dashboard/style//style-rule[@element='table']/format[@attr='background-color']"):
            val = fmt.get("value")
            if val and val.startswith("#") and len(val) in (7, 9):
                colors_seen[val[:7].upper()] += 10

        # Zone-style colors
        for zs in tree.findall(".//zone-style/format"):
            attr = zs.get("attr")
            val = zs.get("value")
            if val and val.startswith("#") and len(val) in (7, 9):
                c = val[:7].upper()
                if attr == "background-color":
                    colors_seen[c] += 5
                elif attr == "border-color":
                    colors_seen[c] += 3

        # Text runs
        for run in tree.findall(".//run"):
            col = run.get("fontcolor")
            if col and col.startswith("#") and len(col) in (7, 9):
                colors_seen[col[:7].upper()] += 2
            fnt = run.get("fontname")
            if fnt:
                fonts_seen[fnt] += 1

        # Classify colors
        canvas_bg = "#F8FAFC"
        card_bg = "#FFFFFF"
        card_border = "#E2E8F0"
        text_primary = "#0F172A"
        accent_primary = "#2563EB"
        positive_color = "#10B981"
        negative_color = "#EF4444"

        # Determine top light colors for backgrounds
        sorted_colors = [c for c, _ in colors_seen.most_common()]
        for c in sorted_colors:
            # Simple luminance check
            try:
                r = int(c[1:3], 16)
                g = int(c[3:5], 16)
                b = int(c[5:7], 16)
                lum = (0.299 * r + 0.587 * g + 0.114 * b)
                if lum > 230 and canvas_bg == "#F8FAFC":
                    canvas_bg = c
                elif lum < 80 and text_primary == "#0F172A":
                    text_primary = c
                elif 80 <= lum <= 200:
                    if g > r + 30 and g > b + 30:
                        positive_color = c
                    elif r > g + 40 and r > b + 40:
                        negative_color = c
                    elif b > r + 20:
                        accent_primary = c
            except Exception:
                continue

        top_font = fonts_seen.most_common(1)
        font_family = top_font[0][0] if top_font else "Tableau Bold"

        return LearnedPalette(
            canvas_bg=canvas_bg,
            card_bg=card_bg,
            card_border=card_border,
            text_primary=text_primary,
            text_secondary="#475569",
            accent_primary=accent_primary,
            positive_color=positive_color,
            negative_color=negative_color,
            font_family=font_family,
        )

    def _mine_calculations(self, tree: etree._Element) -> tuple[list[LearnedCalculatedField], list[LearnedCalculatedField]]:
        """Identify advanced formulas (LOD, period logic, parameter switchers)."""
        all_calcs: list[LearnedCalculatedField] = []
        advanced: list[LearnedCalculatedField] = []

        for col in tree.findall(".//datasources//column"):
            calc = col.find("calculation")
            if calc is None or not calc.get("formula"):
                continue

            formula = calc.get("formula").strip()
            name = col.get("caption") or col.get("name") or "Calc"
            # Clean tableau bracket formatting from name if present
            clean_name = name.replace("[", "").replace("]", "")

            f_upper = formula.upper()
            category = "Measure"

            if any(k in f_upper for k in ["{FIXED", "{INCLUDE", "{EXCLUDE", "{ MAX", "{ MIN"]):
                category = "LOD"
            elif any(k in f_upper for k in ["DATETRUNC", "DATEADD", "DATEDIFF"]):
                category = "Period/Date"
            elif "CASE" in f_upper and "WHEN" in f_upper:
                category = "Dynamic Metric"
            elif any(k in f_upper for k in ["WINDOW_", "RUNNING_", "RANK("]):
                category = "Table Calc"

            calc_obj = LearnedCalculatedField(name=clean_name, formula=formula, category=category)
            all_calcs.append(calc_obj)

            if category != "Measure" and len(formula) > 10:
                advanced.append(calc_obj)

        return all_calcs, advanced

    def _mine_actions(self, tree: etree._Element) -> list[str]:
        """Catalog interactive dashboard actions."""
        actions: list[str] = []
        for a in tree.findall(".//actions/action"):
            cap = a.get("caption") or a.get("name") or "Action"
            cmd = a.find(".//command")
            cmd_type = cmd.get("command") if cmd is not None else "unknown"
            actions.append(f"{cap} ({cmd_type})")
        return actions

    def _update_skill_docs(
        self,
        source_name: str,
        source_type: str,
        dimensions: str,
        palette: LearnedPalette,
        advanced_calcs: list[LearnedCalculatedField],
        actions: list[str],
    ) -> bool:
        """Append learned patterns to SKILL.md for persistent agent memory."""
        skill_path = Path(r"C:\Users\User\.agents\skills\tableau-dashboard-designer\SKILL.md")
        if not skill_path.exists():
            return False

        content = skill_path.read_text(encoding="utf-8")
        entry_title = f"### Learned Model: {source_name}"
        if entry_title in content:
            # Already cataloged
            return True

        # Build markdown section
        md_lines = [
            f"\n{entry_title}",
            f"* **Source**: {source_type} | **Canvas**: {dimensions}",
            f"* **Extracted Palette**: Canvas `{palette.canvas_bg}`, Accent `{palette.accent_primary}`, Positive `{palette.positive_color}`, Negative `{palette.negative_color}`",
            "* **Key Learned Calculations**:",
        ]
        for c in advanced_calcs[:4]:
            clean_f = c.formula.replace("\n", " ").strip()
            if len(clean_f) > 85:
                clean_f = clean_f[:82] + "..."
            md_lines.append(f"  * `{c.name}` ({c.category}): `{clean_f}`")

        if actions:
            md_lines.append(f"* **Interactive Actions**: {', '.join(actions[:4])}")

        md_block = "\n".join(md_lines) + "\n"

        # Insert right before "## Quick CLI Reference"
        if "## Quick CLI Reference" in content:
            content = content.replace("## Quick CLI Reference", md_block + "\n## Quick CLI Reference")
        else:
            content += md_block

        skill_path.write_text(content, encoding="utf-8")
        logger.info("Successfully updated %s with learned patterns from %s", skill_path, source_name)
        return True
