from lxml import etree

tree = etree.parse(r'C:\Users\User\tableau-document-schemas\schemas\2026_2\twb_2026.2.0.xsd')
root = tree.getroot()
ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}

for el in root.findall('.//xs:element', ns):
    name = el.get('name')
    if name in ['table', 'zone', 'shelf-sorts']:
        print(f"=== ELEMENT: {name} ===")
        print(etree.tostring(el, pretty_print=True).decode('utf-8')[:1500])
