"""Dashboard interactivity manager.

Configures interactive Filter Actions, Highlight Actions, and Navigation
within and across Tableau dashboards.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional
from lxml import etree

logger = logging.getLogger(__name__)


class ActionsManager:
    """Manages Tableau interactive actions."""

    @staticmethod
    def add_filter_action(
        root_el: etree._Element,
        dashboard_name: str,
        source_sheet: str,
        target_sheets: list[str],
        action_caption: Optional[str] = None,
        event_type: str = "on-select",  # "on-select", "on-hover", "on-menu"
        clear_behavior: str = "all-fields",  # "all-fields", "leave", "exclude-all"
    ) -> etree._Element:
        """Add a Cross-Filtering action to the workbook."""
        # Find or create <actions> container under <workbook>
        actions_el = root_el.find("actions")
        if actions_el is None:
            # Place actions before <worksheets> or at appropriate schema location
            worksheets_el = root_el.find("worksheets")
            if worksheets_el is not None:
                actions_el = etree.Element("actions")
                root_el.insert(root_el.index(worksheets_el), actions_el)
            else:
                actions_el = etree.SubElement(root_el, "actions")

        action_id = f"[Action_{uuid.uuid4().hex[:8]}]"
        caption = action_caption or f"Filter from {source_sheet}"

        action = etree.SubElement(actions_el, "action")
        action.set("caption", caption)
        action.set("name", action_id)


        activation = etree.SubElement(action, "activation")
        activation.set("auto-clear", "true")
        activation.set("type", event_type)

        source = etree.SubElement(action, "source")
        source.set("dashboard", dashboard_name)
        source.set("type", "sheet")
        source.set("worksheet", source_sheet)

        command = etree.SubElement(action, "command")
        command.set("command", "tsc:tsl-filter")

        param_spec = etree.SubElement(command, "param")
        param_spec.set("name", "special-fields")
        param_spec.set("value", "all")

        # Targets
        for tgt in target_sheets:
            param_tgt = etree.SubElement(command, "param")
            param_tgt.set("name", "target")
            param_tgt.set("value", f"{dashboard_name}/{tgt}")

        return action
