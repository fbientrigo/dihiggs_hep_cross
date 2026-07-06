from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class TableSummary:
    path: str
    filename: str
    group: str
    dependent_headers: str
    independent_headers: str
    qualifiers: str
    n_dependent: int
    n_independent: int
    n_values_first_dep: int


def classify_table_name(name: str) -> str:
    low = name.lower()
    if "yield" in low:
        return "yields"
    if "excl_xsec" in low or "xsec" in low:
        return "cross_section_limits"
    if "excl" in low:
        return "exclusion_limits"
    if "acceptance" in low:
        return "acceptance"
    if "event_efficiency" in low:
        return "event_efficiency"
    if "vertex_efficiency" in low:
        return "vertex_efficiency"
    if "cutflow" in low:
        return "cutflow"
    return "other"


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _header_name(obj: Any) -> str:
    if isinstance(obj, dict):
        header = obj.get("header", {})
        if isinstance(header, dict):
            name = header.get("name", "")
            units = header.get("units")
            if units:
                return f"{name} [{units}]"
            return str(name)
    return ""


def _qualifiers(dep: Any) -> str:
    if not isinstance(dep, dict):
        return ""
    quals = dep.get("qualifiers", [])
    parts: list[str] = []
    if isinstance(quals, list):
        for q in quals:
            if isinstance(q, dict):
                name = q.get("name", "")
                value = q.get("value", "")
                units = q.get("units")
                if units:
                    parts.append(f"{name}={value} {units}")
                else:
                    parts.append(f"{name}={value}")
    return "; ".join(parts)


def summarize_table(path: str | Path, root: str | Path | None = None) -> TableSummary:
    p = Path(path)
    data = load_yaml(p)
    deps = data.get("dependent_variables", [])
    indeps = data.get("independent_variables", [])
    if not isinstance(deps, list):
        deps = []
    if not isinstance(indeps, list):
        indeps = []

    dep_headers = [_header_name(d) for d in deps]
    indep_headers = [_header_name(d) for d in indeps]
    qualifiers = [_qualifiers(d) for d in deps[:3]]
    n_values_first = 0
    if deps and isinstance(deps[0], dict) and isinstance(deps[0].get("values"), list):
        n_values_first = len(deps[0]["values"])

    rel = str(p.relative_to(root)) if root is not None else str(p)
    return TableSummary(
        path=rel,
        filename=p.name,
        group=classify_table_name(p.name),
        dependent_headers=" | ".join(h for h in dep_headers if h),
        independent_headers=" | ".join(h for h in indep_headers if h),
        qualifiers=" || ".join(q for q in qualifiers if q),
        n_dependent=len(deps),
        n_independent=len(indeps),
        n_values_first_dep=n_values_first,
    )


_BIN_LABEL_RE = re.compile(r"\[\s*([\d.eE+-]+)\s*,\s*([\d.eE+-]+)\s*\)")


def parse_bin_label(s: str) -> tuple[float, float]:
    """Parse a "[low, high)" bin string (the inverse of _indep_value_str) into (low, high)."""
    m = _BIN_LABEL_RE.match(s.strip())
    if not m:
        raise ValueError(f"not a bin label: {s!r}")
    return float(m.group(1)), float(m.group(2))


def _indep_value_str(entry: Any) -> str:
    """Format one independent-variable row: a point value or a [low, high) bin."""
    if not isinstance(entry, dict):
        return str(entry)
    if "value" in entry:
        return str(entry["value"])
    if "low" in entry or "high" in entry:
        return f"[{entry.get('low', '')}, {entry.get('high', '')})"
    return ""


def tidy_rows(path: str | Path) -> list[dict[str, Any]]:
    """Flatten one HEPData YAML table into tidy rows.

    Each dependent_variables entry is a "series" (its qualifiers pin down mass,
    lifetime, luminosity, etc.). Each value in that series lines up positionally
    with the same-index entry of every independent_variables column (a selection
    label, a bin edge, ...). One tidy row = one (series, position) pair, keeping
    the series qualifiers and all independent-variable columns intact rather than
    flattening them away.
    """
    p = Path(path)
    data = load_yaml(p)
    deps = data.get("dependent_variables", [])
    indeps = data.get("independent_variables", [])
    if not isinstance(deps, list):
        deps = []
    if not isinstance(indeps, list):
        indeps = []
    indep_headers = [_header_name(iv) or f"indep_{i}" for i, iv in enumerate(indeps)]

    rows: list[dict[str, Any]] = []
    for dep in deps:
        if not isinstance(dep, dict):
            continue
        dep_header = _header_name(dep)
        quals = _qualifiers(dep)
        values = dep.get("values", [])
        if not isinstance(values, list):
            continue
        for i, val_entry in enumerate(values):
            row: dict[str, Any] = {
                "source_yaml": p.name,
                "observable": dep_header,
                "qualifiers": quals,
            }
            for h_idx, iv in enumerate(indeps):
                iv_values = iv.get("values", []) if isinstance(iv, dict) else []
                row[indep_headers[h_idx]] = _indep_value_str(iv_values[i]) if i < len(iv_values) else ""
            row["error_label"] = ""
            row["error_symerror"] = ""
            row["error_minus"] = ""
            row["error_plus"] = ""
            if isinstance(val_entry, dict):
                row["value"] = val_entry.get("value")
                errs = val_entry.get("errors", [])
                if isinstance(errs, list) and errs and isinstance(errs[0], dict):
                    e0 = errs[0]
                    row["error_label"] = e0.get("label", "")
                    if "symerror" in e0:
                        row["error_symerror"] = e0.get("symerror")
                    asym = e0.get("asymerror")
                    if isinstance(asym, dict):
                        row["error_minus"] = asym.get("minus")
                        row["error_plus"] = asym.get("plus")
            else:
                row["value"] = val_entry
            rows.append(row)
    return rows


def find_yaml_tables(root: str | Path) -> list[Path]:
    r = Path(root)
    # ponytail: submission.yaml is HEPData's multi-doc manifest, not a table
    paths = list(r.rglob("*.yaml")) + list(r.rglob("*.yml"))
    return sorted(p for p in paths if p.name != "submission.yaml")


def safe_slug(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.=-]+", "_", text.strip())
    return re.sub(r"_+", "_", text).strip("_") or "table"
