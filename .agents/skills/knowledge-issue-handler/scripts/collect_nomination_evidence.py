# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Collect verifiable evidence for a Committer / Reviewer nomination issue.

Nomination issues are governance items, not knowledge or bug reports: the reply is
a nomination record built only from facts that can be checked in this repository.
This script gathers those facts and, with ``--draft``, writes a four-段 skeleton
for a human to review.

What it checks, and what it deliberately does not:

* PR state by ``merged_at`` only — open and closed-without-merge are "in flight",
  never "merged".
* Card counts from the actual file list of a merged PR; ``index.md`` is counted
  separately so an index edit cannot inflate the card count.
* Issues authored by the applicant, split into closed and in-flight.
* Local card count of the claimed responsibility path, read from the working
  tree. Existing authorship and migration history are **not** inferred here —
  they need ``git log`` and a human reading.

Read-only: every request is a GET. The script never comments, labels, assigns or
closes anything, and it does not decide whether the nomination should pass.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scan_pr_issue_links import api_get, paginate  # noqa: E402  (same-dir helper)

CONVENTIONAL_PREFIX_RE = re.compile(r"^\s*[a-z]+(?:\([^)]*\))?\s*[:：]\s*", re.IGNORECASE)
# A path must not be preceded by ``/`` or a word character: otherwise the
# "knowledge/pull/218" inside a PR URL is read as a responsibility path.
DOMAIN_PATH_RE = re.compile(r"(?<![\w/-])knowledge/[A-Za-z0-9_\-/]+")
# Second segment of a GitCode web path, never a knowledge domain.
WEB_SEGMENTS = {"pull", "pulls", "issue", "issues", "blob", "tree", "commit", "commits", "raw"}
OTHER_REPOS = ("cannbot-skills", "asc-tools", "asc-devkit")
GOVERNANCE_PREFIXES = ("governance/", ".agents/", "evals/", "docs/", "logs/")


def _request_issue(repo: str, number: int, token: str | None) -> dict[str, Any]:
    issue = api_get(f"/repos/{repo}/issues/{number}", {}, token)
    if not isinstance(issue, dict):
        raise RuntimeError(f"unexpected issue payload for #{number}")
    return issue


def _login_of(node: Any) -> str:
    if isinstance(node, dict):
        return str(node.get("login") or node.get("username") or "")
    return ""


def _clean_title(title: str) -> str:
    return CONVENTIONAL_PREFIX_RE.sub("", title or "").strip()


def detect_domain_path(body: str) -> str:
    """Guess the claimed responsibility path from the issue body.

    Only the first two segments are kept (``knowledge/tools``): nomination bodies
    quote deeper paths per card, and the domain is what a reviewer assigns.
    """
    counts: dict[str, int] = {}
    for match in DOMAIN_PATH_RE.findall(body or ""):
        parts = [part for part in match.strip("/").split("/") if part]
        if len(parts) < 2 or parts[1] in WEB_SEGMENTS:
            continue
        prefix = "/".join(parts[:2])
        counts[prefix] = counts.get(prefix, 0) + 1
    if not counts:
        return ""
    return max(sorted(counts), key=lambda key: counts[key])


def collect_pulls(
    repo: str, login: str, token: str | None, max_pages: int, domain: str
) -> list[dict[str, Any]]:
    pulls = paginate(f"/repos/{repo}/pulls", token, max_pages, params={"state": "all"})
    mine = [item for item in pulls if _login_of(item.get("user")) == login]
    out: list[dict[str, Any]] = []
    for item in sorted(mine, key=lambda value: int(value.get("number") or 0)):
        number = int(item.get("number") or 0)
        merged_at = item.get("merged_at") or ""
        record: dict[str, Any] = {
            "number": number,
            "title": item.get("title") or "",
            "state": item.get("state") or "",
            "merged_at": merged_at[:10],
            "url": item.get("html_url") or "",
            "in_domain": False,
        }
        if merged_at:
            try:
                files = api_get(f"/repos/{repo}/pulls/{number}/files", {}, token) or []
            except Exception:  # noqa: BLE001 - file list is optional detail
                files = []
            names = [str(entry.get("filename") or "") for entry in files if isinstance(entry, dict)]
            # Fall back to the whole knowledge tree when no domain could be
            # inferred, so a nomination without explicit paths still reports
            # real card counts instead of "none found".
            base = domain.rstrip("/") + "/" if domain else "knowledge/"
            cards = [
                name
                for name in names
                if name.startswith(base) and name.endswith(".md") and not name.endswith("/index.md")
            ]
            indexes = [name for name in names if name.startswith(base) and name.endswith("/index.md")]
            record.update(
                {
                    "files": len(names),
                    "additions": sum(int(entry.get("additions") or 0) for entry in files),
                    "deletions": sum(int(entry.get("deletions") or 0) for entry in files),
                    "cards": len(cards),
                    "indexes": len(indexes),
                    "in_domain": bool(cards),
                    # Index-only PRs still carry governance changes (profiles,
                    # paths,门禁), so only card presence disqualifies them.
                    "governance": not cards
                    and any(name.startswith(GOVERNANCE_PREFIXES) for name in names),
                }
            )
        out.append(record)
    return out


def collect_issues(
    repo: str, login: str, token: str | None, max_pages: int
) -> list[dict[str, Any]]:
    # Filter by author locally: the creator filter is not part of the documented
    # v5 contract, and a silently ignored filter would return every issue.
    issues = paginate(f"/repos/{repo}/issues", token, max_pages, params={"state": "all"})
    mine = [item for item in issues if _login_of(item.get("user")) == login]
    return [
        {
            "number": int(item.get("number") or 0),
            "title": item.get("title") or "",
            "state": item.get("state") or "",
            "created_at": (item.get("created_at") or "")[:10],
        }
        for item in sorted(mine, key=lambda value: int(value.get("number") or 0))
    ]


def local_domain_stats(repo_root: Path, domain: str) -> dict[str, Any]:
    if not domain:
        return {}
    target = repo_root / domain
    if not target.exists():
        return {"path": domain, "exists": False, "source": "工作树"}
    cards = [path for path in target.rglob("*.md") if path.name != "index.md"]
    indexes = [path for path in target.rglob("index.md")]
    return {
        "path": domain,
        "exists": True,
        "cards": len(cards),
        "indexes": len(indexes),
        "source": "工作树",
    }


def remote_domain_stats(
    repo: str, domain: str, token: str | None, depth: int = 3
) -> dict[str, Any]:
    """Count cards on the default branch, independent of the local checkout.

    A stale working tree reports zero cards for a domain that already exists on
    master, so master via the contents API is the primary source; the local tree
    is only a fallback.
    """
    if not domain:
        return {}

    def walk(path: str, level: int) -> tuple[int, int]:
        entries = api_get(f"/repos/{repo}/contents/{path}", {"ref": "master"}, token)
        if not isinstance(entries, list):
            return 0, 0
        found_cards = found_indexes = 0
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name") or "")
            kind = str(entry.get("type") or "")
            if kind == "dir" and level < depth:
                more_cards, more_indexes = walk(str(entry.get("path") or f"{path}/{name}"), level + 1)
                found_cards += more_cards
                found_indexes += more_indexes
            elif name.endswith(".md"):
                if name == "index.md":
                    found_indexes += 1
                else:
                    found_cards += 1
        return found_cards, found_indexes

    try:
        cards, indexes = walk(domain, 0)
    except Exception:  # noqa: BLE001 - network or permission failure, fall back below
        return {}
    return {"path": domain, "exists": True, "cards": cards, "indexes": indexes, "source": "master"}


def _bullet_cards(merged: list[dict[str, Any]], pending: list[dict[str, Any]]) -> str:
    if not merged:
        return "- 知识卡：本仓暂未检到已合入的知识卡 PR。"
    detail = "；".join(
        f"!{item['number']}《{_clean_title(item['title'])}》于 {item['merged_at']} 合入，"
        f"{item.get('cards', 0)} 张卡 + {item.get('indexes', 0)} 个索引共 {item.get('files', 0)} 个文件，"
        f"+{item.get('additions', 0)}/−{item.get('deletions', 0)}"
        for item in merged
    )
    if pending:
        detail += "；" + "、".join(f"!{item['number']}" for item in pending) + " 在途"
    return f"- 知识卡：{detail}。"


def _bullet_governance(governance: list[dict[str, Any]]) -> str:
    if not governance:
        return ""
    detail = "；".join(
        f"!{item['number']} {_clean_title(item['title'])}，{item['merged_at']} 合入"
        for item in governance
    )
    return f"- 路径治理：{detail}。"


def _bullet_issues(issues: list[dict[str, Any]]) -> list[str]:
    if not issues:
        return []
    knowledge_markers = ("[Knowledge-Request]", "[Knowledge-Report]", "[Bug-Report]", "知识需求")
    knowledge = [item for item in issues if any(marker in item["title"] for marker in knowledge_markers)]
    other = [item for item in issues if item not in knowledge]
    lines: list[str] = []
    if knowledge:
        closed = [item for item in knowledge if item["state"] == "closed"]
        opening = [item for item in knowledge if item["state"] != "closed"]
        parts = []
        if closed:
            parts.append("、".join(f"#{item['number']}" for item in closed) + " 已关闭")
        if opening:
            parts.append("、".join(f"#{item['number']}" for item in opening) + " 在途")
        lines.append("- 知识 Issue：" + "，".join(parts) + "，均由本账号提起。")
    if other:
        lines.append(
            "- 另有 "
            + "、".join(f"#{item['number']}" for item in other)
            + " 为同类任命申请或其它议题，不重复计入知识贡献。"
        )
    return lines


def build_draft(payload: dict[str, Any]) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    merged = [item for item in payload["pulls"] if item.get("merged_at") and item.get("in_domain")]
    pending = [item for item in payload["pulls"] if not item.get("merged_at") and item.get("in_domain")]
    governance = [
        item
        for item in payload["pulls"]
        if item.get("merged_at") and not item.get("in_domain") and item.get("governance")
    ]
    issues = payload["issues"]
    domain = payload.get("domain") or ""
    lines = [
        "已收到提名申请，本单作为提名记录保留。",
        "",
        f"已核验的贡献（截至 {today}）",
        "",
        _bullet_cards(merged, pending),
    ]
    for bullet in [_bullet_governance(governance)] + _bullet_issues(issues):
        if bullet:
            lines.append(bullet)
    if payload.get("other_repos"):
        lines.append(
            f"- {'、'.join(payload['other_repos'])} 等跨仓贡献为申请人自述，不在本仓范围，本次未逐条核验。"
        )
    lines.append("")
    if domain:
        stats = payload.get("domain_stats") or {}
        count = stats.get("cards")
        where = f"{domain} 现有 {count} 张卡" if isinstance(count, int) else f"{domain} 的存量规模待核"
        lines.append(f"<!-- 待确认：责任田边界（{where}）；存量归属与是否与同域在途申请合并评审，由维护者确认 -->")
    else:
        lines.append("<!-- 待确认：责任田路径与边界；由维护者确认 -->")
    lines.append("")
    lines.append(
        "Committer 任命属治理事项，由本仓有合入权限的维护者决定，同步安排进入 SIG 例会陈述。"
    )
    return "\n".join(lines) + "\n"


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# 角色任命申请取证：#{payload['issue']}" if payload.get("issue") else "# 角色任命申请取证",
        "",
        f"- 申请人：`{payload['login']}`",
        f"- 核查时间：{payload['collected_at']}",
        f"- 责任田路径（按正文推断）：`{payload.get('domain') or '未识别'}`",
        "",
        "## 本仓 PR",
        "",
        "| PR | 状态 | 合入日期 | 文件 | 增/删 | 卡/索引 | 责任田 | 标题 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in payload["pulls"]:
        lines.append(
            f"| !{item['number']} | {item['state']} | {item['merged_at'] or '-'} "
            f"| {item.get('files', '-')} | +{item.get('additions', '-')}/−{item.get('deletions', '-')} "
            f"| {item.get('cards', '-')}/{item.get('indexes', '-')} "
            f"| {'是' if item.get('in_domain') else '否'} | {item['title'][:56]} |"
        )
    if not payload["pulls"]:
        lines.append("| - | - | - | - | - | - | - | 未检到该账号的 PR |")
    lines.extend(["", "## 本仓 Issue", "", "| Issue | 状态 | 创建 | 标题 |", "|---|---|---|---|"])
    for item in payload["issues"]:
        lines.append(
            f"| #{item['number']} | {item['state']} | {item['created_at']} | {item['title'][:56]} |"
        )
    if not payload["issues"]:
        lines.append("| - | - | - | 未检到该账号提起的 Issue |")
    stats = payload.get("domain_stats") or {}
    lines.extend(["", "## 责任田现状", ""])
    if stats.get("exists"):
        lines.append(
            f"`{stats['path']}` 在 {stats.get('source', 'master')} 上现有 "
            f"{stats['cards']} 张卡、{stats['indexes']} 个索引。"
            "存量作者与迁移历史需人工 `git log` 核对，本脚本不推断归属。"
        )
        if stats.get("source") != "master":
            lines.append("")
            lines.append("> 取数来源为本地工作树，可能落后于 master；复核前先 `git fetch`。")
    elif stats:
        lines.append(f"`{stats['path']}` 未检到内容，请确认路径或先同步仓库。")
    else:
        lines.append("未从正文识别出责任田路径。")
    lines.extend(
        [
            "",
            "## 待人工核对",
            "",
            "- 申请人自述与上表的差异（数量、合入状态、责任田范围）；",
            "- 同域在途的其它 Committer 申请，是否需要合并评审；",
            "- 跨仓贡献只能标注为申请人自述，不在本仓核验范围。",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Collect read-only evidence for a Committer/Reviewer nomination issue."
    )
    parser.add_argument("--repo", default="cann/cannbot-knowledge", help="owner/repo")
    parser.add_argument("--issue", type=int, help="nomination issue number; supplies the applicant login")
    parser.add_argument("--login", help="applicant login; required when --issue is omitted")
    parser.add_argument("--path", help="responsibility path override, e.g. knowledge/tools")
    parser.add_argument("--repo-root", default=".", help="local repository root for card counting")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="directory for evidence and draft files; defaults to "
        ".cannbot/gitcode-issue-handler/data/nomination-<issue or login>",
    )
    parser.add_argument("--draft", action="store_true", help="write reply-draft.md next to the evidence")
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--json", action="store_true", help="print the machine-readable summary")
    args = parser.parse_args(argv)

    token = os.environ.get("GITCODE_TOKEN") or None
    login = (args.login or "").strip()
    body = ""
    title = ""
    if args.issue:
        issue = _request_issue(args.repo, args.issue, token)
        login = login or _login_of(issue.get("user"))
        body = str(issue.get("body") or "")
        title = str(issue.get("title") or "")
    if not login:
        parser.error("需要 --login，或用 --issue 从 Issue 作者推断申请人")

    if args.output_dir is None:
        # Per-run directory so two applicants never overwrite each other's evidence.
        args.output_dir = (
            f".cannbot/gitcode-issue-handler/data/nomination-{args.issue}"
            if args.issue
            else f".cannbot/gitcode-issue-handler/data/nomination-{login}"
        )

    domain = (args.path or "").strip().strip("/") or detect_domain_path(body)
    pulls = collect_pulls(args.repo, login, token, args.max_pages, domain)
    issues = [item for item in collect_issues(args.repo, login, token, args.max_pages) if item["number"] != args.issue]
    stats = remote_domain_stats(args.repo, domain, token) or local_domain_stats(Path(args.repo_root), domain)
    payload: dict[str, Any] = {
        "issue": args.issue,
        "issue_title": title,
        "login": login,
        "domain": domain,
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pulls": pulls,
        "issues": issues,
        "domain_stats": stats,
        "other_repos": [name for name in OTHER_REPOS if name in body],
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "nomination-evidence.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "nomination-evidence.md").write_text(_render_markdown(payload), encoding="utf-8")
    if args.draft:
        (out_dir / "reply-draft.md").write_text(build_draft(payload), encoding="utf-8")

    if args.json:
        print(
            json.dumps(
                {
                    "issue": payload["issue"],
                    "login": login,
                    "domain": domain,
                    "pulls": len(pulls),
                    "merged": sum(1 for item in pulls if item.get("merged_at")),
                    "issues": len(issues),
                    "output_dir": str(out_dir),
                    "draft": bool(args.draft),
                },
                ensure_ascii=False,
            )
        )
    else:
        print(f"申请人：{login}")
        print(f"责任田：{domain or '未识别'}")
        print(f"PR：{len(pulls)}（已合入 {sum(1 for item in pulls if item.get('merged_at'))}）")
        print(f"Issue：{len(issues)}")
        print(f"输出：{out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
