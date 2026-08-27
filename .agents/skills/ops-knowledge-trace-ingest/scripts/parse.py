#!/usr/bin/env python3
"""
CANNBot APISIX gateway log -> readable trace.

Input:  EITHER a parent dir containing one or more session=ses_*/ subdirs,
        OR a single session=ses_*/ dir passed directly (auto-detected).
        Layout under each session: session=ses_*/YYYY-MM-DD/ls.s3.*.partN.txt
Output: trace_<MAIN>/{trace.json, trace.md, tree.txt, summary.json,
                     attachments/, subagents/<child>/...}

Each *.txt is JSONL where every line is one complete LLM call (one APISIX row).
Within a single session, `messages` is cumulative across calls -> we just need
the LINE WITH THE MOST `messages` to recover the full conversation.

Usage:
    python3 parse.py <input_dir> -o <output_dir> [--max-inline 2048]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ----------------------------------------------------------------------- utils

SESSION_DIR_RE = re.compile(r"^session=(ses_[A-Za-z0-9]+)$")
PART_FILE_RE = re.compile(
    r"^ls\.s3\.[0-9a-f-]+\.(\d{4}-\d{2}-\d{2})T(\d{2})\.(\d{2})\.part(\d+)\.txt$"
)
TOOL_NAMES = {
    "bash", "edit", "glob", "grep", "question", "read",
    "skill", "task", "todowrite", "webfetch", "write",
}


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}B"
        n /= 1024
    return f"{n:.1f}TB"


def safe_json_loads(s: str) -> Any:
    try:
        return json.loads(s)
    except Exception:
        return None


# ----------------------------------------------------------------- SSE reducer

def reduce_sse(body: str) -> dict:
    """Reduce an OpenAI-style SSE response into a single assistant message + meta."""
    content_parts: list[str] = []
    reasoning_parts: list[str] = []
    # tool_calls grouped by index (the order they're emitted in)
    tcs: dict[int, dict] = {}
    finish_reason: str | None = None
    usage: dict | None = None
    model: str | None = None
    chunk_count = 0

    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            continue
        chunk = safe_json_loads(payload)
        if not chunk:
            continue
        chunk_count += 1
        if not model and chunk.get("model"):
            model = chunk["model"]
        if chunk.get("usage"):
            usage = chunk["usage"]
        choices = chunk.get("choices") or []
        for ch in choices:
            if ch.get("finish_reason"):
                finish_reason = ch["finish_reason"]
            delta = ch.get("delta") or {}
            if delta.get("content"):
                content_parts.append(delta["content"])
            if delta.get("reasoning_content"):
                reasoning_parts.append(delta["reasoning_content"])
            for tc in delta.get("tool_calls") or []:
                idx = tc.get("index", 0)
                slot = tcs.setdefault(idx, {"id": None, "type": "function",
                                           "function": {"name": "", "arguments": ""}})
                if tc.get("id"):
                    slot["id"] = tc["id"]
                fn = tc.get("function") or {}
                if fn.get("name"):
                    slot["function"]["name"] = fn["name"]
                if fn.get("arguments"):
                    slot["function"]["arguments"] += fn["arguments"]

    return {
        "content": "".join(content_parts),
        "reasoning": "".join(reasoning_parts),
        "tool_calls": [tcs[k] for k in sorted(tcs)],
        "finish_reason": finish_reason,
        "usage": usage,
        "model": model,
        "chunks": chunk_count,
    }


# -------------------------------------------------------------- file discovery

@dataclass
class SessionFiles:
    session_id: str
    session_dir: Path
    parts: list[Path] = field(default_factory=list)
    children: list["SessionFiles"] = field(default_factory=list)
    parent: "SessionFiles | None" = None

    @property
    def is_main(self) -> bool:
        return self.parent is None


def _part_sort_key(p: Path) -> tuple:
    m = PART_FILE_RE.match(p.name)
    if not m:
        return ("", p.name)
    date, hh, mm, partN = m.groups()
    return (date, int(hh), int(mm), int(partN), p.name)


def discover_sessions(root: Path) -> list[SessionFiles]:
    """Walk the input root; return a list of root SessionFiles (one per top-level session)."""
    sessions: dict[Path, SessionFiles] = {}

    def visit(d: Path, parent: SessionFiles | None) -> SessionFiles | None:
        m = SESSION_DIR_RE.match(d.name)
        if not m:
            return None
        sid = m.group(1)
        sf = SessionFiles(session_id=sid, session_dir=d, parent=parent)
        sessions[d] = sf
        if parent:
            parent.children.append(sf)
        # collect parts from all date subdirs directly under this session
        for child in sorted(d.iterdir()):
            if child.is_dir():
                if SESSION_DIR_RE.match(child.name):
                    visit(child, sf)
                else:
                    # date dir
                    for f in sorted(child.iterdir()):
                        if f.is_file() and PART_FILE_RE.match(f.name):
                            sf.parts.append(f)
        sf.parts.sort(key=_part_sort_key)
        return sf

    # Robustness: accept BOTH a parent dir of many session=ses_* subdirs AND a single
    # session=ses_* dir passed directly. If the input root is itself a session dir,
    # treat it as the one root session (collects its own date-folder logs + nested
    # subagent sessions); otherwise scan children for session=ses_* subdirs.
    root_path = Path(root)
    if SESSION_DIR_RE.match(root_path.name):
        sf = visit(root_path, None)
        return [sf] if sf else []

    roots: list[SessionFiles] = []
    for child in sorted(Path(root).iterdir()):
        if child.is_dir() and SESSION_DIR_RE.match(child.name):
            sf = visit(child, None)
            if sf:
                roots.append(sf)
    return roots


# ----------------------------------------------------- best-line picker (cumul)

def pick_best_line(parts: list[Path]) -> tuple[dict | None, Path | None, int]:
    """
    Scan all .txt parts, return the JSON line with the largest len(messages)
    in request.body. That's the canonical full-conversation snapshot.

    Returns (parsed_outer_obj, file, line_index_1based) or (None, None, 0).
    """
    best: dict | None = None
    best_len = -1
    best_file: Path | None = None
    best_idx = 0
    for fp in parts:
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh, 1):
                    line = line.rstrip("\n")
                    if not line:
                        continue
                    obj = safe_json_loads(line)
                    if not obj:
                        continue
                    rbs = obj.get("request", {}).get("body")
                    if not isinstance(rbs, str):
                        continue
                    rb = safe_json_loads(rbs)
                    if not rb or not isinstance(rb.get("messages"), list):
                        continue
                    n = len(rb["messages"])
                    if n > best_len:
                        best_len = n
                        best = obj
                        best_file = fp
                        best_idx = i
        except OSError as e:
            print(f"  [warn] cannot read {fp}: {e}", file=sys.stderr)
    return best, best_file, best_idx


def collect_per_call_meta(parts: list[Path]) -> list[dict]:
    """
    Walk every line across all parts and extract per-call metadata:
    timestamp, latency, upstream_latency, model, msgs_len, response usage.
    Light-weight; does NOT keep messages/SSE bodies.
    """
    out: list[dict] = []
    for fp in parts:
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    obj = safe_json_loads(line)
                    if not obj:
                        continue
                    rb = safe_json_loads(obj.get("request", {}).get("body") or "{}") or {}
                    body = obj.get("response", {}).get("body") or ""
                    # usage lives in the final SSE chunk where choices==[]; parse just that chunk
                    usage = None
                    for chunk_line in reversed(body.splitlines()):
                        chunk_line = chunk_line.strip()
                        if not chunk_line.startswith("data:"):
                            continue
                        payload = chunk_line[5:].strip()
                        if not payload or payload == "[DONE]":
                            continue
                        c = safe_json_loads(payload)
                        if c and c.get("usage"):
                            usage = c["usage"]
                            break
                    out.append({
                        "ts": obj.get("@timestamp"),
                        "start_time": obj.get("start_time"),
                        "latency": obj.get("latency"),
                        "upstream_latency": obj.get("upstream_latency"),
                        "model": rb.get("model"),
                        "msgs_len": len(rb.get("messages") or []),
                        "usage": usage,
                        "file": fp.name,
                    })
        except OSError:
            pass
    out.sort(key=lambda x: (x.get("ts") or "", x.get("start_time") or 0))
    return out


# ------------------------------------------------------- normalize & emit turns

@dataclass
class Turn:
    idx: int
    role: str                    # system / user / assistant / tool
    content: str = ""            # main visible content
    reasoning: str = ""          # assistant CoT (optional)
    tool_calls: list[dict] = field(default_factory=list)  # for assistant turns
    tool_call_id: str | None = None  # for tool turns
    tool_name: str | None = None     # for tool turns (resolved)
    raw_content_obj: Any = None      # if content was list/dict, keep original


def normalize_messages(messages: list[dict]) -> list[Turn]:
    """Convert OpenAI chat messages into a flat list of Turn objects."""
    # First pass: build assistant tool_call_id -> tool_name map
    tcid_to_name: dict[str, str] = {}
    for m in messages:
        if m.get("role") == "assistant":
            for tc in m.get("tool_calls") or []:
                tcid_to_name[tc.get("id", "")] = (tc.get("function") or {}).get("name", "")

    turns: list[Turn] = []
    for i, m in enumerate(messages):
        role = m.get("role", "")
        c = m.get("content")
        text = ""
        raw_obj = None
        if isinstance(c, str):
            text = c
        elif isinstance(c, list):
            # OpenAI vision-style or part lists -> flatten text parts
            parts = []
            for p in c:
                if isinstance(p, dict) and p.get("type") == "text":
                    parts.append(p.get("text", ""))
                elif isinstance(p, str):
                    parts.append(p)
                else:
                    parts.append(json.dumps(p, ensure_ascii=False))
            text = "\n".join(parts)
            raw_obj = c
        elif c is None:
            text = ""
        else:
            text = json.dumps(c, ensure_ascii=False)
            raw_obj = c

        t = Turn(
            idx=i,
            role=role,
            content=text,
            reasoning=m.get("reasoning_content") or "",
            tool_call_id=m.get("tool_call_id"),
            raw_content_obj=raw_obj,
        )
        if role == "assistant":
            for tc in m.get("tool_calls") or []:
                fn = tc.get("function") or {}
                args_raw = fn.get("arguments", "")
                args_obj = safe_json_loads(args_raw) if isinstance(args_raw, str) else args_raw
                t.tool_calls.append({
                    "id": tc.get("id"),
                    "name": fn.get("name", ""),
                    "arguments_raw": args_raw,
                    "arguments": args_obj,
                })
        if role == "tool":
            t.tool_name = tcid_to_name.get(m.get("tool_call_id", ""))
        turns.append(t)
    return turns


# ----------------------------------------------------------------- attachments

def maybe_offload(text: str, max_inline: int, attach_dir: Path,
                  basename: str, ext: str = "md") -> tuple[str, str | None]:
    """If text > max_inline, write it to attach_dir/basename.ext and return a stub."""
    if len(text) <= max_inline:
        return text, None
    attach_dir.mkdir(parents=True, exist_ok=True)
    fp = attach_dir / f"{basename}.{ext}"
    # avoid clobber
    n = 1
    while fp.exists():
        fp = attach_dir / f"{basename}_{n}.{ext}"
        n += 1
    fp.write_text(text, encoding="utf-8")
    head = text[:300].replace("\n", " ")
    return (
        f"[→ attachments/{fp.name}, {human_size(len(text.encode('utf-8')))}]\n"
        f"> preview: {head}{'…' if len(text) > 300 else ''}",
        fp.name,
    )


# ----------------------------------------------------------------------- emit

def render_turns(turns: list[Turn], attach_dir: Path, max_inline: int) -> tuple[list[dict], str]:
    """Build trace.json structure (list of dicts) and trace.md string."""
    json_turns: list[dict] = []
    md: list[str] = []

    for t in turns:
        # JSON entry: keep full content (we offload at md render time only)
        entry: dict[str, Any] = {
            "idx": t.idx,
            "role": t.role,
        }
        if t.content:
            entry["content"] = t.content
        if t.reasoning:
            entry["reasoning"] = t.reasoning
        if t.tool_calls:
            entry["tool_calls"] = t.tool_calls
        if t.tool_call_id:
            entry["tool_call_id"] = t.tool_call_id
        if t.tool_name:
            entry["tool_name"] = t.tool_name
        json_turns.append(entry)

        # Markdown rendering (with offload)
        head_emoji = {"system": "⚙️", "user": "👤", "assistant": "🤖", "tool": "🛠"}.get(t.role, "•")
        md.append(f"\n## {head_emoji} #{t.idx} `{t.role}`" +
                  (f" ← tool=`{t.tool_name}`" if t.role == "tool" and t.tool_name else ""))

        # Reasoning (collapsed)
        if t.reasoning:
            shown, _ = maybe_offload(t.reasoning, max_inline, attach_dir,
                                     f"{t.idx:03d}_{t.role}_reasoning")
            md.append("<details><summary>💭 reasoning</summary>\n\n" + shown + "\n\n</details>")

        # Tool calls (assistant)
        if t.tool_calls:
            for tc in t.tool_calls:
                args = tc["arguments"] if tc["arguments"] is not None else tc["arguments_raw"]
                args_str = json.dumps(args, ensure_ascii=False, indent=2) if not isinstance(args, str) else args
                shown, _ = maybe_offload(args_str, max_inline, attach_dir,
                                         f"{t.idx:03d}_call_{tc['name']}", ext="json")
                spawn = ""
                if tc["name"] == "task":
                    sub_type = ""
                    if isinstance(tc["arguments"], dict):
                        sub_type = tc["arguments"].get("subagent_type", "")
                    spawn = f" 🌿 SPAWN subagent_type=`{sub_type}`"
                md.append(f"**→ tool_call `{tc['name']}`** id=`{tc['id']}`{spawn}")
                md.append("```json\n" + shown + "\n```")

        # Content
        if t.content:
            shown, _ = maybe_offload(t.content, max_inline, attach_dir,
                                     f"{t.idx:03d}_{t.role}_content")
            md.append(shown)

        if not (t.reasoning or t.tool_calls or t.content):
            md.append("_(empty)_")

    return json_turns, "\n".join(md)


def render_tree(root: SessionFiles, depth: int = 0) -> str:
    pad = "  " * depth
    line = f"{pad}- {root.session_id}  ({len(root.parts)} parts)"
    out = [line]
    for ch in root.children:
        out.append(render_tree(ch, depth + 1))
    return "\n".join(out)


# ----------------------------------------------------------------- per-session

def process_session(sf: SessionFiles, out_dir: Path, max_inline: int,
                    is_root: bool) -> dict:
    """Render trace.json/trace.md/summary.json for one session into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    attach_dir = out_dir / "attachments"

    obj, src_file, line_idx = pick_best_line(sf.parts)
    per_call = collect_per_call_meta(sf.parts)

    if not obj:
        (out_dir / "trace.md").write_text(
            f"# {sf.session_id}\n\n_(no parseable line found in {len(sf.parts)} parts)_\n",
            encoding="utf-8")
        return {"session_id": sf.session_id, "turns": 0, "calls": 0, "error": "no parseable line"}

    rb = safe_json_loads(obj["request"]["body"]) or {}
    messages = rb.get("messages") or []
    sse = reduce_sse(obj.get("response", {}).get("body", ""))

    # The pick_best_line may have selected a line that is itself non-final;
    # but after appending the SSE assistant we still want to show it.
    turns = normalize_messages(messages)
    # Append a synthetic "final assistant" turn for the canonical line's response
    if sse["content"] or sse["tool_calls"] or sse["reasoning"]:
        synth = Turn(
            idx=len(turns),
            role="assistant",
            content=sse["content"],
            reasoning=sse["reasoning"],
            tool_calls=[{
                "id": tc.get("id"),
                "name": (tc.get("function") or {}).get("name", ""),
                "arguments_raw": (tc.get("function") or {}).get("arguments", ""),
                "arguments": safe_json_loads((tc.get("function") or {}).get("arguments", "")),
            } for tc in sse["tool_calls"]],
        )
        turns.append(synth)

    json_turns, md_body = render_turns(turns, attach_dir, max_inline)

    # token totals
    total_prompt = sum((c.get("usage") or {}).get("prompt_tokens", 0) for c in per_call)
    total_completion = sum((c.get("usage") or {}).get("completion_tokens", 0) for c in per_call)
    duration_s = None
    if per_call:
        ts0 = per_call[0].get("ts")
        ts1 = per_call[-1].get("ts")
        duration_s = f"{ts0} → {ts1}"

    summary = {
        "session_id": sf.session_id,
        "is_main": is_root,
        "parts": [str(p.relative_to(sf.session_dir.parent)) for p in sf.parts],
        "calls": len(per_call),
        "turns": len(turns),
        "model": sse.get("model") or rb.get("model"),
        "tokens_prompt": total_prompt,
        "tokens_completion": total_completion,
        "duration": duration_s,
        "tools_available": [t.get("function", {}).get("name") for t in (rb.get("tools") or [])],
        "subagents": [c.session_id for c in sf.children],
        "canonical_line": {
            "file": src_file.name if src_file else None,
            "line_idx_1based": line_idx,
            "msgs_len": len(messages),
        },
    }

    # Write outputs
    (out_dir / "trace.json").write_text(
        json.dumps({"summary": summary, "turns": json_turns}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md_head = [
        f"# Trace `{sf.session_id}`",
        f"- main: **{is_root}**",
        f"- calls (LLM round-trips): **{len(per_call)}**",
        f"- turns (messages including final): **{len(turns)}**",
        f"- model: `{summary['model']}`",
        f"- tokens: prompt={total_prompt:,} / completion={total_completion:,}",
        f"- duration: {duration_s}",
        f"- subagents spawned: {len(sf.children)}" + (
            "  (" + ", ".join(c.session_id for c in sf.children) + ")"
            if sf.children else ""),
        f"- canonical full-history line: `{src_file.name if src_file else '?'}` "
        f"L{line_idx} (msgs={len(messages)})",
        "",
        "---",
    ]
    (out_dir / "trace.md").write_text("\n".join(md_head) + md_body + "\n", encoding="utf-8")

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    return summary


# ----------------------------------------------------------------------- main

def parse_trace_root(input_dir: str | Path, out_dir: str | Path,
                     max_inline: int = 2048) -> list[dict]:
    """Programmatic entry. Returns list of summaries (one per top-level session)."""
    input_dir = Path(input_dir).expanduser().resolve()
    out_dir = Path(out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    roots = discover_sessions(input_dir)
    if not roots:
        print(f"[!] no session=ses_* dirs found under {input_dir}", file=sys.stderr)
        return []

    summaries: list[dict] = []
    for root in roots:
        trace_dir = out_dir / f"trace_{root.session_id}"
        trace_dir.mkdir(parents=True, exist_ok=True)

        # Tree
        (trace_dir / "tree.txt").write_text(render_tree(root) + "\n", encoding="utf-8")

        # Main session
        s = process_session(root, trace_dir, max_inline, is_root=True)
        summaries.append(s)

        # Subagents (recursive — flatten one level for now; nested recursion supported)
        def walk_sub(parent: SessionFiles, parent_dir: Path):
            for ch in parent.children:
                ch_dir = parent_dir / "subagents" / ch.session_id
                process_session(ch, ch_dir, max_inline, is_root=False)
                walk_sub(ch, ch_dir)

        walk_sub(root, trace_dir)

    return summaries


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input_dir", help="parent dir of session=ses_* subdirs, OR a single session=ses_* dir (auto-detected)")
    ap.add_argument("-o", "--output", required=True, help="output trace dir")
    ap.add_argument("--max-inline", type=int, default=2048,
                    help="content larger than this (chars) is offloaded to attachments/")
    args = ap.parse_args(argv)

    summaries = parse_trace_root(args.input_dir, args.output, args.max_inline)
    print(f"\n[ok] wrote {len(summaries)} top-level traces to {args.output}")
    for s in summaries:
        print(f"  - {s['session_id']}: turns={s['turns']} calls={s['calls']} "
              f"subagents={len(s.get('subagents', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
