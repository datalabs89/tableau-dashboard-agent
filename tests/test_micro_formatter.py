"""Unit tests for MicroFormatter."""

from lxml import etree
from tableau_dashboard_agent.micro_formatter import MicroFormatter


def test_micro_formatter_entire_view():
    xml = """<workbook>
      <worksheets>
        <worksheet name="Sheet1"><table/></worksheet>
      </worksheets>
      <windows>
        <window class="dashboard" name="Dashboard1">
          <viewpoints>
            <viewpoint name="Sheet1"/>
          </viewpoints>
        </window>
      </windows>
    </workbook>"""
    root = etree.fromstring(xml)
    count = MicroFormatter.apply_entire_view(root, ["Sheet1"])
    assert count == 1
    zoom = root.find(".//windows/window[@class='dashboard']/viewpoints/viewpoint[@name='Sheet1']/zoom")
    assert zoom is not None
    assert zoom.get("type") == "entire-view"


def test_micro_formatter_clean_chartjunk():
    xml = """<worksheet name="Sheet1">
      <table>
        <style/>
      </table>
    </worksheet>"""
    ws = etree.fromstring(xml)
    MicroFormatter.clean_chartjunk(ws)
    sr_grid = ws.find(".//style-rule[@element='gridline']")
    assert sr_grid is not None
    assert sr_grid.find("format[@attr='line-visibility']").get("value") == "off"
