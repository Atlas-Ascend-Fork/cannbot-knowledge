#!/usr/bin/env python3
"""Build and inspect an optional graph derived only from knowledge card links."""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import sys
from pathlib import Path

import yaml


def load_ingest_module():
    module_name = "_cannbot_knowledge_graph_ingest"
    loaded = sys.modules.get(module_name)
    if loaded is not None:
        return loaded
    source = Path(__file__).with_name("knowledge_ingest.py")
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load ingest support module: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


ingest = load_ingest_module()


def render_graph_html(graph: dict[str, object]) -> str:
    rows = []
    for edge in graph["edges"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(edge['source']))}</td>"
            f"<td>{html.escape(str(edge['relation']))}</td>"
            f"<td>{html.escape(str(edge['target']))}</td>"
            "</tr>"
        )
    return """<!doctype html>
<meta charset="utf-8">
<title>CANNBot Knowledge Graph</title>
<style>
body{font:14px system-ui;margin:2rem;color:#1f2937}input{width:100%%;padding:.7rem}
table{border-collapse:collapse;width:100%%;margin-top:1rem}th,td{padding:.45rem;border:1px solid #ddd;text-align:left}
</style>
<h1>CANNBot Knowledge Graph</h1>
<p>nodes=%s edges=%s</p>
<input id="q" placeholder="Filter source, relation, or target">
<table><thead><tr><th>Source</th><th>Relation</th><th>Target</th></tr></thead><tbody>%s</tbody></table>
<script>q.oninput=()=>{for(const r of document.querySelectorAll('tbody tr'))r.hidden=!r.innerText.toLowerCase().includes(q.value.toLowerCase())}</script>
""" % (len(graph["nodes"]), len(graph["edges"]), "".join(rows))


def current_graph(root: Path) -> dict[str, object]:
    path = ingest.graph_artifact_path(root, "artifacts/graphs/graph.json")
    if not path.is_file():
        raise ValueError("graph artifact is missing; run build first")
    actual = json.loads(path.read_text(encoding="utf-8"))
    if actual != ingest.graph_payload(root):
        raise ValueError("graph artifact is stale or invalid; run build again")
    return actual


def viz_command(args: argparse.Namespace) -> int:
    root = ingest.resolve_root(args.knowledge_root)
    graph = current_graph(root)
    output = ingest.graph_artifact_path(root, "artifacts/graphs/graph.html")
    ingest.atomic_write(output, render_graph_html(graph))
    print(f"output={output}")
    return 0


def verify_command(args: argparse.Namespace) -> int:
    root = ingest.resolve_root(args.knowledge_root)
    graph = current_graph(root)
    html_path = ingest.graph_artifact_path(root, "artifacts/graphs/graph.html")
    if html_path.exists() and html_path.read_text(encoding="utf-8") != render_graph_html(graph):
        raise ValueError("graph visualization is stale or invalid; run viz again")
    print(f"verified nodes={len(graph['nodes'])} edges={len(graph['edges'])}")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--knowledge-root")
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("build", help="derive the graph from existing card links").set_defaults(
        handler=ingest.build_graph
    )
    sub.add_parser("viz", help="render a local searchable HTML edge view").set_defaults(
        handler=viz_command
    )
    sub.add_parser("verify", help="check the graph and any existing HTML against card links").set_defaults(
        handler=verify_command
    )
    return result


def main() -> int:
    try:
        args = parser().parse_args()
        return args.handler(args)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
