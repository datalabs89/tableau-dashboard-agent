import sys
sys.path.insert(0, '.')
import zipfile
from lxml import etree
from tableau_dashboard_agent.schema_validator import TableauSchemaValidator

twb_path = r"C:\Users\User\Documents\Superstore_Tableau_Visionary_Edition.twb"
tree = etree.parse(twb_path)
root = tree.getroot()

# 1. Reorder zone children
def reorder_zone_children(zone_el):
    for child in zone_el.findall("./zone"):
        reorder_zone_children(child)
    z_order = ["formatted-text", "zone-layout-cache", "zone", "button", "add-in", "zone-style"]
    children = list(zone_el)
    for c in children:
        zone_el.remove(c)
    def get_z_key(el):
        tag = el.tag.split("}")[-1]
        if tag in z_order:
            return z_order.index(tag)
        return 999
    children.sort(key=get_z_key)
    for c in children:
        zone_el.append(c)

for z in root.findall(".//zones/zone"):
    reorder_zone_children(z)

# 2. Fix shelf-sorts location: move from <table> to <table/view>
for ws in root.findall(".//worksheets/worksheet"):
    table = ws.find("table")
    if table is None:
        continue
    ss = table.find("shelf-sorts")
    if ss is not None:
        table.remove(ss)
        view = table.find("view")
        if view is not None:
            agg = view.find("aggregation")
            if agg is not None:
                view.insert(list(view).index(agg), ss)
            else:
                view.append(ss)

v = TableauSchemaValidator()
res = v.validate_xml_root(root)
print("Validation Valid:", res.valid)
if not res.valid:
    print("Errors:")
    for e in res.errors[:15]:
        print(f"  Line {e.line}:{e.column} - {e.message}")
