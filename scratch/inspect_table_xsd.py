from lxml import etree

tree = etree.parse(r'C:\Users\User\tableau-document-schemas\schemas\2026_2\twb_2026.2.0.xsd')
root = tree.getroot()
ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}

for el in root.findall('.//xs:element', ns):
    if el.get('name') == 'table':
        view = el.find('.//xs:element[@name="view"]', ns)
        if view is not None:
            print(etree.tostring(el, pretty_print=True).decode('utf-8'))
