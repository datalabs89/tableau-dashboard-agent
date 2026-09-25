"""Unit tests for BusinessCalculationEngine."""

from cwtwb.twb_editor import TWBEditor
from tableau_dashboard_agent.business_calcs import BusinessCalculationEngine, MetricOption


def test_business_calcs():
    editor = TWBEditor("")
    editor.field_registry.set_unknown_field_policy(allow_unknown_fields=True)

    param_id, calc_name = BusinessCalculationEngine.add_dynamic_metric_switcher(editor)
    assert param_id == "[Parameter 1]"
    assert calc_name == "Dynamic Metric"
    assert "Select Metric" in editor._parameters

    ratio = BusinessCalculationEngine.add_profit_ratio(editor)
    assert ratio == "Profit Ratio"

    lod = BusinessCalculationEngine.add_lod_customer_lifetime_sales(editor)
    assert lod == "Customer Lifetime Sales"
