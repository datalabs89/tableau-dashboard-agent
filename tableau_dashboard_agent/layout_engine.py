"""Declarative Tableau Layout Engine.

Constructs structured nested Layout Containers (Horizontal, Vertical, Tiled)
with exact zone dimensions, card styling, padding, and borders.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from lxml import etree

from tableau_dashboard_agent.themes import DashboardTheme, get_theme

logger = logging.getLogger(__name__)


@dataclass
class LayoutNode:
    """Represents a node in the dashboard layout tree."""
    node_type: str  # "container", "worksheet", "text", "filter", "empty", "button"
    direction: Optional[str] = None  # "horizontal", "vertical" (for containers)
    name: Optional[str] = None  # Worksheet name or container identifier
    text_content: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    style: dict[str, Any] = field(default_factory=dict)
    children: list[LayoutNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to cwtwb compatible declarative layout dictionary."""
        d: dict[str, Any] = {
            "type": "container" if self.node_type == "container" else self.node_type
        }
        if self.node_type == "container":
            d["direction"] = self.direction or "vertical"
        if self.name:
            d["name"] = self.name
        if self.text_content:
            d["text"] = self.text_content
        if self.width is not None:
            d["width"] = self.width
        if self.height is not None:
            d["height"] = self.height
        if self.style:
            d["style"] = self.style
        if self.children:
            d["children"] = [c.to_dict() for c in self.children]
        return d


class LayoutBuilder:
    """Builds modern executive dashboard layouts."""

    def __init__(self, theme: Optional[DashboardTheme] = None, width: int = 1440, height: int = 900):
        self.theme = theme or get_theme("executive-light")
        self.width = width
        self.height = height

    def create_executive_layout(
        self,
        *,
        title: str,
        subtitle: str = "Executive Performance Overview",
        kpi_sheets: list[str] = (),
        main_sheets: list[str] = (),
        filter_sheets: list[str] = (),
        detail_sheets: list[str] = (),
    ) -> LayoutNode:
        """Assemble an executive layout:
        [ Header (Title + Subtitle) ]
        [ KPI Cards Strip (Horizontal) ]
        [ Main Analytical Body (1+2 or 2x2 grid) ]
        [ Optional Bottom Detail Row ]
        """
        root = LayoutNode(
            node_type="container",
            direction="vertical",
            style={"background-color": self.theme.canvas_bg, "padding": 8},
        )

        # 1. Header Container
        header_card = LayoutNode(
            node_type="container",
            direction="horizontal",
            height=70,
            style=self.theme.get_zone_style(is_card=True),
            children=[
                LayoutNode(
                    node_type="text",
                    text_content=f"{title}\n{subtitle}",
                    style={"font-family": self.theme.font_family},
                )
            ],
        )
        root.children.append(header_card)

        # 2. KPI Ribbon (if any)
        if kpi_sheets:
            kpi_row = LayoutNode(
                node_type="container",
                direction="horizontal",
                height=130,
                style={"padding": 4},
                children=[
                    LayoutNode(
                        node_type="worksheet",
                        name=sheet,
                        style=self.theme.get_zone_style(is_card=True),
                    )
                    for sheet in kpi_sheets
                ],
            )
            root.children.append(kpi_row)

        # 3. Main Analytical Content Grid
        if main_sheets:
            if len(main_sheets) == 1:
                # Single featured chart
                body_row = LayoutNode(
                    node_type="worksheet",
                    name=main_sheets[0],
                    style=self.theme.get_zone_style(is_card=True),
                )
            elif len(main_sheets) == 2:
                # Side-by-side 50/50 split
                body_row = LayoutNode(
                    node_type="container",
                    direction="horizontal",
                    style={"padding": 4},
                    children=[
                        LayoutNode(
                            node_type="worksheet",
                            name=sheet,
                            style=self.theme.get_zone_style(is_card=True),
                        )
                        for sheet in main_sheets
                    ],
                )
            elif len(main_sheets) == 3:
                # 1 large featured left, 2 stacked right
                left_col = LayoutNode(
                    node_type="worksheet",
                    name=main_sheets[0],
                    style=self.theme.get_zone_style(is_card=True),
                )
                right_col = LayoutNode(
                    node_type="container",
                    direction="vertical",
                    children=[
                        LayoutNode(
                            node_type="worksheet",
                            name=sheet,
                            style=self.theme.get_zone_style(is_card=True),
                        )
                        for sheet in main_sheets[1:]
                    ],
                )
                body_row = LayoutNode(
                    node_type="container",
                    direction="horizontal",
                    style={"padding": 4},
                    children=[left_col, right_col],
                )
            else:
                # 2x2 grid
                top_row = LayoutNode(
                    node_type="container",
                    direction="horizontal",
                    children=[
                        LayoutNode(
                            node_type="worksheet",
                            name=s,
                            style=self.theme.get_zone_style(is_card=True),
                        )
                        for s in main_sheets[:2]
                    ],
                )
                bottom_row = LayoutNode(
                    node_type="container",
                    direction="horizontal",
                    children=[
                        LayoutNode(
                            node_type="worksheet",
                            name=s,
                            style=self.theme.get_zone_style(is_card=True),
                        )
                        for s in main_sheets[2:4]
                    ],
                )
                body_row = LayoutNode(
                    node_type="container",
                    direction="vertical",
                    style={"padding": 4},
                    children=[top_row, bottom_row],
                )
            root.children.append(body_row)

        # 4. Detail Table Row (if any)
        if detail_sheets:
            detail_row = LayoutNode(
                node_type="container",
                direction="horizontal",
                height=220,
                style={"padding": 4},
                children=[
                    LayoutNode(
                        node_type="worksheet",
                        name=sheet,
                        style=self.theme.get_zone_style(is_card=True),
                    )
                    for sheet in detail_sheets
                ],
            )
            root.children.append(detail_row)

        return root

    def create_command_center_layout(
        self,
        *,
        title: str,
        subtitle: str = "Command Center Executive Overview",
        kpi_sheets: list[str] = (),
        main_sheets: list[str] = (),
        filter_sheets: list[str] = (),
    ) -> LayoutNode:
        """Assemble a modern Command Center layout with a Left-Hand Vertical KPI Stack
        and Right Analytical Grid, inspired by top Tableau Public executive designs."""
        root = LayoutNode(
            node_type="container",
            direction="horizontal",
            style={"background-color": self.theme.canvas_bg, "padding": 8},
        )

        # 1. Left Vertical KPI Stack Column (width ~ 320)
        if kpi_sheets:
            left_col = LayoutNode(
                node_type="container",
                direction="vertical",
                width=320,
                style={"padding": 4},
                children=[
                    LayoutNode(
                        node_type="worksheet",
                        name=s,
                        style=self.theme.get_zone_style(is_card=True),
                    )
                    for s in kpi_sheets
                ],
            )
            root.children.append(left_col)

        # 2. Right Analytical Area (Vertical: Header + Charts Grid)
        right_col = LayoutNode(
            node_type="container",
            direction="vertical",
            style={"padding": 4},
        )

        # Header Card
        header_card = LayoutNode(
            node_type="container",
            direction="horizontal",
            height=70,
            style=self.theme.get_zone_style(is_card=True),
            children=[
                LayoutNode(
                    node_type="text",
                    text_content=f"{title}\n{subtitle}",
                    style={"font-family": self.theme.font_family},
                )
            ],
        )
        right_col.children.append(header_card)

        # Grid of main charts
        if main_sheets:
            grid_container = LayoutNode(
                node_type="container",
                direction="vertical",
                style={"padding": 2},
            )
            top_row = LayoutNode(
                node_type="container",
                direction="horizontal",
                children=[
                    LayoutNode(node_type="worksheet", name=s, style=self.theme.get_zone_style(is_card=True))
                    for s in main_sheets[:2]
                ],
            )
            grid_container.children.append(top_row)
            if len(main_sheets) > 2:
                bot_row = LayoutNode(
                    node_type="container",
                    direction="horizontal",
                    children=[
                        LayoutNode(node_type="worksheet", name=s, style=self.theme.get_zone_style(is_card=True))
                        for s in main_sheets[2:4]
                    ],
                )
                grid_container.children.append(bot_row)

            right_col.children.append(grid_container)

        root.children.append(right_col)
        return root

    def inject_layout_into_dashboard(
        self,
        dashboard_el: etree._Element,
        layout_root: LayoutNode,
        next_zone_id: int = 100,
    ) -> int:
        """Directly compile LayoutNode into Tableau <zones> XML tree inside dashboard_el."""
        # Ensure simple-id is placed AFTER zones according to Tableau Document Schema
        sid = dashboard_el.find("simple-id")
        if sid is not None:
            dashboard_el.remove(sid)

        # Clean existing zones
        existing_zones = dashboard_el.find("zones")
        if existing_zones is not None:
            dashboard_el.remove(existing_zones)

        zones_el = etree.SubElement(dashboard_el, "zones")
        current_id = next_zone_id

        def _build_xml_zone(node: LayoutNode, parent_el: etree._Element) -> etree._Element:
            nonlocal current_id
            current_id += 1
            zid = str(current_id)

            zone = etree.SubElement(parent_el, "zone")
            zone.set("id", zid)
            # Tableau Document Schema strictly requires x, y, w, h attributes on every zone
            zone.set("x", "0")
            zone.set("y", "0")
            zone.set("w", str(node.width if node.width is not None else 100000))
            zone.set("h", str(node.height if node.height is not None else 100000))

            if node.node_type == "container":
                if parent_el == zones_el:
                    zone.set("type-v2", "layout-basic")
                else:
                    zone.set("type-v2", "layout-flow")
                    zone.set("param", "horz" if node.direction == "horizontal" else "vert")
            elif node.node_type == "worksheet":
                zone.set("type-v2", "widget")
                zone.set("name", node.name or "")
            elif node.node_type == "text":
                zone.set("type-v2", "text")
                formatted_text = etree.SubElement(zone, "formatted-text")
                run = etree.SubElement(formatted_text, "run")
                run.text = node.text_content or ""
            elif node.node_type == "empty":
                zone.set("type-v2", "empty")

            if node.style:
                self._apply_style(zone, node.style)

            for child in node.children:
                _build_xml_zone(child, zone)

            return zone

        _build_xml_zone(layout_root, zones_el)

        # Re-attach simple-id after zones as required by schema
        if sid is not None:
            dashboard_el.append(sid)

        return current_id

    @staticmethod
    def _apply_style(zone: etree._Element, style: dict[str, Any]):
        zone_style = etree.SubElement(zone, "zone-style")
        for k, v in style.items():
            fmt = etree.SubElement(zone_style, "format")
            fmt.set("attr", k.replace("_", "-"))
            fmt.set("value", str(v))
