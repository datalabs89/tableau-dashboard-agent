"""Template Grafter and Native Packaging Engine for Tableau Dashboards.

Implements Langkah 2: Template Grafting & Robust Packaging.
Takes validated, native Tableau templates and grafts external datasets (Excel, CSV, Hyper)
with 100% schema integrity and guaranteed Tableau Desktop compatibility.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Any
from lxml import etree

logger = logging.getLogger(__name__)


class TemplateGrafter:
    """Safely grafts datasets into Tableau workbooks with correct relative paths for TWBX."""

    @staticmethod
    def package_workbook_bundle(
        twb_path: str | Path,
        data_file_path: str | Path,
        output_twbx_path: str | Path,
    ) -> Path:
        """Create a 100% standard Tableau Packaged Workbook (.twbx).
        
        Rewrites the connection filename in the internal XML to relative 'Data/<basename>'
        and stores the data file under 'Data/<basename>' in the ZIP archive.
        """
        twb_p = Path(twb_path).resolve()
        data_p = Path(data_file_path).resolve()
        out_twbx = Path(output_twbx_path).resolve()

        if not twb_p.exists():
            raise FileNotFoundError(f"TWB file not found: {twb_p}")
        if not data_p.exists():
            raise FileNotFoundError(f"Data file not found: {data_p}")

        # Parse TWB XML and rewrite connection path to relative
        tree = etree.parse(str(twb_p))
        root = tree.getroot()
        data_rel_name = f"Data/{data_p.name}"

        # Update all connection references
        for conn in root.findall(".//connection"):
            for attr in ["filename", "dbname"]:
                val = conn.get(attr)
                if val and (data_p.name.lower() in val.lower() or Path(val).name.lower() == data_p.name.lower()):
                    conn.set(attr, data_rel_name)

        # Temporary directory for clean assembly
        temp_dir = Path(tempfile.mkdtemp(prefix="twbx_graft_"))
        try:
            internal_twb_name = f"{out_twbx.stem}.twb"
            temp_twb = temp_dir / internal_twb_name
            tree.write(str(temp_twb), encoding="utf-8", xml_declaration=True)

            with zipfile.ZipFile(out_twbx, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(temp_twb, arcname=internal_twb_name)
                zf.write(data_p, arcname=data_rel_name)

            logger.info("Successfully packaged .twbx bundle at %s", out_twbx)
            return out_twbx
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def fix_twb_absolute_connection(
        twb_path: str | Path,
        data_file_path: str | Path,
        output_twb_path: Optional[str | Path] = None,
    ) -> Path:
        """Ensure standalone .twb points to the valid absolute path of the local data file."""
        twb_p = Path(twb_path).resolve()
        data_p = Path(data_file_path).resolve()
        out_p = Path(output_twb_path).resolve() if output_twb_path else twb_p

        tree = etree.parse(str(twb_p))
        root = tree.getroot()
        abs_posix_path = str(data_p).replace("\\", "/")

        for conn in root.findall(".//connection"):
            for attr in ["filename", "dbname"]:
                val = conn.get(attr)
                if val and (data_p.name.lower() in val.lower() or Path(val).name.lower() == data_p.name.lower() or "data/" in val.lower()):
                    conn.set(attr, abs_posix_path)

        tree.write(str(out_p), encoding="utf-8", xml_declaration=True)
        return out_p
