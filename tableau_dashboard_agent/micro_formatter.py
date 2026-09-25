"""Micro-Formatting and Visual Hygiene Engine for Tableau Workbooks.

Implements high-fidelity visual styling:
- 'Fit to Entire View' on all dashboard worksheets
- Elimination of chartjunk (gridlines, zero-lines, harsh axis rulers)
- Executive BAN (Big Ass Number) card formatting (multi-tier typography, delta badges)
- Transparent worksheet backgrounds and card container alignment
"""

from __future__ import annotations

import logging
from typing import Optional, Any
from lxml import etree

logger = logging.getLogger(__name__)


class MicroFormatter:
    """Injects micro-formatting and aesthetic rules into Tableau XML."""

    @staticmethod
    def apply_entire_view(root: etree._Element, worksheet_names: Optional[list[str]] = None) -> int:
        """Ensure dashboard viewpoints have zoom type='entire-view'.
        This eliminates scrollbars and forces charts/BANs to fill their container card.
        Safe implementation: strictly updates existing viewpoints in dashboard windows.
        """
        windows_el = root.find("windows")
        if windows_el is None:
            return 0

        count = 0
        for db_win in windows_el.findall("window[@class='dashboard']"):
            viewpoints_el = db_win.find("viewpoints")
            if viewpoints_el is not None:
                for vp in viewpoints_el.findall("viewpoint"):
                    sname = vp.get("name")
                    if worksheet_names is None or sname in worksheet_names:
                        zoom = vp.find("zoom")
                        if zoom is None:
                            zoom = etree.SubElement(vp, "zoom")
                        zoom.set("type", "entire-view")
                        count += 1

        return count

    @staticmethod
    def clean_chartjunk(
        worksheet_el: etree._Element,
        remove_gridlines: bool = True,
        remove_zerolines: bool = True,
        transparent_bg: bool = True,
        hide_axis_rulers: bool = True,
        hide_field_labels: bool = True,
        font_family: str = "Arial",
    ):
        """Clean unnecessary lines, borders, field labels, and default clutter."""
        table_el = worksheet_el.find(".//table")
        if table_el is None:
            return

        style_el = table_el.find("style")
        if style_el is None:
            style_el = etree.SubElement(table_el, "style")
        else:
            # Clean duplicate/existing line & axis rules to keep XML pristine
            for sr in list(style_el.findall("style-rule")):
                el = sr.get("element")
                if el in ("gridline", "zeroline", "dropline", "refline", "table-div", "axis", "worksheet"):
                    style_el.remove(sr)

        if transparent_bg:
            sr_table = style_el.find("./style-rule[@element='table']")
            if sr_table is None:
                sr_table = etree.SubElement(style_el, "style-rule")
                sr_table.set("element", "table")
            fmt = sr_table.find("./format[@attr='background-color']")
            if fmt is None:
                fmt = etree.SubElement(sr_table, "format")
                fmt.set("attr", "background-color")
            fmt.set("value", "#00000000")

        if hide_field_labels:
            sr_ws = etree.SubElement(style_el, "style-rule")
            sr_ws.set("element", "worksheet")
            for scope in ("rows", "cols"):
                fmt = etree.SubElement(sr_ws, "format")
                fmt.set("attr", "display-field-labels")
                fmt.set("scope", scope)
                fmt.set("value", "false")
            fmt_gen = etree.SubElement(sr_ws, "format")
            fmt_gen.set("attr", "display-field-labels")
            fmt_gen.set("value", "false")

        if remove_gridlines:
            sr_grid = etree.SubElement(style_el, "style-rule")
            sr_grid.set("element", "gridline")
            fmt1 = etree.SubElement(sr_grid, "format")
            fmt1.set("attr", "stroke-size")
            fmt1.set("value", "0")
            fmt2 = etree.SubElement(sr_grid, "format")
            fmt2.set("attr", "line-visibility")
            fmt2.set("value", "off")

        if remove_zerolines:
            sr_zero = etree.SubElement(style_el, "style-rule")
            sr_zero.set("element", "zeroline")
            fmt1 = etree.SubElement(sr_zero, "format")
            fmt1.set("attr", "stroke-size")
            fmt1.set("value", "0")
            fmt2 = etree.SubElement(sr_zero, "format")
            fmt2.set("attr", "line-visibility")
            fmt2.set("value", "off")

        # Drop lines, ref lines, table dividers off
        for rule_el in ("dropline", "refline", "table-div"):
            sr_extra = etree.SubElement(style_el, "style-rule")
            sr_extra.set("element", rule_el)
            f1 = etree.SubElement(sr_extra, "format")
            f1.set("attr", "stroke-size")
            f1.set("value", "0")
            f2 = etree.SubElement(sr_extra, "format")
            f2.set("attr", "line-visibility")
            f2.set("value", "off")

        if hide_axis_rulers:
            sr_axis = etree.SubElement(style_el, "style-rule")
            sr_axis.set("element", "axis")
            fmt1 = etree.SubElement(sr_axis, "format")
            fmt1.set("attr", "stroke-size")
            fmt1.set("value", "0")
            fmt2 = etree.SubElement(sr_axis, "format")
            fmt2.set("attr", "line-visibility")
            fmt2.set("value", "off")
            fmt3 = etree.SubElement(sr_axis, "format")
            fmt3.set("attr", "tick-color")
            fmt3.set("value", "#00000000")
            fmt4 = etree.SubElement(sr_axis, "format")
            fmt4.set("attr", "title")
            fmt4.set("value", "")
            fmt5 = etree.SubElement(sr_axis, "format")
            fmt5.set("attr", "font-family")
            fmt5.set("value", font_family)
            fmt6 = etree.SubElement(sr_axis, "format")
            fmt6.set("attr", "color")
            fmt6.set("value", "#737899")
            fmt7 = etree.SubElement(sr_axis, "format")
            fmt7.set("attr", "font-size")
            fmt7.set("value", "9")

        # Header and Pane borders off + Arial typography
        for rule_el in ("header", "pane"):
            sr_hp = style_el.find(f"./style-rule[@element='{rule_el}']")
            if sr_hp is None:
                sr_hp = etree.SubElement(style_el, "style-rule")
                sr_hp.set("element", rule_el)
            f_bw = etree.SubElement(sr_hp, "format")
            f_bw.set("attr", "border-width")
            f_bw.set("value", "0")
            f_bs = etree.SubElement(sr_hp, "format")
            f_bs.set("attr", "border-style")
            f_bs.set("value", "none")
            if rule_el == "pane":
                f_bg = etree.SubElement(sr_hp, "format")
                f_bg.set("attr", "background-color")
                f_bg.set("value", "#00000000")
            if rule_el == "header":
                f_ff = etree.SubElement(sr_hp, "format")
                f_ff.set("attr", "font-family")
                f_ff.set("value", font_family)
                f_fc = etree.SubElement(sr_hp, "format")
                f_fc.set("attr", "color")
                f_fc.set("value", "#404375")
                f_fs = etree.SubElement(sr_hp, "format")
                f_fs.set("attr", "font-size")
                f_fs.set("value", "9")

        # Label & Datalabel styling
        for rule_el in ("label", "datalabel"):
            sr_lbl = style_el.find(f"./style-rule[@element='{rule_el}']")
            if sr_lbl is None:
                sr_lbl = etree.SubElement(style_el, "style-rule")
                sr_lbl.set("element", rule_el)
            f_ff = etree.SubElement(sr_lbl, "format")
            f_ff.set("attr", "font-family")
            f_ff.set("value", font_family)
            f_fc = etree.SubElement(sr_lbl, "format")
            f_fc.set("attr", "color")
            f_fc.set("value", "#3D425A")
            f_fs = etree.SubElement(sr_lbl, "format")
            f_fs.set("attr", "font-size")
            f_fs.set("value", "9")

    @staticmethod
    def format_ban_card(
        worksheet_el: etree._Element,
        label_title: str,
        value_field_tag: str,
        delta_badge: Optional[str] = None,
        is_positive: bool = True,
        value_color: str = "#010948",
        label_color: str = "#737899",
        font_family: str = "Arial",
    ):
        """Format a worksheet into an executive BAN (Big Ass Number) card:
        - Center-aligned text
        - Upper subtitle (8pt bold uppercase Arial)
        - Big metric value (22pt bold Arial)
        - Bottom delta badge (e.g. '▲ +12.4% YoY')
        """
        table_el = worksheet_el.find(".//table")
        if table_el is None:
            return

        style_el = table_el.find("style")
        if style_el is None:
            style_el = etree.SubElement(table_el, "style")

        # Center alignment
        sr_cell = etree.SubElement(style_el, "style-rule")
        sr_cell.set("element", "cell")
        fmt_align = etree.SubElement(sr_cell, "format")
        fmt_align.set("attr", "text-align")
        fmt_align.set("value", "center")
        fmt_valign = etree.SubElement(sr_cell, "format")
        fmt_valign.set("attr", "vertical-align")
        fmt_valign.set("value", "center")

        # Hide worksheet title
        title_el = worksheet_el.find(".//title")
        if title_el is not None:
            title_el.set("formatted-title", "")
            for c in list(title_el):
                title_el.remove(c)

        # Configure custom label in pane
        panes = worksheet_el.findall(".//panes/pane")
        if not panes:
            panes_el = worksheet_el.find(".//panes")
            if panes_el is None:
                panes_el = etree.SubElement(table_el, "panes")
            pane = etree.SubElement(panes_el, "pane")
            panes = [pane]

        for p in panes:
            cl = p.find("customized-label")
            if cl is not None:
                p.remove(cl)
            cl = etree.SubElement(p, "customized-label")
            ft = etree.SubElement(cl, "formatted-text")

            # 1. Title/Label Run
            run_lbl = etree.SubElement(ft, "run")
            run_lbl.set("fontalignment", "1")
            run_lbl.set("fontcolor", label_color)
            run_lbl.set("fontname", font_family)
            run_lbl.set("fontsize", "8")
            run_lbl.set("bold", "true")
            run_lbl.text = f"{label_title.upper()}\n"

            # 2. Main Metric Run
            run_val = etree.SubElement(ft, "run")
            run_val.set("fontalignment", "1")
            run_val.set("fontcolor", value_color)
            run_val.set("fontname", font_family)
            run_val.set("fontsize", "22")
            run_val.set("bold", "true")
            run_val.text = f"{value_field_tag}\n"

            # 3. Delta Badge Run
            if delta_badge:
                run_delta = etree.SubElement(ft, "run")
                run_delta.set("fontalignment", "1")
                badge_color = "#1CAF83" if is_positive else "#E5592E"
                run_delta.set("fontcolor", badge_color)
                run_delta.set("fontname", font_family)
                run_delta.set("fontsize", "9")
                run_delta.set("bold", "true")
                run_delta.text = f"{delta_badge}"

            # Strict schema sequence inside pane: customized-label must precede style!
            MicroFormatter.reorder_pane_children(p)

    @staticmethod
    def reorder_pane_children(pane_el: etree._Element) -> None:
        """Guarantee strict schema ordering inside pane:
        (view, mark, mark-sizing?, encodings?, label-data*, dropline?, trendline?, reference-line*, customized-tooltip?, customized-label?, style?)
        """
        order = [
            "view", "mark", "mark-sizing", "encodings", "label-data",
            "dropline", "trendline", "reference-line",
            "customized-tooltip", "customized-label", "style"
        ]
        elements = list(pane_el)
        for el in elements:
            pane_el.remove(el)

        def get_order_key(el):
            tag = el.tag
            if tag in order:
                return order.index(tag)
            return 999

        elements.sort(key=get_order_key)
        for el in elements:
            pane_el.append(el)
