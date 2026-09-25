"""Unit tests for ReferenceLearner."""

import tempfile
from pathlib import Path
from lxml import etree
import pytest

from tableau_dashboard_agent.reference_learner import ReferenceLearner


def test_reference_learner_local():
    xml_content = b"""<?xml version='1.0' encoding='utf-8' ?>
<workbook source-build="2026.2.0" version="18.1">
  <datasources>
    <datasource caption="Sample Data" name="federated.1">
      <column caption="Total Sales" name="[Sales]" datatype="real" role="measure">
        <calculation formula="SUM([Amount])" />
      </column>
      <column caption="LOD Max" name="[Max Date]" datatype="date" role="dimension">
        <calculation formula="{ MAX([Order Date]) }" />
      </column>
      <column caption="Period Filter" name="[Filter]" datatype="boolean" role="dimension">
        <calculation formula="DATETRUNC('month', [Order Date]) >= #2026-01-01#" />
      </column>
    </datasource>
  </datasources>
  <dashboards>
    <dashboard name="Main Overview">
      <style>
        <style-rule element="table">
          <format attr="background-color" value="#F0F4F8" />
        </style-rule>
      </style>
      <size maxheight="900" maxwidth="1440" minheight="900" minwidth="1440" />
      <zones>
        <zone id="3" type-v2="layout-basic">
          <zone-style>
            <format attr="background-color" value="#FFFFFF" />
            <format attr="border-color" value="#D9E2EC" />
          </zone-style>
          <zone id="5" type-v2="text">
            <formatted-text>
              <run fontcolor="#102A43" fontname="Tableau Bold">Executive Dashboard</run>
            </formatted-text>
          </zone>
        </zone>
      </zones>
    </dashboard>
  </dashboards>
</workbook>"""
    with tempfile.TemporaryDirectory() as td:
        twb_file = Path(td) / "test_ref.twb"
        twb_file.write_bytes(xml_content)

        vault_dir = Path(td) / "vault"
        learner = ReferenceLearner(vault_dir=vault_dir)

        summary = learner.learn(str(twb_file), update_skill_docs=False)

        assert summary.source_name == "test_ref"
        assert summary.dimensions == "1440x900"
        assert summary.palette.canvas_bg == "#F0F4F8"
        assert summary.palette.text_primary == "#102A43"
        assert summary.total_calculations >= 3

        # Check advanced calculations categorization
        categories = {c.category for c in summary.advanced_calculations}
        assert "LOD" in categories
        assert "Period/Date" in categories
