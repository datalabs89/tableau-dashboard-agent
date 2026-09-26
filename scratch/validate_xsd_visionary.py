import zipfile
import sys
sys.path.insert(0, '.')
from lxml import etree
from tableau_dashboard_agent.schema_validator import TableauSchemaValidator

v = TableauSchemaValidator()

for path in [
    r"C:\Users\User\Documents\Superstore_Tableau_Visionary_Edition.twbx",
    r"C:\Users\User\Documents\Superstore_Ellen_Blackburn_Edition.twbx"
]:
    print(f"\n==========================================")
    print(f"XSD SCHEMA VALIDATION: {path}")
    print(f"==========================================")
    with zipfile.ZipFile(path, 'r') as z:
        for name in z.namelist():
            if name.endswith('.twb'):
                xml = z.read(name)
                root = etree.fromstring(xml)
                res = v.validate_xml_root(root)
                print("Result Valid:", res.valid)
                print("Schema Version:", res.schema_version)
                if not res.valid:
                    print("Errors:")
                    for e in res.errors[:10]:
                        print(f"  Line {e.line}:{e.column} - {e.message}")
