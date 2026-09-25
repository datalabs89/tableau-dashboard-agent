"""Business calculations and dynamic parameter engine for Tableau dashboards.

Implements Langkah 3:
- Dynamic metric switchers (Parameter + CASE calculations)
- Profitability & Margin ratios
- Customer cohort & Level of Detail (LOD) expressions
- Period-over-period delta measures
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class MetricOption:
    name: str
    field_expression: str
    display_alias: str
    format_string: str = ""


class BusinessCalculationEngine:
    """Manages creation of advanced business calculations and parameter actions."""

    @staticmethod
    def add_dynamic_metric_switcher(
        editor: Any,
        parameter_name: str = "Select Metric",
        metric_options: Optional[list[MetricOption]] = None,
    ) -> tuple[str, str]:
        """Configure a dynamic metric parameter and corresponding calculated measure.
        
        Returns:
            (parameter_internal_name, calculated_field_name)
        """
        options = metric_options or [
            MetricOption(name="Sales", field_expression="[Sales]", display_alias="Revenue ($)", format_string="$#,##0"),
            MetricOption(name="Profit", field_expression="[Profit]", display_alias="Gross Profit ($)", format_string="$#,##0"),
            MetricOption(name="Quantity", field_expression="[Quantity]", display_alias="Units Sold", format_string="#,##0"),
        ]

        allowed_values = [opt.name for opt in options]
        allowed_aliases = {opt.name: opt.display_alias for opt in options}

        # 1. Register parameter
        param_msg = editor.add_parameter(
            name=parameter_name,
            datatype="string",
            default_value=allowed_values[0],
            domain_type="list",
            allowed_values=allowed_values,
            allowed_aliases=allowed_aliases,
        )
        logger.info("Added parameter: %s", param_msg)

        param_internal = editor._parameters[parameter_name]["internal_name"]

        # 2. Build CASE formula: CASE [Parameters].[Parameter 1] WHEN 'Sales' THEN [Sales] ... END
        cases = " ".join([f"WHEN '{opt.name}' THEN {opt.field_expression}" for opt in options])
        formula = f"CASE [Parameters].{param_internal} {cases} ELSE {options[0].field_expression} END"

        calc_name = "Dynamic Metric"
        calc_msg = editor.add_calculated_field(
            field_name=calc_name,
            formula=formula,
            datatype="real",
            role="measure",
        )
        logger.info("Added dynamic calculation: %s", calc_msg)
        return param_internal, calc_name

    @staticmethod
    def add_profit_ratio(editor: Any) -> str:
        """Add standard Profit Margin Ratio: SUM([Profit]) / SUM([Sales])."""
        name = "Profit Ratio"
        editor.add_calculated_field(
            field_name=name,
            formula="SUM([Profit]) / SUM([Sales])",
            datatype="real",
            role="measure",
            default_format="p0.0%",
        )
        return name

    @staticmethod
    def add_lod_customer_lifetime_sales(editor: Any) -> str:
        """Add Level of Detail (LOD) calculation: {FIXED [Customer ID] : SUM([Sales])}."""
        name = "Customer Lifetime Sales"
        editor.add_calculated_field(
            field_name=name,
            formula="{FIXED [Customer ID] : SUM([Sales])}",
            datatype="real",
            role="measure",
            default_format="$#,##0",
        )
        return name

    @staticmethod
    def add_lod_first_purchase_date(editor: Any) -> str:
        """Add Level of Detail (LOD) calculation: {FIXED [Customer ID] : MIN([Order Date])}."""
        name = "Customer Cohort Date"
        editor.add_calculated_field(
            field_name=name,
            formula="{FIXED [Customer ID] : MIN([Order Date])}",
            datatype="date",
            role="dimension",
        )
        return name

    @staticmethod
    def add_yoy_calculations(
        editor: Any,
        metric_field: str = "[Sales]",
        date_field: str = "[Order Date]",
        year_parameter_name: str = "Select Year",
    ) -> dict[str, str]:
        """Add Current Year (CY), Prior Year (PY), and YoY Delta % calculations."""
        cy_name = "CY Measure"
        py_name = "PY Measure"
        yoy_pct_name = "YoY Delta %"
        badge_name = "YoY Delta Badge"

        editor.add_calculated_field(
            field_name=cy_name,
            formula=f"IF YEAR({date_field}) = [Parameters].[{year_parameter_name}] THEN {metric_field} END",
            datatype="real",
            role="measure",
        )
        editor.add_calculated_field(
            field_name=py_name,
            formula=f"IF YEAR({date_field}) = [Parameters].[{year_parameter_name}] - 1 THEN {metric_field} END",
            datatype="real",
            role="measure",
        )
        editor.add_calculated_field(
            field_name=yoy_pct_name,
            formula=f"(ZN(SUM([{cy_name}])) - ZN(SUM([{py_name}]))) / ABS(ZN(SUM([{py_name}])))",
            datatype="real",
            role="measure",
            default_format="p+0.0%;-0.0%",
        )
        editor.add_calculated_field(
            field_name=badge_name,
            formula=f"IF [{yoy_pct_name}] >= 0 THEN '▲ +' + STR(ROUND([{yoy_pct_name}] * 100, 1)) + '%' ELSE '▼ ' + STR(ROUND([{yoy_pct_name}] * 100, 1)) + '%' END",
            datatype="string",
            role="dimension",
        )
        return {
            "cy": cy_name,
            "py": py_name,
            "yoy_pct": yoy_pct_name,
            "badge": badge_name,
        }

    @staticmethod
    def add_dehighlight_field(editor: Any) -> str:
        """Add dummy string field for the Tableau De-Highlight action trick."""
        name = "H"
        editor.add_calculated_field(
            field_name=name,
            formula="'H'",
            datatype="string",
            role="dimension",
        )
        return name

    @staticmethod
    def add_rolling_period_engine(
        editor: Any,
        date_field: str = "[Order Date]",
        parameter_name: str = "Period Selection",
    ) -> dict[str, str]:
        """Configure dynamic rolling period engine anchored to max date with adaptive time grain.
        
        Inspired by Digital Ads Performance Dashboard:
        - Last 7 days, 14 days, 28 days, 30 days, 90 days, This Week, This Year
        - Automatic sparkline time grain (day / week / month)
        - Dynamic 'vs Previous Period' text label
        """
        # 1. Max Date LOD anchor
        max_date_name = "Max Date"
        editor.add_calculated_field(
            field_name=max_date_name,
            formula=f"{{ MAX({date_field}) }}",
            datatype="date",
            role="dimension",
        )

        # 2. Period Selection parameter
        periods = [
            "Last 7 days",
            "Last 14 days",
            "Last 28 days",
            "Last 30 days",
            "Last 90 days",
            "This Week",
            "This Year",
        ]
        editor.add_parameter(
            name=parameter_name,
            datatype="string",
            default_value="Last 7 days",
            domain_type="list",
            allowed_values=periods,
        )

        # 3. Date Filter (Current Period vs Prior Period)
        filter_name = "Period Date Filter"
        filter_formula = f"""CASE [Parameters].[{parameter_name}]
WHEN 'This Week' THEN DATETRUNC('day', {date_field}) >= DATETRUNC('week', [{max_date_name}]) AND DATETRUNC('day', {date_field}) <= [{max_date_name}]
WHEN 'Last 7 days' THEN DATETRUNC('day', {date_field}) >= DATEADD('day', -6, [{max_date_name}]) AND DATETRUNC('day', {date_field}) <= [{max_date_name}]
WHEN 'Last 14 days' THEN DATETRUNC('day', {date_field}) >= DATEADD('day', -13, [{max_date_name}]) AND DATETRUNC('day', {date_field}) <= [{max_date_name}]
WHEN 'Last 28 days' THEN DATETRUNC('day', {date_field}) >= DATEADD('day', -27, [{max_date_name}]) AND DATETRUNC('day', {date_field}) <= [{max_date_name}]
WHEN 'Last 30 days' THEN DATETRUNC('day', {date_field}) >= DATEADD('day', -29, [{max_date_name}]) AND DATETRUNC('day', {date_field}) <= [{max_date_name}]
WHEN 'Last 90 days' THEN DATETRUNC('day', {date_field}) >= DATEADD('day', -89, [{max_date_name}]) AND DATETRUNC('day', {date_field}) <= [{max_date_name}]
WHEN 'This Year' THEN DATETRUNC('day', {date_field}) >= DATETRUNC('year', [{max_date_name}]) AND DATETRUNC('day', {date_field}) <= [{max_date_name}]
END"""
        editor.add_calculated_field(
            field_name=filter_name,
            formula=filter_formula,
            datatype="boolean",
            role="dimension",
        )

        # 4. Adaptive Sparkline Date Grain (Day / Week / Month)
        grain_name = "Dynamic Date Grain"
        grain_formula = f"""CASE [Parameters].[{parameter_name}]
WHEN 'Last 90 days' THEN DATETRUNC('week', {date_field})
WHEN 'This Year' THEN DATETRUNC('month', {date_field})
ELSE DATETRUNC('day', {date_field})
END"""
        editor.add_calculated_field(
            field_name=grain_name,
            formula=grain_formula,
            datatype="date",
            role="dimension",
        )

        # 5. vs Period Label
        vs_label_name = "vs Period Label"
        vs_formula = f"""CASE [Parameters].[{parameter_name}]
WHEN 'This Week' THEN 'vs Last Week'
WHEN 'Last 7 days' THEN 'vs Previous 7 days'
WHEN 'Last 14 days' THEN 'vs Previous 14 days'
WHEN 'Last 28 days' THEN 'vs Previous 28 days'
WHEN 'Last 30 days' THEN 'vs Previous 30 days'
WHEN 'Last 90 days' THEN 'vs Previous 90 days'
WHEN 'This Year' THEN 'vs Last Year'
END"""
        editor.add_calculated_field(
            field_name=vs_label_name,
            formula=vs_formula,
            datatype="string",
            role="dimension",
        )

        return {
            "max_date": max_date_name,
            "parameter": parameter_name,
            "filter": filter_name,
            "date_grain": grain_name,
            "vs_label": vs_label_name,
        }

    @staticmethod
    def add_sla_duration_calculation(
        editor: Any,
        start_date: str = "[Order Date]",
        end_date: str = "[Ship Date]",
        severity_field: Optional[str] = None,
        field_name: str = "Days to Resolve",
    ) -> str:
        """Calculate SLA resolution duration in days with priority/severity weighting.
        Learned from CustomerSupportCaseDemo.
        """
        if severity_field:
            formula = f"""IF {severity_field} != 'Severe' THEN
    ROUND((DATEDIFF('day', {start_date}, {end_date}) * 0.65), 0)
ELSE
    DATEDIFF('day', {start_date}, {end_date}) + 1
END"""
        else:
            formula = f"DATEDIFF('day', {start_date}, {end_date})"

        editor.add_calculated_field(
            field_name=field_name,
            formula=formula,
            datatype="integer",
            role="measure",
        )
        return field_name

    @staticmethod
    def add_nested_reference_lod(
        editor: Any,
        fixed_dimensions: list[str],
        include_dimensions: list[str],
        measure_expr: str,
        field_name: str = "Dynamic Benchmark LOD",
    ) -> str:
        """Create a nested {FIXED ... : MAX({INCLUDE ...})} dynamic benchmark reference line.
        Learned from CustomerSupportCaseDemo.
        """
        fixed_str = ", ".join(fixed_dimensions)
        include_str = ", ".join(include_dimensions)
        formula = f"{{FIXED {fixed_str} : MAX({{INCLUDE {include_str} : {measure_expr}}})}}"
        editor.add_calculated_field(
            field_name=field_name,
            formula=formula,
            datatype="real",
            role="measure",
        )
        return field_name


