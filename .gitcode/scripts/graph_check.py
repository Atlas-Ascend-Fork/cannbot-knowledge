#!/usr/bin/env python3
"""Run GraphCheck and render its GitCode Actions summary."""

import argparse
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path


BUILDER = ".agents/skills/knowledge-ingest/scripts/knowledge_ingest.py"
GENERATED_GRAPH = "artifacts/graphs/graph.json"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def load_graph(path):
    try:
        graph = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(graph, dict)
            or not isinstance(graph.get("nodes"), list)
            or not isinstance(graph.get("edges"), list)
        ):
            raise ValueError
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    return graph


def failure_reason(output, repo_root):
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    errors = [line for line in lines if line.startswith("error: ")]
    if not errors:
        return "构图失败，未提供具体原因"
    return errors[-1].removeprefix("error: ").replace(f"{repo_root}/", "")


def escape_summary(value):
    return (
        html.escape(str(value))
        .replace("`", "&#96;")
        .replace("[", "&#91;")
        .replace("]", "&#93;")
        .replace("\n", "<br>")
    )


def render_summary(graph, error=""):
    lines = [
        f"## GraphCheck · {'✅ 通过' if graph is not None else '❌ 编译失败'}",
        "",
    ]
    if graph is None:
        lines.append(f"- 失败原因：{escape_summary(error)}")
    else:
        lines.extend(
            [
                f"- 节点：`{len(graph['nodes'])}`",
                f"- 边：`{len(graph['edges'])}`",
            ]
        )
    return "\n".join(lines) + "\n"


def main():
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output = args.output.resolve()
    output.unlink(missing_ok=True)
    generated = repo_root / GENERATED_GRAPH
    generated.unlink(missing_ok=True)
    completed = subprocess.run(
        [
            sys.executable,
            BUILDER,
            "--knowledge-root",
            str(repo_root),
            "build-graph",
        ],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if completed.stdout and completed.returncode != 0:
        print(completed.stdout, end="", file=sys.stderr)
    graph = load_graph(generated) if completed.returncode == 0 else None
    error = ""
    if completed.returncode != 0:
        error = failure_reason(completed.stdout, repo_root)
    elif graph is None:
        error = "构图器未生成有效图数据"
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(generated, output)
    generated.unlink(missing_ok=True)
    print(render_summary(graph, error), end="")
    return 0 if graph is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
