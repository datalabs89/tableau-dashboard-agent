from lxml import etree
tree = etree.parse(r'C:\Users\User\tableau-document-schemas\schemas\2026_2\twb_2026.2.0.xsd')
root = tree.getroot()
ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}
for el in root.xpath('//xs:group[@ref="ViewSpecification-G"]', namespaces=ns):
    p = el.getparent()
    chain = []
    while p is not None:
        chain.append(f"{p.tag} {p.attrib}")
        p = p.getparent()
    print(" -> ".join(chain))
