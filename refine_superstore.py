"""Script to refine the Superstore Modern Executive Dashboard with elite Tableau patterns.

Fixes all schema constraints:
- Unique hyphenated simple-id UUIDs for each worksheet and dashboard
- Explicit x, y, w, h attributes on EVERY zone element (required by Tableau Document Schema)
- Correct dashboard child ordering: style -> size -> datasources -> zones -> simple-id
- Correct derivation prefix: 'usr' for User-defined aggregate calcs (SUM(Profit)/SUM(Sales))
- Proper sequence ordering for workbook children: worksheets -> dashboards -> windows -> external
"""

import copy
import uuid
from pathlib import Path
from lxml import etree

from tableau_dashboard_agent.micro_formatter import MicroFormatter
from tableau_dashboard_agent.theme_styler import ThemeStyler
from tableau_dashboard_agent.template_grafter import TemplateGrafter
from tableau_dashboard_agent.visual_linter import VisualLinter
from tableau_dashboard_agent.visual_evaluator import VisualEvaluator


def refine_superstore_workbook():
    twb_path = Path(r"C:\Users\User\Documents\Superstore_Modern_Executive_Dashboard.twb")
    excel_path = Path(r"C:\Users\User\Documents\My Tableau Repository\Datasources\2026.2\en_US-US\Sample - Superstore.xlsx")

    tree = etree.parse(str(twb_path))
    root = tree.getroot()

    # 1. Identify primary datasource
    main_ds = None
    for ds in root.findall(".//datasources/datasource"):
        if ds.get("caption") == "Sample - Superstore" or "Sample - Superstore" in ds.get("name", ""):
            main_ds = ds
            break
    if main_ds is None:
        main_ds = root.findall(".//datasources/datasource")[0]
    ds_name = main_ds.get("name")
    print(f"Primary datasource: {ds_name}")

    # 2. Check or create Profit Ratio in datasource
    profit_ratio_col = None
    dynamic_metric_col = None
    for col in main_ds.findall(".//column"):
        cap = col.get("caption") or col.get("name", "")
        if cap == "Profit Ratio":
            profit_ratio_col = col
        elif cap == "Dynamic Metric":
            dynamic_metric_col = col

    if profit_ratio_col is None:
        pr_id = f"Calculation_{str(uuid.uuid4()).replace('-', '').upper()}"
        profit_ratio_col = etree.SubElement(main_ds, "column")
        profit_ratio_col.set("caption", "Profit Ratio")
        profit_ratio_col.set("datatype", "real")
        profit_ratio_col.set("name", f"[{pr_id}]")
        profit_ratio_col.set("role", "measure")
        profit_ratio_col.set("type", "quantitative")
        profit_ratio_col.set("default-format", "p0.0%")
        calc = etree.SubElement(profit_ratio_col, "calculation")
        calc.set("class", "tableau")
        calc.set("formula", "SUM([Profit]) / SUM([Sales])")
    pr_id = profit_ratio_col.get("name").strip("[]")
    print(f"Profit Ratio column: [{pr_id}]")

    dm_id = dynamic_metric_col.get("name").strip("[]") if dynamic_metric_col is not None else "Calculation_968778082F9A40DBBD9D474F40C11342"
    print(f"Dynamic Metric column: [{dm_id}]")

    # 3. Add Quantity column to datasource if needed
    qty_col = main_ds.find(".//column[@name='[Quantity]']")
    if qty_col is None:
        qty_col = etree.SubElement(main_ds, "column")
        qty_col.set("datatype", "integer")
        qty_col.set("name", "[Quantity]")
        qty_col.set("role", "measure")
        qty_col.set("type", "quantitative")

    # 4. Create KPI_Quantity and KPI_Profit_Ratio worksheets by copying KPI_Sales
    worksheets_el = root.find(".//worksheets")
    kpi_sales_ws = worksheets_el.find(".//worksheet[@name='KPI_Sales']")

    def create_kpi_sheet(sheet_name, col_name, col_derivation, col_type, format_str=""):
        existing = worksheets_el.find(f".//worksheet[@name='{sheet_name}']")
        if existing is not None:
            worksheets_el.remove(existing)

        new_ws = copy.deepcopy(kpi_sales_ws)
        new_ws.set("name", sheet_name)

        # Crucial fix 1: Assign a fresh unique hyphenated UUID to worksheet's simple-id
        sid = new_ws.find("simple-id")
        if sid is not None:
            sid.set("uuid", f"{{{str(uuid.uuid4()).upper()}}}")

        # Crucial fix 2: Tableau derivation prefix for User-defined calc is 'usr', not 'user'
        prefix = "usr" if col_derivation.lower() == "user" else col_derivation.lower()
        ci_name = f"[{prefix}:{col_name}:qk]"

        # Update datasource-dependencies
        dep_el = new_ws.find(f".//datasource-dependencies[@datasource='{ds_name}']")
        if dep_el is not None:
            for ch in list(dep_el):
                dep_el.remove(ch)
            c1 = etree.SubElement(dep_el, "column")
            c1.set("datatype", col_type)
            c1.set("name", f"[{col_name}]")
            c1.set("role", "measure")
            c1.set("type", "quantitative")

            ci = etree.SubElement(dep_el, "column-instance")
            ci.set("column", f"[{col_name}]")
            ci.set("derivation", col_derivation)
            ci.set("name", ci_name)
            ci.set("pivot", "key")
            ci.set("type", "quantitative")

        # Update pane encoding
        text_el = new_ws.find(".//panes/pane/encodings/text")
        if text_el is not None:
            text_el.set("column", f"[{ds_name}].{ci_name}")

        worksheets_el.append(new_ws)
        print(f"Created worksheet: {sheet_name} with derivation prefix [{prefix}]")

    create_kpi_sheet("KPI_Quantity", "Quantity", "Sum", "integer")
    create_kpi_sheet("KPI_Profit_Ratio", pr_id, "User", "real", "p0.0%")

    # Ensure all worksheets have unique hyphenated UUIDs
    for ws in worksheets_el.findall("./worksheet"):
        ws_sid = ws.find("simple-id")
        if ws_sid is not None:
            u = ws_sid.get("uuid", "")
            if "-" not in u:
                ws_sid.set("uuid", f"{{{str(uuid.uuid4()).upper()}}}")

    # 5. Update Category_Breakdown and Segment_Sales to use Dynamic Metric
    cat_ws = worksheets_el.find(".//worksheet[@name='Category_Breakdown']")
    if cat_ws is not None:
        dep = cat_ws.find(f".//datasource-dependencies[@datasource='{ds_name}']")
        if dep is not None:
            if dep.find(f".//column[@name='[{dm_id}]']") is None:
                c = etree.SubElement(dep, "column")
                c.set("caption", "Dynamic Metric")
                c.set("datatype", "real")
                c.set("name", f"[{dm_id}]")
                c.set("role", "measure")
                c.set("type", "quantitative")
                ci = etree.SubElement(dep, "column-instance")
                ci.set("column", f"[{dm_id}]")
                ci.set("derivation", "Sum")
                ci.set("name", f"[sum:{dm_id}:qk]")
                ci.set("pivot", "key")
                ci.set("type", "quantitative")
        cols_el = cat_ws.find("table/cols")
        if cols_el is not None:
            cols_el.text = f"[{ds_name}].[sum:{dm_id}:qk]"
        print("Updated Category_Breakdown to use Dynamic Metric")

    seg_ws = worksheets_el.find(".//worksheet[@name='Segment_Sales']")
    if seg_ws is not None:
        dep = seg_ws.find(f".//datasource-dependencies[@datasource='{ds_name}']")
        if dep is not None:
            if dep.find(f".//column[@name='[{dm_id}]']") is None:
                c = etree.SubElement(dep, "column")
                c.set("caption", "Dynamic Metric")
                c.set("datatype", "real")
                c.set("name", f"[{dm_id}]")
                c.set("role", "measure")
                c.set("type", "quantitative")
                ci = etree.SubElement(dep, "column-instance")
                ci.set("column", f"[{dm_id}]")
                ci.set("derivation", "Sum")
                ci.set("name", f"[sum:{dm_id}:qk]")
                ci.set("pivot", "key")
                ci.set("type", "quantitative")
        rows_el = seg_ws.find("table/rows")
        if rows_el is not None:
            rows_el.text = f"[{ds_name}].[sum:{dm_id}:qk]"
        print("Updated Segment_Sales to use Dynamic Metric")

    # 6. Rebuild Dashboard Zones (Executive Layout)
    db = root.find(".//dashboards/dashboard[@name='Executive_Overview']")
    if db is None:
        raise ValueError("Executive_Overview dashboard not found")

    # Set Canvas Size
    size_el = db.find("size")
    if size_el is None:
        size_el = etree.SubElement(db, "size")
    size_el.set("maxwidth", "1440")
    size_el.set("maxheight", "900")
    size_el.set("minwidth", "1440")
    size_el.set("minheight", "900")
    size_el.set("preset-index", "14")
    size_el.set("sizing-mode", "fixed")

    # Crucial fix 3: Remove simple-id first so it can be re-appended AFTER zones
    # Content model: (layout-options?, style?, size?, datasources, datasource-dependencies*, zones, devicelayouts?, simple-id)
    db_sid = db.find("simple-id")
    if db_sid is not None:
        db.remove(db_sid)

    # Remove existing zones
    old_zones = db.find("zones")
    if old_zones is not None:
        db.remove(old_zones)

    zones_el = etree.SubElement(db, "zones")

    # Root vertical container
    z_root = etree.SubElement(zones_el, "zone")
    z_root.set("id", "3")
    z_root.set("x", "0")
    z_root.set("y", "0")
    z_root.set("w", "100000")
    z_root.set("h", "100000")
    z_root.set("type-v2", "layout-flow")
    z_root.set("param", "vert")

    # 1. Header Container (Height 75 = 8333)
    z_head = etree.SubElement(z_root, "zone")
    z_head.set("id", "4")
    z_head.set("x", "0")
    z_head.set("y", "0")
    z_head.set("w", "100000")
    z_head.set("h", "8333")
    z_head.set("fixed-size", "75")
    z_head.set("is-fixed", "true")
    z_head.set("type-v2", "layout-flow")
    z_head.set("param", "horz")

    # Title text
    z_title = etree.SubElement(z_head, "zone")
    z_title.set("id", "5")
    z_title.set("x", "0")
    z_title.set("y", "0")
    z_title.set("w", "80000")
    z_title.set("h", "8333")
    z_title.set("type-v2", "text")
    z_title.set("forceUpdate", "true")
    ftext = etree.SubElement(z_title, "formatted-text")
    run = etree.SubElement(ftext, "run")
    run.set("bold", "true")
    run.set("fontalignment", "1")
    run.set("fontcolor", "#111e29")
    run.set("fontsize", "16")
    run.text = "SUPERSTORE EXECUTIVE COMMAND CENTER\nInteractive Omnichannel Analytics with Dynamic Metric Toggle"
    zs = etree.SubElement(z_title, "zone-style")
    fmt = etree.SubElement(zs, "format")
    fmt.set("attr", "border-style")
    fmt.set("value", "none")

    # Parameter Control (Select Metric)
    z_param = etree.SubElement(z_head, "zone")
    z_param.set("id", "6")
    z_param.set("x", "80000")
    z_param.set("y", "0")
    z_param.set("w", "20000")
    z_param.set("h", "8333")
    z_param.set("fixed-size", "220")
    z_param.set("is-fixed", "true")
    z_param.set("type-v2", "paramctrl")
    z_param.set("param", "[Parameters].[Parameter 1]")
    zs_p = etree.SubElement(z_param, "zone-style")
    fmt_p = etree.SubElement(zs_p, "format")
    fmt_p.set("attr", "border-style")
    fmt_p.set("value", "none")

    # 2. KPI Ribbon Container (Height 120 = 13333)
    z_kpi_row = etree.SubElement(z_root, "zone")
    z_kpi_row.set("id", "7")
    z_kpi_row.set("x", "0")
    z_kpi_row.set("y", "8333")
    z_kpi_row.set("w", "100000")
    z_kpi_row.set("h", "13333")
    z_kpi_row.set("fixed-size", "120")
    z_kpi_row.set("is-fixed", "true")
    z_kpi_row.set("type-v2", "layout-flow")
    z_kpi_row.set("param", "horz")

    # Crucial fix 4: Every zone MUST have id, x, y, w, h attributes!
    kpi_list = ["KPI_Sales", "KPI_Profit", "KPI_Quantity", "KPI_Profit_Ratio"]
    kpi_zone_id = 8
    kpi_w = 100000 // len(kpi_list)
    for i, k_name in enumerate(kpi_list):
        zk = etree.SubElement(z_kpi_row, "zone")
        zk.set("id", str(kpi_zone_id))
        zk.set("name", k_name)
        zk.set("type-v2", "NONE")
        zk.set("x", str(i * kpi_w))
        zk.set("y", "8333")
        zk.set("w", str(kpi_w))
        zk.set("h", "13333")
        zs_k = etree.SubElement(zk, "zone-style")
        f1 = etree.SubElement(zs_k, "format")
        f1.set("attr", "border-color")
        f1.set("value", "#E2E8F0")
        f2 = etree.SubElement(zs_k, "format")
        f2.set("attr", "border-style")
        f2.set("value", "solid")
        f3 = etree.SubElement(zs_k, "format")
        f3.set("attr", "border-width")
        f3.set("value", "1")
        f4 = etree.SubElement(zs_k, "format")
        f4.set("attr", "padding")
        f4.set("value", "8")
        f5 = etree.SubElement(zs_k, "format")
        f5.set("attr", "background-color")
        f5.set("value", "#FFFFFF")
        kpi_zone_id += 1

    # 3. Middle Analytical Row (Trend & Region)
    z_mid = etree.SubElement(z_root, "zone")
    z_mid.set("id", "15")
    z_mid.set("x", "0")
    z_mid.set("y", "21666")
    z_mid.set("w", "100000")
    z_mid.set("h", "39167")
    z_mid.set("type-v2", "layout-flow")
    z_mid.set("param", "horz")

    mid_list = ["Dynamic_Trend", "Regional_Breakdown"]
    mid_w = 100000 // len(mid_list)
    for i, s_name in enumerate(mid_list):
        zm = etree.SubElement(z_mid, "zone")
        zm.set("id", str(kpi_zone_id))
        zm.set("name", s_name)
        zm.set("type-v2", "NONE")
        zm.set("x", str(i * mid_w))
        zm.set("y", "21666")
        zm.set("w", str(mid_w))
        zm.set("h", "39167")
        zs_m = etree.SubElement(zm, "zone-style")
        f1 = etree.SubElement(zs_m, "format")
        f1.set("attr", "border-color")
        f1.set("value", "#E2E8F0")
        f2 = etree.SubElement(zs_m, "format")
        f2.set("attr", "border-style")
        f2.set("value", "solid")
        f3 = etree.SubElement(zs_m, "format")
        f3.set("attr", "border-width")
        f3.set("value", "1")
        f4 = etree.SubElement(zs_m, "format")
        f4.set("attr", "padding")
        f4.set("value", "8")
        f5 = etree.SubElement(zs_m, "format")
        f5.set("attr", "background-color")
        f5.set("value", "#FFFFFF")
        kpi_zone_id += 1

    # 4. Bottom Analytical Row (Category & Segment)
    z_bot = etree.SubElement(z_root, "zone")
    z_bot.set("id", "20")
    z_bot.set("x", "0")
    z_bot.set("y", "60833")
    z_bot.set("w", "100000")
    z_bot.set("h", "39167")
    z_bot.set("type-v2", "layout-flow")
    z_bot.set("param", "horz")

    bot_list = ["Category_Breakdown", "Segment_Sales"]
    bot_w = 100000 // len(bot_list)
    for i, s_name in enumerate(bot_list):
        zb = etree.SubElement(z_bot, "zone")
        zb.set("id", str(kpi_zone_id))
        zb.set("name", s_name)
        zb.set("type-v2", "NONE")
        zb.set("x", str(i * bot_w))
        zb.set("y", "60833")
        zb.set("w", str(bot_w))
        zb.set("h", "39167")
        zs_b = etree.SubElement(zb, "zone-style")
        f1 = etree.SubElement(zs_b, "format")
        f1.set("attr", "border-color")
        f1.set("value", "#E2E8F0")
        f2 = etree.SubElement(zs_b, "format")
        f2.set("attr", "border-style")
        f2.set("value", "solid")
        f3 = etree.SubElement(zs_b, "format")
        f3.set("attr", "border-width")
        f3.set("value", "1")
        f4 = etree.SubElement(zs_b, "format")
        f4.set("attr", "padding")
        f4.set("value", "8")
        f5 = etree.SubElement(zs_b, "format")
        f5.set("attr", "background-color")
        f5.set("value", "#FFFFFF")
        kpi_zone_id += 1

    # Re-append simple-id to dashboard AFTER zones (with standard hyphenated UUID)
    db_sid = etree.SubElement(db, "simple-id")
    db_sid.set("uuid", f"{{{str(uuid.uuid4()).upper()}}}")

    # 7. Update Actions (Cross-filtering)
    actions_el = root.find(".//actions")
    if actions_el is None:
        actions_el = etree.SubElement(root, "actions")
    for ch in list(actions_el):
        actions_el.remove(ch)

    # Filter action from Region to other charts
    a1 = etree.SubElement(actions_el, "action")
    a1.set("caption", "Cross-Filter by Region")
    a1.set("name", "[Action_Region_Filter]")
    act1 = etree.SubElement(a1, "activation")
    act1.set("auto-clear", "true")
    act1.set("type", "on-select")
    src1 = etree.SubElement(a1, "source")
    src1.set("dashboard", "Executive_Overview")
    src1.set("type", "sheet")
    src1.set("worksheet", "Regional_Breakdown")
    cmd1 = etree.SubElement(a1, "command")
    cmd1.set("command", "tsc:tsl-filter")
    p_t1 = etree.SubElement(cmd1, "param")
    p_t1.set("name", "target")
    p_t1.set("value", "Executive_Overview")
    p_s1 = etree.SubElement(cmd1, "param")
    p_s1.set("name", "special-fields")
    p_s1.set("value", "all")

    # Filter action from Category to other charts
    a2 = etree.SubElement(actions_el, "action")
    a2.set("caption", "Cross-Filter by Category")
    a2.set("name", "[Action_Category_Filter]")
    act2 = etree.SubElement(a2, "activation")
    act2.set("auto-clear", "true")
    act2.set("type", "on-select")
    src2 = etree.SubElement(a2, "source")
    src2.set("dashboard", "Executive_Overview")
    src2.set("type", "sheet")
    src2.set("worksheet", "Category_Breakdown")
    cmd2 = etree.SubElement(a2, "command")
    cmd2.set("command", "tsc:tsl-filter")
    p_t2 = etree.SubElement(cmd2, "param")
    p_t2.set("name", "target")
    p_t2.set("value", "Executive_Overview")
    p_s2 = etree.SubElement(cmd2, "param")
    p_s2.set("name", "special-fields")
    p_s2.set("value", "all")

    # 8. Update Windows (Crucial fix 5: Maintain correct sequence position right after dashboards and before external)
    existing_win = root.find("./windows")
    if existing_win is not None:
        root.remove(existing_win)

    dashboards_el = root.find("./dashboards")
    dashboards_idx = list(root).index(dashboards_el)
    windows_el = etree.Element("windows")
    root.insert(dashboards_idx + 1, windows_el)

    all_sheets = [
        "KPI_Sales", "KPI_Profit", "KPI_Quantity", "KPI_Profit_Ratio",
        "Dynamic_Trend", "Regional_Breakdown", "Category_Breakdown", "Segment_Sales"
    ]

    for s_name in all_sheets:
        w = etree.SubElement(windows_el, "window")
        w.set("class", "worksheet")
        w.set("name", s_name)
        etree.SubElement(w, "cards")
        vp = etree.SubElement(w, "viewpoint")
        zoom = etree.SubElement(vp, "zoom")
        zoom.set("type", "entire-view")
        sid = etree.SubElement(w, "simple-id")
        sid.set("uuid", f"{{{str(uuid.uuid4()).upper()}}}")

    w_db = etree.SubElement(windows_el, "window")
    w_db.set("class", "dashboard")
    w_db.set("name", "Executive_Overview")
    vps = etree.SubElement(w_db, "viewpoints")
    for s_name in all_sheets:
        vp_db = etree.SubElement(vps, "viewpoint")
        vp_db.set("name", s_name)
        z = etree.SubElement(vp_db, "zoom")
        z.set("type", "entire-view")
    act = etree.SubElement(w_db, "active")
    act.set("id", "6")
    sid_db = etree.SubElement(w_db, "simple-id")
    sid_db.set("uuid", f"{{{str(uuid.uuid4()).upper()}}}")

    # 9. Clean chartjunk & ensure no direct styles on worksheets
    for ws in root.findall(".//worksheets/worksheet"):
        for s in ws.findall("./style"):
            ws.remove(s)
        MicroFormatter.clean_chartjunk(ws)

    # 10. Write refined twb
    tree.write(str(twb_path), encoding="utf-8", xml_declaration=True)
    print("Refined base TWB successfully written!")

    # 11. Generate All 4 Theme Editions as TWBX
    packages = [
        ("executive-light", r"C:\Users\User\Documents\Superstore_Modern_Executive_Dashboard.twbx"),
        ("periwinkle-executive", r"C:\Users\User\Documents\Superstore_Periwinkle_Executive.twbx"),
        ("executive-dark", r"C:\Users\User\Documents\Superstore_Executive_Dark.twbx"),
        ("digital-marketing", r"C:\Users\User\Documents\Superstore_Digital_Marketing.twbx"),
    ]

    for theme_name, out_twbx in packages:
        styler = ThemeStyler(theme_name)
        styler.style_workbook_file(twb_path, output_file=out_twbx, data_file_path=excel_path)
        print(f"Generated packaged bundle: {Path(out_twbx).name} ({theme_name})")

    # 12. Run Visual Scorecard on refined dashboard
    sc = VisualEvaluator.evaluate_dashboard(r"C:\Users\User\Documents\Superstore_Modern_Executive_Dashboard.twbx")
    print(sc.summary())


if __name__ == "__main__":
    refine_superstore_workbook()
