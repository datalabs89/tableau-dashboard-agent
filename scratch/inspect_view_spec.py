from lxml import etree
tree = etree.parse(r'C:\Users\User\tableau-document-schemas\schemas\2026_2\twb_2026.2.0.xsd')
root = tree.getroot()
ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}
for g in root.xpath('//xs:group[@name="ViewSpec-ShelfSorts-G"]', namespaces=ns):
    print(etree.tostring(g, pretty_print=True).decode('utf-8'))
