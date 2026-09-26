from lxml import etree

tree = etree.parse(r'C:\Users\User\tableau-document-schemas\schemas\2026_2\twb_2026.2.0.xsd')
root = tree.getroot()
ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}

for p in root.xpath('//*[contains(@ref, "shelf-sort") or contains(@name, "shelf-sort")]', namespaces=ns):
    parent = p.getparent()
    print(f"Parent: {parent.tag} {parent.attrib} -> Element: {p.tag} {p.attrib}")
