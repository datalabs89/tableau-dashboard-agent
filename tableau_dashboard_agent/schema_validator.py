"""Schema validator using official Tableau Document Schemas (tableau/tableau-document-schemas).

Validates .twb XML against official XSD files (e.g. twb_2026.1.0.xsd, twb_2026.2.0.xsd).
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from lxml import etree

logger = logging.getLogger(__name__)

# Search paths for official Tableau Document Schemas
_SCHEMA_PATHS = [
    Path(r"C:\Users\User\tableau-document-schemas\schemas"),
    Path(__file__).parent.parent / "vendor" / "tableau-document-schemas" / "schemas",
]

_DEFAULT_SCHEMA_VERSION = "2026.1"

# Stub definitions for external Tableau namespaces required by the XSD
_STUBS: dict[str, bytes] = {
    "_user_ns_stub.xsd": b"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           targetNamespace="http://www.tableausoftware.com/xml/user"
           elementFormDefault="qualified">
  <xs:attributeGroup name="UserAttributes-AG"/>
</xs:schema>""",
    "_xml_ns_stub.xsd": b"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           targetNamespace="http://www.w3.org/XML/1998/namespace">
  <xs:attribute name="lang" type="xs:language"/>
  <xs:attribute name="space">
    <xs:simpleType>
      <xs:restriction base="xs:NCName">
        <xs:enumeration value="default"/>
        <xs:enumeration value="preserve"/>
      </xs:restriction>
    </xs:simpleType>
  </xs:attribute>
  <xs:attribute name="base" type="xs:anyURI"/>
  <xs:attribute name="id" type="xs:ID"/>
</xs:schema>""",
}

_IMPORT_PATCHES: list[tuple[bytes, bytes]] = [
    (
        b'<xs:import namespace="http://www.tableausoftware.com/xml/user"/>',
        b'<xs:import namespace="http://www.tableausoftware.com/xml/user" schemaLocation="_user_ns_stub.xsd"/>',
    ),
    (
        b'<xs:import namespace="http://www.w3.org/XML/1998/namespace"/>',
        b'<xs:import namespace="http://www.w3.org/XML/1998/namespace" schemaLocation="_xml_ns_stub.xsd"/>',
    ),
]


@dataclass
class ValidationIssue:
    line: int
    column: int
    message: str
    is_warning: bool = False


@dataclass
class ValidationResult:
    valid: bool
    schema_version: str
    schema_found: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    def summary(self) -> str:
        status = "VALID" if self.valid else "INVALID"
        lines = [f"Schema Validation Result: {status} (Schema Version: {self.schema_version})"]
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for e in self.errors[:10]:
                lines.append(f"  Line {e.line}:{e.column} - {e.message}")
            if len(self.errors) > 10:
                lines.append(f"  ... and {len(self.errors) - 10} more errors.")
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for w in self.warnings[:5]:
                lines.append(f"  Line {w.line}:{w.column} - {w.message}")
        return "\n".join(lines)


class TableauSchemaValidator:
    """Validates Tableau Workbook XML against official Tableau Document Schemas."""

    def __init__(self, schemas_dir: Optional[str | Path] = None):
        self.schemas_dir = self._resolve_schemas_dir(schemas_dir)
        self._schema_cache: dict[str, etree.XMLSchema] = {}

    @staticmethod
    def _resolve_schemas_dir(preferred: Optional[str | Path]) -> Optional[Path]:
        if preferred:
            p = Path(preferred).resolve()
            if p.exists():
                return p
        for candidate in _SCHEMA_PATHS:
            if candidate.exists():
                return candidate
        return None

    def _locate_xsd_file(self, version_str: str) -> Optional[Path]:
        if not self.schemas_dir or not self.schemas_dir.exists():
            return None

        clean_ver = version_str.replace("'", "").strip()
        # Tableau versions can be 26.1, 2026.1, etc.
        patterns = [
            f"twb_{clean_ver}*.xsd",
            f"twb_20{clean_ver}*.xsd" if len(clean_ver) == 4 and clean_ver.startswith("2") else None,
            "twb_2026.1.0.xsd",
            "twb_2026.2.0.xsd",
        ]

        for pat in [p for p in patterns if p]:
            matches = list(self.schemas_dir.glob(f"**/{pat}"))
            if matches:
                return matches[0]

        # fallback to any twb_*.xsd
        fallbacks = list(self.schemas_dir.glob("**/*.xsd"))
        return fallbacks[0] if fallbacks else None

    def load_schema(self, version_str: str = _DEFAULT_SCHEMA_VERSION) -> Optional[etree.XMLSchema]:
        if version_str in self._schema_cache:
            return self._schema_cache[version_str]

        xsd_path = self._locate_xsd_file(version_str)
        if not xsd_path or not xsd_path.exists():
            logger.warning("No XSD found for version %s in %s", version_str, self.schemas_dir)
            return None

        try:
            # write stub if needed
            for stub_name, stub_bytes in _STUBS.items():
                stub_file = xsd_path.parent / stub_name
                if not stub_file.exists():
                    stub_file.write_bytes(stub_bytes)

            raw = xsd_path.read_bytes()
            for old, new in _IMPORT_PATCHES:
                raw = raw.replace(old, new, 1)

            xsd_doc = etree.parse(io.BytesIO(raw), base_url=xsd_path.as_uri())
            xml_schema = etree.XMLSchema(xsd_doc)
            self._schema_cache[version_str] = xml_schema
            return xml_schema
        except Exception as e:
            logger.error("Failed to compile XSD schema %s: %s", xsd_path, e)
            return None

    def validate_xml_root(self, root: etree._Element) -> ValidationResult:
        """Validate an lxml Element root against the schema."""
        version = root.get("version", _DEFAULT_SCHEMA_VERSION)
        schema = self.load_schema(version)

        if schema is None:
            return ValidationResult(
                valid=True,
                schema_version=version,
                schema_found=False,
                warnings=[ValidationIssue(0, 0, f"Schema definition not found for version {version}. Skipped syntactic validation.", True)],
            )

        is_valid = schema.validate(root)
        errors: list[ValidationIssue] = []
        for err in schema.error_log:
            errors.append(
                ValidationIssue(
                    line=err.line,
                    column=err.column,
                    message=err.message,
                    is_warning=False,
                )
            )

        return ValidationResult(
            valid=is_valid,
            schema_version=version,
            schema_found=True,
            errors=errors,
        )

    def validate_file(self, file_path: str | Path) -> ValidationResult:
        """Validate a .twb file directly from disk."""
        p = Path(file_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")

        try:
            tree = etree.parse(str(p))
            return self.validate_xml_root(tree.getroot())
        except Exception as e:
            return ValidationResult(
                valid=False,
                schema_version="unknown",
                schema_found=False,
                errors=[ValidationIssue(0, 0, f"XML Parsing failed: {e}")],
            )
