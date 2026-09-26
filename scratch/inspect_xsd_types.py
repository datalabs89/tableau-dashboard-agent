from lxml import etree

tree = etree.parse(r'C:\Users\User\tableau-document-schemas\schemas\2026_2\twb_2026.2.0.xsd')
root = tree.getroot()
ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}

for ct in root.findall('.//xs:complexType', ns):
    name = ct.get('name')
    if name in ['tableType', 'zoneType']:
        print(f"=== {name} ===")
        print(etree.tostring(ct, pretty_print=True).decode('utf-8'))
