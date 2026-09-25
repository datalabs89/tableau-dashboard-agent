"""Unit tests for ThemeStyler."""

from pathlib import Path
from lxml import etree
import pytest

from tableau_dashboard_agent.theme_styler import ThemeStyler
from tableau_dashboard_agent.themes import get_theme


def test_theme_styler_xml():
    xml_content = b"""<?xml version='1.0' encoding='utf-8' ?>
<workbook source-build="2026.2.0" version="18.1">
  <worksheets>
    <worksheet name="Sheet1">
      <table><view><datasources/></view></table>
      <style/>
    </worksheet>
  </worksheets>
  <dashboards>
    <dashboard name="DB1">
      <style/>
      <zones>
        <zone id="3" w="100000" h="100000" type-v2="layout-basic">
          <zone id="5" type-v2="text">
            <formatted-text>
              <run fontsize="16">Title</run>
            </formatted-text>
          </zone>
          <zone id="6" name="Sheet1" type-v2="NONE"/>
        </zone>
      </zones>
    </dashboard>
  </dashboards>
  <windows>
    <window class="dashboard" name="DB1">
      <viewpoints/>
      <active id="1"/>
      <simple-id uuid="{00000000-0000-0000-0000-000000000000}"/>
    </window>
  </windows>
</workbook>"""
    root = etree.fromstring(xml_content)
    styler = ThemeStyler("executive-dark")
    styler.apply_to_xml(root)

    # Check dashboard table background format
    db_style = root.find(".//dashboards/dashboard/style")
    assert db_style is not None
    table_rule = db_style.find("./style-rule[@element='table']/format[@attr='background-color']")
    assert table_rule is not None
    assert table_rule.get("value") == "#0B0F19"

    # Check text run fontcolor
    title_run = root.find(".//zone[@id='5']//formatted-text/run")
    assert title_run is not None
    assert title_run.get("fontcolor") == "#F8FAFC"

    # Check sheet background format
    ws_style = root.find(".//worksheets/worksheet/table/style")
    assert ws_style is not None
    ws_bg = ws_style.find("./style-rule[@element='table']/format[@attr='background-color']")
    assert ws_bg is not None
    assert ws_bg.get("value") == "#151D2F"
