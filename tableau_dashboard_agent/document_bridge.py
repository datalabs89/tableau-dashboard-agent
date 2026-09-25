"""Bridge to Tableau Document API (tableau/document-api-python).

Provides inspecting, extracting, and updating connections, datasources,
and fields inside Tableau workbooks (.twb and .twbx).
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

# Add local document-api-python to path if not installed globally
_DOC_API_PATH = Path(r"C:\Users\User\document-api-python")
if _DOC_API_PATH.exists() and str(_DOC_API_PATH) not in sys.path:
    sys.path.insert(0, str(_DOC_API_PATH))

try:
    from tableaudocumentapi import Workbook as DocWorkbook, Datasource, Connection, Field
except ImportError:
    DocWorkbook = None
    Datasource = None
    Connection = None
    Field = None

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    server: Optional[str]
    dbname: Optional[str]
    dbclass: Optional[str]
    port: Optional[str]
    username: Optional[str]
    authentication: Optional[str]


@dataclass
class FieldInfo:
    name: str
    id: str
    datatype: str
    role: str
    is_quantitative: bool
    is_ordinal: bool
    is_nominal: bool
    calculation: Optional[str]
    worksheets_used: list[str] = field(default_factory=list)


@dataclass
class DatasourceInfo:
    name: str
    caption: str
    connections: list[ConnectionInfo] = field(default_factory=list)
    fields_count: int = 0
    fields: list[FieldInfo] = field(default_factory=list)


@dataclass
class WorkbookMetadata:
    file_path: str
    is_packaged: bool
    worksheets: list[str]
    dashboards: list[str]
    datasources: list[DatasourceInfo]


class DocumentBridge:
    """Provides high-level integration with tableau/document-api-python."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path).resolve()
        if not self.file_path.exists():
            raise FileNotFoundError(f"Workbook file not found: {self.file_path}")
        self.is_packaged = self.file_path.suffix.lower() == ".twbx"
        self._doc_wb: Optional[Any] = None

    def _ensure_doc_api(self):
        if DocWorkbook is None:
            raise RuntimeError(
                "tableaudocumentapi is not installed or available. "
                "Ensure tableau/document-api-python is cloned and in PYTHONPATH."
            )

    def load(self) -> DocWorkbook:
        """Load the workbook into Tableau Document API."""
        self._ensure_doc_api()
        self._doc_wb = DocWorkbook(str(self.file_path))
        return self._doc_wb

    def inspect(self) -> WorkbookMetadata:
        """Extract full metadata, datasources, and field mapping from the workbook."""
        wb = self.load()
        ds_infos: list[DatasourceInfo] = []

        for ds in wb.datasources:
            conn_infos = []
            for conn in getattr(ds, "connections", []):
                conn_infos.append(
                    ConnectionInfo(
                        server=getattr(conn, "server", None),
                        dbname=getattr(conn, "dbname", None),
                        dbclass=getattr(conn, "dbclass", None),
                        port=getattr(conn, "port", None),
                        username=getattr(conn, "username", None),
                        authentication=getattr(conn, "authentication", None),
                    )
                )

            field_infos = []
            fields = getattr(ds, "fields", {})
            for fname, fobj in fields.items():
                field_infos.append(
                    FieldInfo(
                        name=getattr(fobj, "name", fname),
                        id=getattr(fobj, "id", fname),
                        datatype=getattr(fobj, "datatype", "string"),
                        role=getattr(fobj, "role", "dimension"),
                        is_quantitative=getattr(fobj, "is_quantitative", False),
                        is_ordinal=getattr(fobj, "is_ordinal", False),
                        is_nominal=getattr(fobj, "is_nominal", True),
                        calculation=getattr(fobj, "calculation", None),
                        worksheets_used=list(getattr(fobj, "worksheets", [])),
                    )
                )

            ds_infos.append(
                DatasourceInfo(
                    name=getattr(ds, "name", "Unnamed"),
                    caption=getattr(ds, "caption", getattr(ds, "name", "")),
                    connections=conn_infos,
                    fields_count=len(field_infos),
                    fields=field_infos,
                )
            )

        return WorkbookMetadata(
            file_path=str(self.file_path),
            is_packaged=self.is_packaged,
            worksheets=list(wb.worksheets),
            dashboards=list(wb.dashboards),
            datasources=ds_infos,
        )

    def update_connection(
        self,
        *,
        datasource_name: Optional[str] = None,
        server: Optional[str] = None,
        dbname: Optional[str] = None,
        username: Optional[str] = None,
        port: Optional[str] = None,
        output_path: Optional[str | Path] = None,
    ) -> Path:
        """Update connection parameters for one or all datasources."""
        wb = self.load()
        modified = False

        for ds in wb.datasources:
            if datasource_name and ds.name != datasource_name and getattr(ds, "caption", "") != datasource_name:
                continue
            for conn in getattr(ds, "connections", []):
                if server is not None:
                    conn.server = server
                    modified = True
                if dbname is not None:
                    conn.dbname = dbname
                    modified = True
                if username is not None:
                    conn.username = username
                    modified = True
                if port is not None:
                    conn.port = port
                    modified = True

        if not modified:
            logger.warning("No connections were matched or modified.")

        target = Path(output_path).resolve() if output_path else self.file_path
        if target == self.file_path:
            wb.save()
        else:
            wb.save_as(str(target))
        return target

    def extract_twb(self, output_dir: Optional[str | Path] = None) -> tuple[Path, Optional[Path]]:
        """If workbook is .twbx, extract its internal .twb and return (twb_path, temp_dir).
        If already .twb, returns (self.file_path, None).
        """
        if not self.is_packaged:
            return self.file_path, None

        out_dir = Path(output_dir or tempfile.mkdtemp(prefix="twbx_unpack_"))
        out_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(self.file_path, "r") as zf:
            zf.extractall(out_dir)

        twb_candidates = list(out_dir.glob("*.twb"))
        if not twb_candidates:
            raise FileNotFoundError(f"No .twb found inside packaged workbook {self.file_path}")
        return twb_candidates[0], out_dir

    @staticmethod
    def repack_twbx(extracted_dir: Path, output_twbx_path: str | Path) -> Path:
        """Repack an extracted directory back into a .twbx archive."""
        out_path = Path(output_twbx_path).resolve()
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(extracted_dir):
                for f in files:
                    full_p = Path(root) / f
                    arcname = full_p.relative_to(extracted_dir)
                    zf.write(full_p, arcname)
        return out_path
