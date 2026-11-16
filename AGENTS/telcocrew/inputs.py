"""Inputs for live demos: synthetic datasets (editable files) and scenario packs.

AGENTS/inputs/
  datasets/tables/*.csv          source and gold tables (synthetic)
  datasets/reference/*.yaml      source metadata, glossary, SID map, semantic metrics and lineage
  datasets/operations/*.json     alarms, changes, KEDB, topology, KPIs, pipeline runs, model metrics, cost
  datasets/MANIFEST.yaml         what each file is, its classification and row count
  scenarios/<id>/scenario.yaml   a demo scenario: track, pipeline or agent, request, context, notes
"""
from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path

import yaml

from .registry import ROOT

OPS_FILES = {"alarms": "ALARMS", "changes": "CHANGES", "kedb": "KEDB", "topology": "TOPOLOGY", "kpis": "KPIS",
             "pipeline_runs": "PIPELINE_RUNS", "model_metrics": "MODEL_METRICS", "cost_usage": "COST_USAGE"}
NUM = re.compile(r"^-?\d+(\.\d+)?$")


def inputs_dir() -> Path:
    return Path(os.environ.get("TELCOCREW_INPUTS_DIR") or ROOT / "inputs")


def datasets_dir() -> Path:
    return inputs_dir() / "datasets"


def scenarios_dir() -> Path:
    return inputs_dir() / "scenarios"


# ---------------------------------------------------------------- datasets: write
def write_datasets(n: int = 6000, seed: int = 42) -> dict:
    """(Re)generate every dataset file from the deterministic generator."""
    from . import data
    root = datasets_dir()
    (root / "tables").mkdir(parents=True, exist_ok=True)
    (root / "reference").mkdir(parents=True, exist_ok=True)
    (root / "operations").mkdir(parents=True, exist_ok=True)
    tables = data.generate_tables(n, seed)
    manifest = {"operator": "NorthStar Telecom (fictional)", "synthetic": True, "seed": seed,
                "note": "All values are generated. Personal-looking values (msisdn, full_name, date_of_birth) are fake "
                        "but classified Restricted, so the agents never read them.", "tables": {}, "reference": {}, "operations": {}}
    for name, rows in tables.items():
        with open(root / "tables" / f"{name}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(data.TABLE_COLUMNS[name])
            w.writerows(rows)
        system = next((k for k, v in data.SOURCES.items() if name in v["tables"]), "gold" if name.startswith("gld_") else "other")
        manifest["tables"][name] = {"file": f"tables/{name}.csv", "rows": len(rows), "system": system,
                                    "classification": _table_class(name)}
    src = {k: {**{x: y for x, y in v.items() if x != "tables"},
               "tables": {t: {"ingest": spec["ingest"],
                              "columns": {c: {"type": x[0], "key": x[1], "classification": x[2], "description": x[3]}
                                          for c, x in spec["columns"].items()}} for t, spec in v["tables"].items()}}
           for k, v in data.SOURCES.items()}
    refs = {
        "source_metadata": src,
        "glossary": {k: {"term": v[0], "definition": v[1], "steward": v[2]} for k, v in data.GLOSSARY.items()},
        "sid": {k: {"sid_entity": v[0], "tmf_api": v[1]} for k, v in data.SID.items()},
        "semantic_metrics": {"metrics": data.METRICS, "lineage": data.LINEAGE},
    }
    for name, obj in refs.items():
        (root / "reference" / f"{name}.yaml").write_text(yaml.safe_dump(obj, sort_keys=False, allow_unicode=True, width=120))
        manifest["reference"][name] = f"reference/{name}.yaml"
    for fname, attr in OPS_FILES.items():
        (root / "operations" / f"{fname}.json").write_text(json.dumps(getattr(data, attr), indent=1))
        manifest["operations"][fname] = f"operations/{fname}.json"
    (root / "MANIFEST.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False, width=120))
    return manifest


def _table_class(name: str) -> str:
    from . import data
    for s in data.SOURCES.values():
        if name in s["tables"]:
            classes = {c[2] for c in s["tables"][name]["columns"].values()}
            for level in ("Restricted", "Confidential", "Internal"):
                if level in classes:
                    return f"contains {level}"
    return "Confidential (gold)"


# ---------------------------------------------------------------- datasets: read
def _cell(v: str):
    if NUM.match(v):
        return float(v) if "." in v else int(v)
    return v


def load_datasets() -> dict[str, tuple[list[str], list[tuple]]] | None:
    """Tables from inputs/datasets/tables/*.csv, and reference/operations files applied to the data module.
    Returns None when the folder is missing (the runtime then generates data in memory)."""
    root = datasets_dir()
    tdir = root / "tables"
    if not tdir.exists() or not any(tdir.glob("*.csv")):
        return None
    out = {}
    for p in sorted(tdir.glob("*.csv")):
        with open(p, newline="") as f:
            r = csv.reader(f)
            cols = next(r)
            out[p.stem] = (cols, [tuple(_cell(v) for v in row) for row in r])
    _apply_reference(root)
    return out


def _apply_reference(root: Path) -> None:
    from . import data
    ref = root / "reference"
    if (ref / "source_metadata.yaml").exists():
        src = yaml.safe_load((ref / "source_metadata.yaml").read_text())
        data.SOURCES.clear()
        for k, v in src.items():
            data.SOURCES[k] = {**{x: y for x, y in v.items() if x != "tables"},
                               "tables": {t: {"rows": None, "ingest": spec.get("ingest", ""),
                                              "columns": {c: (x.get("type", ""), x.get("key", ""), x.get("classification", "Restricted"),
                                                              x.get("description", "")) for c, x in spec["columns"].items()}}
                                          for t, spec in v["tables"].items()}}
    if (ref / "glossary.yaml").exists():
        g = yaml.safe_load((ref / "glossary.yaml").read_text())
        data.GLOSSARY.clear()
        data.GLOSSARY.update({k: (v["term"], v["definition"], v.get("steward", "Data Steward")) for k, v in g.items()})
    if (ref / "sid.yaml").exists():
        s = yaml.safe_load((ref / "sid.yaml").read_text())
        data.SID.clear()
        data.SID.update({k: (v["sid_entity"], v["tmf_api"]) for k, v in s.items()})
    if (ref / "semantic_metrics.yaml").exists():
        m = yaml.safe_load((ref / "semantic_metrics.yaml").read_text())
        data.METRICS.clear()
        data.METRICS.update(m.get("metrics", {}))
        data.LINEAGE.clear()
        data.LINEAGE.update(m.get("lineage", {}))
    ops = root / "operations"
    for fname, attr in OPS_FILES.items():
        p = ops / f"{fname}.json"
        if p.exists():
            val = json.loads(p.read_text())
            cur = getattr(data, attr)
            if isinstance(cur, list):
                cur.clear()
                cur.extend(val)
            else:
                cur.clear()
                cur.update(val)


# ---------------------------------------------------------------- scenarios
def list_scenarios() -> list[dict]:
    out = []
    for p in sorted(scenarios_dir().glob("*/scenario.yaml")):
        sc = yaml.safe_load(p.read_text())
        sc["id"] = p.parent.name
        out.append(sc)
    return out


def load_scenario(scenario_id: str) -> dict:
    p = scenarios_dir() / scenario_id / "scenario.yaml"
    if not re.fullmatch(r"[\w-]+", scenario_id) or not p.exists():
        raise KeyError(f"Unknown scenario {scenario_id}. Known: {', '.join(s['id'] for s in list_scenarios())}")
    sc = yaml.safe_load(p.read_text())
    sc["id"] = scenario_id
    base = p.parent
    sc["request"] = (base / sc["request_file"]).read_text().strip() if sc.get("request_file") else sc.get("request", "")
    sc["context"] = "\n\n".join(f"## {f}\n{(base / f).read_text().strip()}" for f in sc.get("context_files", []))
    sc["tasks"] = sc.get("tasks") or ([sc["request"]] if sc.get("kind") == "agent" else [])
    return sc
