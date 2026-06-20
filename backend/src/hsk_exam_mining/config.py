from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    root_dir: Path
    raw_dir: Path
    output_dir: Path
    output_json_dir: Path
    output_csv_dir: Path
    output_reports_dir: Path
    frontend_public_data_dir: Path


def build_config(root_dir: Path | None = None) -> AppConfig:
    base = (root_dir or Path(__file__).resolve().parents[3]).resolve()
    raw_dir = base / "data" / "raw"
    output_dir = base / "output"
    output_json_dir = output_dir / "json"
    output_csv_dir = output_dir / "csv"
    output_reports_dir = output_dir / "reports"
    frontend_public_data_dir = base / "frontend" / "public" / "data"
    return AppConfig(
        root_dir=base,
        raw_dir=raw_dir,
        output_dir=output_dir,
        output_json_dir=output_json_dir,
        output_csv_dir=output_csv_dir,
        output_reports_dir=output_reports_dir,
        frontend_public_data_dir=frontend_public_data_dir,
    )

