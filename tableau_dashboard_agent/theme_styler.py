"""Theme Styler Engine for Tableau Workbooks.

Applies executive design themes (Executive Light, Executive Dark, Minimalist Slate)
across dashboards, zones, text elements, and worksheet styles with complete XML schema safety.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from lxml import etree

from tableau_dashboard_agent.themes import DashboardTheme, get_theme
from tableau_dashboard_agent.document_bridge import DocumentBridge
from tableau_dashboard_agent.template_grafter import TemplateGrafter
from tableau_dashboard_agent.micro_formatter import MicroFormatter

logger = logging.getLogger(__name__)


class ThemeStyler:
    """Applies end-to-end design themes to Tableau workbooks and dashboards."""

    def __init__(self, theme_name: str = "executive-light"):
        self.theme: DashboardTheme = get_theme(theme_name)

    def apply_to_xml(self, root: etree._Element) -> None:
        """Apply theme styling directly to a parsed .twb XML root element."""
        # 1. Apply to all dashboards
        for db in root.findall(".//dashboards/dashboard"):
            self._style_dashboard(db)

        # 2. Apply to all worksheets (backgrounds, headers, text colors)
        for ws in root.findall(".//worksheets/worksheet"):
            self._style_worksheet(ws)

        # 3. Maintain visual hygiene (entire view, no junk gridlines)
        MicroFormatter.apply_entire_view(root)

    def _style_dashboard(self, db: etree._Element) -> None:
        """Apply canvas background and zone styling to a dashboard."""
        # 1. Dashboard canvas background
        style_el = db.find("style")
        if style_el is None:
            style_el = etree.Element("style")
            # Insert before zones or size
            db.insert(0, style_el)

        # Remove existing table background style-rule
        for sr in style_el.findall("./style-rule[@element='table']"):
            style_el.remove(sr)

        # Add canvas background
        rule_table = etree.SubElement(style_el, "style-rule")
        rule_table.set("element", "table")
        fmt = etree.SubElement(rule_table, "format")
        fmt.set("attr", "background-color")
        fmt.set("value", self.theme.canvas_bg)

        # 2. Zones styling
        for zone in db.findall(".//zones//zone"):
            z_type = zone.get("type-v2")
            z_name = zone.get("name")

            # Check if this zone is text / header
            if z_type == "text":
                self._style_text_zone(zone)
            elif z_type == "layout-flow" or z_type == "widget" or (z_name and z_type in ("widget", "NONE", None)):
                self._style_card_zone(zone)

    def _style_text_zone(self, zone: etree._Element) -> None:
        """Format text zone runs with theme text colors."""
        for run in zone.findall(".//formatted-text/run"):
            # If bold or large, it's title
            fs = int(run.get("fontsize", 10))
            if fs >= 14:
                run.set("fontcolor", self.theme.text_primary)
            else:
                run.set("fontcolor", self.theme.text_secondary)
            run.set("fontname", self.theme.font_family.split()[0])

        # Zone style for header container
        zs = zone.find("zone-style")
        if zs is None:
            zs = etree.SubElement(zone, "zone-style")
        self._set_zone_format(zs, "background-color", self.theme.card_bg)
        self._set_zone_format(zs, "border-color", self.theme.card_border)
        self._set_zone_format(zs, "border-style", "solid")
        self._set_zone_format(zs, "border-width", str(self.theme.card_border_width))
        self._set_zone_format(zs, "padding", str(self.theme.card_padding))

    def _style_card_zone(self, zone: etree._Element) -> None:
        """Apply theme background, border, and padding to card zones."""
        # Only style visual containers and worksheet cards, not the root container
        if (zone.get("w") == "100000" and zone.get("h") == "100000" and zone.get("x") == "0" and zone.get("y") == "0") or zone.get("id") in ("1", "3"):
            # Root canvas container - no border, canvas bg
            zs = zone.find("zone-style")
            if zs is None:
                zs = etree.SubElement(zone, "zone-style")
            self._set_zone_format(zs, "background-color", self.theme.canvas_bg)
            self._set_zone_format(zs, "border-style", "none")
            self._set_zone_format(zs, "border-width", "0")
            self._set_zone_format(zs, "padding", "8")
            return

        zs = zone.find("zone-style")
        if zs is None:
            zs = etree.SubElement(zone, "zone-style")

        self._set_zone_format(zs, "background-color", self.theme.card_bg)
        self._set_zone_format(zs, "border-color", self.theme.card_border)
        self._set_zone_format(zs, "border-style", "solid")
        self._set_zone_format(zs, "border-width", str(self.theme.card_border_width))
        self._set_zone_format(zs, "padding", str(self.theme.card_padding))

    @staticmethod
    def _set_zone_format(zone_style_el: etree._Element, attr: str, value: str) -> None:
        """Set or update format attribute in zone-style."""
        fmt = zone_style_el.find(f"./format[@attr='{attr}']")
        if fmt is None:
            fmt = etree.SubElement(zone_style_el, "format")
            fmt.set("attr", attr)
        fmt.set("value", value)

    def _style_worksheet(self, ws: etree._Element) -> None:
        """Apply theme styling to worksheet pane background, font colors, and gridlines."""
        # 0. Clean any invalid direct style children under worksheet
        for s in ws.findall("./style"):
            ws.remove(s)

        table_el = ws.find("table")
        if table_el is None:
            return

        style_el = table_el.find("style")
        if style_el is None:
            # Table content model in Tableau: (view?, style?, panes?, rows?, cols?, ...)
            view_el = table_el.find("view")
            style_el = etree.Element("style")
            if view_el is not None:
                idx = list(table_el).index(view_el)
                table_el.insert(idx + 1, style_el)
            else:
                table_el.insert(0, style_el)

        # 1. Worksheet Table / Pane Background
        rule_table = style_el.find("./style-rule[@element='table']")
        if rule_table is None:
            rule_table = etree.SubElement(style_el, "style-rule")
            rule_table.set("element", "table")
        fmt_bg = rule_table.find("./format[@attr='background-color']")
        if fmt_bg is None:
            fmt_bg = etree.SubElement(rule_table, "format")
            fmt_bg.set("attr", "background-color")
        fmt_bg.set("value", self.theme.card_bg)

        # 2. Worksheet Header & Label Text Colors
        for elem_type in ["label", "header"]:
            rule_lbl = style_el.find(f"./style-rule[@element='{elem_type}']")
            if rule_lbl is None:
                rule_lbl = etree.SubElement(style_el, "style-rule")
                rule_lbl.set("element", elem_type)
            fmt_c = rule_lbl.find("./format[@attr='color']")
            if fmt_c is None:
                fmt_c = etree.SubElement(rule_lbl, "format")
                fmt_c.set("attr", "color")
            fmt_c.set("value", self.theme.text_secondary)

        # 3. Clean gridlines
        MicroFormatter.clean_chartjunk(ws, transparent_bg=False)

    def style_workbook_file(
        self,
        input_file: str | Path,
        output_file: Optional[str | Path] = None,
        data_file_path: Optional[str | Path] = None,
    ) -> Path:
        """Apply theme to a .twb or .twbx file and save."""
        in_p = Path(input_file).resolve()
        if not in_p.exists():
            raise FileNotFoundError(f"Input file not found: {in_p}")

        bridge = DocumentBridge(in_p)
        twb_path, temp_dir = bridge.extract_twb()

        tree = etree.parse(str(twb_path))
        root = tree.getroot()

        # Apply styling
        self.apply_to_xml(root)

        # Determine output path
        if output_file:
            out_p = Path(output_file).resolve()
        else:
            out_p = in_p.parent / f"{in_p.stem}_{self.theme.name.replace(' ', '_')}{in_p.suffix}"

        # Write styled twb
        tree.write(str(twb_path), encoding="utf-8", xml_declaration=True)

        if bridge.is_packaged:
            # Locate data file if needed
            if not data_file_path:
                # Look inside temp_dir/Data
                data_candidates = list((temp_dir / "Data").glob("*.*")) if (temp_dir / "Data").exists() else []
                if data_candidates:
                    data_file_path = data_candidates[0]
                else:
                    data_file_path = r"C:\Users\User\Documents\My Tableau Repository\Datasources\2026.2\en_US-US\Sample - Superstore.xlsx"

            TemplateGrafter.package_workbook_bundle(
                twb_path=twb_path,
                data_file_path=data_file_path,
                output_twbx_path=out_p,
            )
        else:
            if out_p.suffix.lower() == ".twbx":
                if not data_file_path:
                    data_file_path = r"C:\Users\User\Documents\My Tableau Repository\Datasources\2026.2\en_US-US\Sample - Superstore.xlsx"
                TemplateGrafter.package_workbook_bundle(
                    twb_path=twb_path,
                    data_file_path=data_file_path,
                    output_twbx_path=out_p,
                )
            else:
                import shutil
                shutil.copy2(twb_path, out_p)

        if temp_dir and temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

        logger.info("Successfully styled workbook with '%s' -> %s", self.theme.name, out_p)
        return out_p
