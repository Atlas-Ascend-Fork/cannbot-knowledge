# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Scan GitCode issues and pull requests and report likely links.

The scan is staged the way a maintainer actually triages, strongest evidence first:

1. **Declared** — the issue says a specific PR fixes it. Judge that PR by its own
   state and stop: merged means the issue can close, open means wait,
   closed-without-merge means the declaration is stale.
2. **Mentioned** — the issue names a PR without claiming it as the fix
   ("built the index on PR #68", "complements PR #100"). Merged PRs here still
   need a human to confirm coverage.
3. **Inferred** — the issue names no PR, so pull requests are matched back by
   closing keywords, ``Issue #N``, ``#N:`` title prefix or ``issue-N`` branch.
4. **Similarity** — nothing explicit on either side; only title overlap remains.
   Never grounds a close recommendation.

Read-only by design: the script only issues GET requests. It never comments,
labels, assigns, closes, or writes anything back to GitCode. All output is
local JSON/Markdown for a human or a separately authorized workflow.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

API_ROOT = "https://api.gitcode.com/api/v5"
USER_AGENT = "cannbot-knowledge-issue-handler/1.0"

ISSUE_URL_RE = re.compile(r"https?://[^\s)>\]]*?/(?:issues|issue)/(\d+)")
# Capture the full repository path so cross-repo PR links can be filtered by
# ownership: "another/repo/pull/251" must never borrow this repo's PR #251.
PR_URL_RE = re.compile(
    r"https?://(?P<host>[^\s)>\]]*?)/(?P<repo>(?:[\w.-]+/){1,2}[\w.-]+)"
    r"(?:/(?:pulls|pull|merge_requests)|/-/merge_requests)/(?P<number>\d+)"
)
CLOSING_RE = re.compile(
    r"(?:fix(?:es|ed)?|close(?:s|d)?|resolve(?:s|d)?|修复|解决|关闭|关联)"
    r"\s*[:：]?\s*(?:#(\d+)|https?://[^\s)>\]]*?/(?:issues|issue)/(\d+))",
    re.IGNORECASE,
)
ISSUE_MENTION_RE = re.compile(r"\bIssue\s*(?:[:：]\s*#?|#)(\d+)", re.IGNORECASE)
PR_MENTION_RE = re.compile(r"\bPR\s*(?:[:：]\s*#?|#)(\d+)", re.IGNORECASE)
BARE_REF_RE = re.compile(r"(?<![\w/#])#(\d+)\b")
BRANCH_ISSUE_RE = re.compile(r"(?:^|[/_-])issue[/_-]?(\d+)(?:$|[/_-])", re.IGNORECASE)
TITLE_PREFIX_RE = re.compile(r"^\s*#(\d+)\s*[:：]")
PR_KEYWORD_RE = re.compile(r"\bPR\b|pull\s*request|merge\s*request|合并请求", re.IGNORECASE)
SEGMENT_SPLIT_RE = re.compile(r"[\n。；;]+")
# "已提交 PR #225" / "已合入 PR #225": the PR is adjacent to the verb, so this is
# about this issue's own resolution rather than an incidental reference.
PR_SOLVE_RE = re.compile(
    r"(?:已提交|已提|已由|已通过|已合入|已并入)\s*(?:PR|pull\s*request)\s*[:：]?\s*#(\d+)",
    re.IGNORECASE,
)
# A declaration needs both a self-reference and a fix verb in the same sentence.
SELF_REF_RE = re.compile(
    r"本\s*(?:Issue|问题|缺陷|需求|提案)|该\s*(?:Issue|问题|缺陷|需求)|此\s*(?:Issue|问题)|上述问题|楼主",
    re.IGNORECASE,
)
FIX_VERB_RE = re.compile(r"已提交|已提|已合入|已并入|已由|已通过|已修复|修复|解决|闭环|覆盖", re.IGNORECASE)
# "关联 PR:" / "对应 PR:" is a template field, i.e. an explicit pointer, not prose.
LABELED_PR_RE = re.compile(
    r"(?:关联|对应|修复|相关|交付|实现)\s*(?:PR|pull\s*request)\s*[:：]", re.IGNORECASE
)
# Negation in front of a fix verb or a self-reference: "本 Issue 尚未修复",
# "该问题仍未解决". Without this guard, "尚未修复" is read as "修复" and a
# non-fixing PR is upgraded to a closing declaration.
NEGATION_RE = re.compile(
    r"(?:尚未|还未|还没有|暂未|未|不曾|没有任何|并不|不会|不再)"
    r"(?:[^。；;\n]{0,12})"
    r"(?:修复|解决|合入|提交|闭环|覆盖|对应|完成)"
)
# Negation window: look this many characters before a fix/self-ref match for a
# leading negation on the same clause.
NEGATION_WINDOW = 24

# Title normalisation for the similarity fallback.
TEMPLATE_PREFIX_RE = re.compile(r"^\s*\[[^\]]{2,60}\]\s*[:：]?\s*")
CONVENTIONAL_PREFIX_RE = re.compile(r"^\s*[a-z]+(?:\([^)]*\))?\s*[:：]\s*")
CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")
LATIN_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.\-]{2,}")

PHASE_DECLARED = "issue_declared"
PHASE_MENTIONED = "issue_mention"
PHASE_INFERRED = "pr_reference"
PHASE_SIMILARITY = "title_similarity"
PHASE_ORDER = (PHASE_DECLARED, PHASE_MENTIONED, PHASE_INFERRED, PHASE_SIMILARITY)

CLASS_DECLARED_CLOSE = "可直接闭环（Issue 已声明）"
CLASS_DECLARED_WAIT = "PR 进行中（Issue 已声明）"
CLASS_DECLARED_UNMERGED = "PR 已关闭未合入（Issue 已声明）"
CLASS_MENTION_MERGED = "PR 已合并，待核对闭环（Issue 仅提及）"
CLASS_MENTION_WAIT = "PR 进行中（Issue 仅提及）"
CLASS_MENTION_UNMERGED = "PR 已关闭未合入（Issue 仅提及）"
CLASS_INFERRED_MERGED = "PR 已合并，待核对闭环（PR 侧引用）"
CLASS_INFERRED_WAIT = "PR 进行中（PR 侧引用）"
CLASS_INFERRED_UNMERGED = "PR 已关闭未合入（PR 侧引用）"
CLASS_SIMILARITY = "疑似匹配，需人工判断"
CLASS_CLOSED = "无需处理（Issue 已关闭）"

CLASSIFICATION_ORDER = (
    CLASS_DECLARED_CLOSE,
    CLASS_DECLARED_WAIT,
    CLASS_DECLARED_UNMERGED,
    CLASS_MENTION_MERGED,
    CLASS_MENTION_WAIT,
    CLASS_MENTION_UNMERGED,
    CLASS_INFERRED_MERGED,
    CLASS_INFERRED_WAIT,
    CLASS_INFERRED_UNMERGED,
    CLASS_SIMILARITY,
    CLASS_CLOSED,
)
CLOSABLE_CLASSES = (CLASS_DECLARED_CLOSE,)
CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}

BARE_MENTION_REASON = "同一句提到 PR 的 #N 引用"
BARE_CLAIM_REASON = "Issue 声明同句的 PR 处理本 Issue"
MENTION_MAX_PER_ISSUE = 3

# Similarity thresholds, calibrated on cann/cannbot-knowledge (79 issues / 239 PRs).
SIMILARITY_MIN_COVERAGE = 0.34
SIMILARITY_MIN_SHARED = 2
SIMILARITY_MIN_IDF = 1.8
SIMILARITY_MAX_PER_ISSUE = 2


def strip_html_comments(text: str) -> str:
    """Remove HTML comments so PR/issue templates do not create fake links."""
    return re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)


def _refs(regex: re.Pattern[str], text: str, group: int = 1) -> set[int]:
    return {int(match.group(group)) for match in regex.finditer(text) if match.group(group)}


def _pr_url_numbers(text: str, repo: str | None) -> set[int]:
    """Numbers from full PR URLs, filtered by repository ownership.

    A URL like ``https://gitcode.com/another/repo/pull/251`` names a PR in a
    different repository: its number must not be matched against this repo's
    PR #251 merge state. ``repo`` is the ``owner/name`` being scanned; when it
    cannot be determined, no URL is trusted as a same-repo reference.
    """
    numbers: set[int] = set()
    for match in PR_URL_RE.finditer(text):
        if repo is None:
            continue
        url_repo = (match.group("repo") or "").strip("/")
        if url_repo != repo:
            continue
        numbers.add(int(match.group("number")))
    return numbers


def _issue_tagged_numbers(text: str) -> set[int]:
    """Numbers explicitly labelled as issues, excluding "本 Issue： #225".

    "本 Issue： #225" is a self-reference followed by a PR number, but
    ``ISSUE_MENTION_RE`` sees "Issue： #225" and would tag 225 as an issue,
    which then drops a real PR reference through the ambiguity guard.
    """
    numbers: set[int] = set()
    for match in ISSUE_MENTION_RE.finditer(text):
        prefix = text[max(0, match.start() - 2) : match.start()]
        if any(char in prefix for char in "本该此上述"):
            continue
        numbers.add(int(match.group(1)))
    return numbers


def _is_negated(segment: str, position: int) -> bool:
    """True when the word at ``position`` is preceded by a negation.

    Looks back one clause (``NEGATION_WINDOW`` characters) for a negation
    immediately followed by a fix-shaped verb, e.g. "尚未修复"、"仍未解决".
    Negations standing alone ("未在 950 验证") do not count because the
    following word is not a fix verb.
    """
    window = segment[max(0, position - NEGATION_WINDOW) : position + 8]
    return bool(NEGATION_RE.search(window))


def extract_pr_side_refs(title: str, body: str, branch: str) -> list[tuple[int, str, str, str]]:
    """Return (issue_number, confidence, reason, strength) candidates named by a PR.

    Bare ``#N`` references are deliberately ignored: GitCode numbers issues and
    pull requests in separate sequences, so a bare reference is ambiguous and
    produces false links ("Depends on #15" may point at another PR).
    """
    text = strip_html_comments(f"{title}\n{body}")
    refs: list[tuple[int, str, str, str]] = []

    for match in CLOSING_RE.finditer(text):
        number = match.group(1) or match.group(2)
        if number:
            refs.append((int(number), "high", "PR 文本中的关闭/关联关键词", "closing"))
    for number in _refs(ISSUE_URL_RE, text):
        refs.append((number, "high", "PR 文本中的 Issue 链接", "closing"))
    prefix = TITLE_PREFIX_RE.match(title)
    if prefix:
        refs.append((int(prefix.group(1)), "high", "PR 标题以 #N 开头", "closing"))
    for number in _refs(ISSUE_MENTION_RE, text):
        refs.append((number, "medium", "PR 文本中的 Issue #N 提及", "reference"))
    if branch:
        for match in BRANCH_ISSUE_RE.finditer(branch):
            refs.append((int(match.group(1)), "medium", "PR 源分支名包含 issue 编号", "reference"))
    return refs


def extract_issue_side_refs(
    title: str, body: str, comments: Iterable[str], repo: str | None = None
) -> list[tuple[int, str, str, str, str]]:
    """Return (pr_number, confidence, reason, strength, kind) candidates named by an issue.

    ``kind`` separates a claim that the PR resolves this issue (``declare``) from
    an incidental reference (``mention``). Conflating the two turns "built an
    experimental index on PR #68" into "PR #68 closes this issue".

    ``repo`` is the ``owner/name`` being scanned. Only same-repo PR URLs count
    as declarations; a URL into another repository stays a mention at best, so
    its number can never borrow this repo's merge state. A negated fix verb
    ("本 Issue 尚未修复") likewise never forms a declaration.
    """
    text = strip_html_comments("\n".join([title, body, *comments]))
    refs: list[tuple[int, str, str, str, str]] = []

    for segment in SEGMENT_SPLIT_RE.split(text):
        if not segment.strip():
            continue
        mentioned = _refs(PR_MENTION_RE, segment)
        linked = _pr_url_numbers(segment, repo)
        solved: set[int] = set()
        for match in PR_SOLVE_RE.finditer(segment):
            # "原 PR #99 已并入 PR #100" resolves another PR, not this issue.
            prefix = segment[max(0, match.start() - 30) : match.start()]
            if re.search(r"(?:PR|pull\s*request)\s*[:：]?\s*#?\d+", prefix, re.IGNORECASE):
                continue
            # "尚未合入 PR #100": the solve verb is negated, not a declaration.
            if _is_negated(segment, match.start()):
                continue
            solved.add(int(match.group(1)))
        # "Issue #88" is an issue number, not a PR number, even in a PR sentence.
        bare = _refs(BARE_REF_RE, segment) - _issue_tagged_numbers(segment) - mentioned
        self_ref = SELF_REF_RE.search(segment)
        fix_verb = FIX_VERB_RE.search(segment)
        # A negated fix verb ("本 Issue 尚未修复") is the opposite of a claim.
        if fix_verb and _is_negated(segment, fix_verb.start()):
            fix_verb = None
        claims_fix = bool(
            LABELED_PR_RE.search(segment) or (self_ref and fix_verb)
        )

        for number in solved:
            refs.append((number, "high", "Issue 侧“已提交/已合入 PR #N”表述", "closing", "declare"))
        for number in linked | mentioned:
            if claims_fix:
                refs.append((number, "high", "Issue 声明该 PR 与本 Issue 对应/修复", "closing", "declare"))
            else:
                refs.append((number, "medium", "Issue 文本或评论提及该 PR", "reference", "mention"))
        for number in bare:
            if claims_fix:
                # Declaration strength; the issue-number guard still applies.
                refs.append((number, "medium", BARE_CLAIM_REASON, "closing", "declare"))
            elif PR_KEYWORD_RE.search(segment):
                # Co-occurrence alone is a relation, not proof that the PR closes it.
                refs.append((number, "low", BARE_MENTION_REASON, "reference", "mention"))
    return refs


def _add_evidence(
    pairs: dict[tuple[int, int], dict[str, Any]],
    issue: int,
    pr: int,
    confidence: str,
    reason: str,
    strength: str,
    phase: str,
) -> None:
    entry = pairs.setdefault(
        (issue, pr),
        {
            "issue": issue,
            "pr": pr,
            "phase": phase,
            "confidence": "low",
            "evidence": [],
            "closing": False,
        },
    )
    if CONFIDENCE_RANK[confidence] > CONFIDENCE_RANK[entry["confidence"]]:
        entry["confidence"] = confidence
    if strength == "closing":
        entry["closing"] = True
    if reason not in entry["evidence"]:
        entry["evidence"].append(reason)


def _is_merged(pull: dict[str, Any]) -> bool:
    return bool(pull.get("merged_at"))


def _pr_is_open(pull: dict[str, Any]) -> bool:
    return str(pull.get("state") or "").lower() in {"open", "opened"}


def classify(issue: dict[str, Any], pull: dict[str, Any], phase: str) -> str:
    """Turn (issue, PR, evidence phase) into an actionable bucket."""
    if str(issue.get("state") or "").lower() != "open":
        return CLASS_CLOSED
    merged = _is_merged(pull)
    if phase == PHASE_DECLARED:
        if merged:
            return CLASS_DECLARED_CLOSE
        return CLASS_DECLARED_WAIT if _pr_is_open(pull) else CLASS_DECLARED_UNMERGED
    if phase == PHASE_MENTIONED:
        if merged:
            return CLASS_MENTION_MERGED
        return CLASS_MENTION_WAIT if _pr_is_open(pull) else CLASS_MENTION_UNMERGED
    if phase == PHASE_INFERRED:
        if merged:
            return CLASS_INFERRED_MERGED
        return CLASS_INFERRED_WAIT if _pr_is_open(pull) else CLASS_INFERRED_UNMERGED
    return CLASS_SIMILARITY


def _title_tokens(text: str) -> set[str]:
    """Tokens for coarse title matching: latin identifiers plus CJK bigrams."""
    value = strip_html_comments(text or "").lower()
    value = TEMPLATE_PREFIX_RE.sub("", value)
    value = CONVENTIONAL_PREFIX_RE.sub("", value)
    tokens = set(LATIN_TOKEN_RE.findall(value))
    for run in CJK_RUN_RE.findall(value):
        for index in range(len(run) - 1):
            tokens.add(run[index : index + 2])
    return {token for token in tokens if token.strip("._-")}


def build_idf(token_sets: list[set[str]]) -> dict[str, float]:
    """Inverse document frequency over all titles, so generic words weigh little."""
    total = len(token_sets)
    document_frequency: dict[str, int] = {}
    for tokens in token_sets:
        for token in tokens:
            document_frequency[token] = document_frequency.get(token, 0) + 1
    return {token: math.log(1 + total / (1 + count)) for token, count in document_frequency.items()}


def similarity(issue_tokens: set[str], pr_tokens: set[str], idf: dict[str, float]) -> tuple[float, int, float]:
    """Return (coverage of the issue title, shared token count, max shared idf)."""
    if not issue_tokens or not pr_tokens:
        return 0.0, 0, 0.0
    shared = issue_tokens & pr_tokens
    if not shared:
        return 0.0, 0, 0.0
    issue_weight = sum(idf.get(token, 1.0) for token in issue_tokens) or 1.0
    shared_weight = sum(idf.get(token, 1.0) for token in shared)
    return shared_weight / issue_weight, len(shared), max(idf.get(token, 1.0) for token in shared)


def triage_phase(
    issues: list[dict[str, Any]],
    pull_index: dict[int, dict[str, Any]],
    issue_index: dict[int, dict[str, Any]],
    comments_by_issue: dict[int, list[str]],
    repo: str | None = None,
) -> tuple[dict[tuple[int, int], dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Phase 1 and 2: split issues into declared / mentioned / untouched.

    A declaration outranks a mention, so an issue that says "fixed by PR #225"
    does not also get reported against every PR it happens to reference.
    """
    pairs: dict[tuple[int, int], dict[str, Any]] = {}
    mentioned_only: list[dict[str, Any]] = []
    untouched: list[dict[str, Any]] = []

    for issue in issues:
        issue_number = int(issue["number"])
        declares: list[tuple[int, str, str, str, str]] = []
        mentions: list[tuple[int, str, str, str, str]] = []
        for number, confidence, reason, strength, kind in extract_issue_side_refs(
            str(issue.get("title") or ""),
            str(issue.get("body") or ""),
            comments_by_issue.get(issue_number, []),
            repo,
        ):
            if number not in pull_index:
                continue
            # A bare reference that is also an issue number is ambiguous; skip it.
            if reason in (BARE_MENTION_REASON, BARE_CLAIM_REASON) and number in issue_index:
                continue
            (declares if kind == "declare" else mentions).append(
                (number, confidence, reason, strength, kind)
            )

        if declares:
            for number, confidence, reason, strength, _ in declares:
                _add_evidence(pairs, issue_number, number, confidence, reason, strength, PHASE_DECLARED)
            continue

        if mentions:
            mentions.sort(key=lambda item: -CONFIDENCE_RANK[item[1]])
            for number, confidence, reason, strength, _ in mentions[:MENTION_MAX_PER_ISSUE]:
                _add_evidence(pairs, issue_number, number, confidence, reason, strength, PHASE_MENTIONED)
            mentioned_only.append(issue)
            continue

        untouched.append(issue)

    return pairs, mentioned_only, untouched


def infer_phase(
    pairs: dict[tuple[int, int], dict[str, Any]],
    untouched: list[dict[str, Any]],
    pulls: list[dict[str, Any]],
    idf: dict[str, float],
    stale_declared: list[dict[str, Any]],
) -> None:
    """Phase 3 and 4: match issues that name no PR, plus stale declarations.

    PR-side references come first; title similarity is only a fallback for
    issues that remain unmatched, so weak guesses never outrank real evidence.
    Evidence is accumulated into ``pairs`` in place: ``_add_evidence`` keeps the
    first phase recorded, so a later weaker phase cannot downgrade a declaration.
    """
    # A stale declaration still deserves PR-side matching against other PRs.
    target_index = {int(item["number"]): item for item in [*untouched, *stale_declared]}
    matched: set[int] = set()

    for pull in pulls:
        pr_number = int(pull["number"])
        for number, confidence, reason, strength in extract_pr_side_refs(
            str(pull.get("title") or ""),
            str(pull.get("body") or ""),
            str(pull.get("source_branch") or ""),
        ):
            if number not in target_index:
                continue
            _add_evidence(pairs, number, pr_number, confidence, reason, strength, PHASE_INFERRED)
            matched.add(number)

    candidates = [*untouched, *stale_declared]
    for issue in candidates:
        issue_number = int(issue["number"])
        if issue_number in matched:
            continue
        issue_tokens = _title_tokens(str(issue.get("title") or ""))
        scored: list[tuple[float, float, int, dict[str, Any]]] = []
        for pull in pulls:
            coverage, shared, max_idf = similarity(issue_tokens, _title_tokens(str(pull.get("title") or "")), idf)
            if shared < SIMILARITY_MIN_SHARED or coverage < SIMILARITY_MIN_COVERAGE:
                continue
            if max_idf < SIMILARITY_MIN_IDF:
                continue
            scored.append((coverage, max_idf, shared, pull))
        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        for coverage, _max_idf, shared, pull in scored[:SIMILARITY_MAX_PER_ISSUE]:
            reason = f"标题相似度 {coverage:.2f}（共享词 {shared}）"
            _add_evidence(
                pairs, issue_number, int(pull["number"]), "low", reason, "reference", PHASE_SIMILARITY
            )


def build_pairs(
    issues: list[dict[str, Any]],
    pulls: list[dict[str, Any]],
    comments_by_issue: dict[int, list[str]],
    repo: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run all phases and return (pairs, funnel statistics)."""
    issue_index = {int(item["number"]): item for item in issues}
    pull_index = {int(item["number"]): item for item in pulls}
    idf = build_idf([_title_tokens(str(item.get("title") or "")) for item in [*issues, *pulls]])

    pairs, mentioned_only, untouched = triage_phase(issues, pull_index, issue_index, comments_by_issue, repo)

    # Declared-but-unmerged: the declaration may be stale, so probe other PRs.
    stale_declared: list[dict[str, Any]] = []
    declared_issues = {
        issue for (issue, _pr), entry in pairs.items() if entry["phase"] == PHASE_DECLARED
    }
    for issue_number in declared_issues:
        declared_prs = [pr for (issue, pr), entry in pairs.items()
                        if issue == issue_number and entry["phase"] == PHASE_DECLARED]
        if all(not _is_merged(pull_index[pr]) for pr in declared_prs):
            stale_declared.append(issue_index[issue_number])

    infer_phase(pairs, untouched, pulls, idf, stale_declared)

    results: list[dict[str, Any]] = []
    for (issue_number, pr_number), entry in pairs.items():
        issue = issue_index[issue_number]
        pull = pull_index[pr_number]
        entry["classification"] = classify(issue, pull, entry["phase"])
        entry["issue_title"] = str(issue.get("title") or "")
        entry["issue_state"] = str(issue.get("state") or "")
        entry["pr_title"] = str(pull.get("title") or "")
        entry["pr_state"] = str(pull.get("state") or "")
        entry["pr_merged_at"] = pull.get("merged_at")
        entry["pr_url"] = pull.get("html_url") or pull.get("web_url")
        entry["issue_url"] = issue.get("html_url")
        results.append(entry)

    results.sort(
        key=lambda item: (
            CLASSIFICATION_ORDER.index(item["classification"]),
            PHASE_ORDER.index(item["phase"]),
            -CONFIDENCE_RANK[item["confidence"]],
            item["issue"],
            item["pr"],
        )
    )

    linked_issues = {item["issue"] for item in results}
    funnel = {
        "issues": len(issues),
        "issues_declared": len({item["issue"] for item in results if item["phase"] == PHASE_DECLARED}),
        "issues_mentioned": len({item["issue"] for item in results if item["phase"] == PHASE_MENTIONED}),
        "issues_matched_by_pr_reference": len(
            {item["issue"] for item in results if item["phase"] == PHASE_INFERRED}
        ),
        "issues_matched_by_similarity": len(
            {item["issue"] for item in results if item["phase"] == PHASE_SIMILARITY}
        ),
        "issues_unmatched": sum(1 for issue in issues if int(issue["number"]) not in linked_issues),
        "closable_pairs": sum(1 for item in results if item["classification"] in CLOSABLE_CLASSES),
        "closable_issues": len(
            {item["issue"] for item in results if item["classification"] in CLOSABLE_CLASSES}
        ),
        "unmatched_list": [
            {
                "issue": int(issue["number"]),
                "title": str(issue.get("title") or ""),
                "url": issue.get("html_url"),
                "state": str(issue.get("state") or ""),
            }
            for issue in issues
            if int(issue["number"]) not in linked_issues
        ],
    }
    return results, funnel


def suggest_comment(pair: dict[str, Any]) -> str:
    """Draft a comment for human review. Never posted by this script."""
    pr = f"#{pair['pr']}"
    classification = pair["classification"]
    if classification == CLASS_DECLARED_CLOSE:
        return (
            f"本 Issue 声明的 PR {pr} 已合入，改动已进入主干。"
            "如无后续问题，建议关闭本 Issue；如仍有未覆盖场景，请在此补充。"
        )
    if classification == CLASS_DECLARED_WAIT:
        return f"本 Issue 声明的 PR {pr} 仍在评审中，尚未合入，暂不具备关闭条件。"
    if classification == CLASS_DECLARED_UNMERGED:
        return (
            f"本 Issue 声明的 PR {pr} 已关闭且未合入，声明已失效。"
            "请确认修复是否已通过其他改动进入主干。"
        )
    if classification == CLASS_MENTION_MERGED:
        return (
            f"检索到 PR {pr} 与本 Issue 涉及同一处改动且已合入。"
            "请确认该 PR 是否已完全覆盖本 Issue 描述的问题。"
        )
    if classification == CLASS_MENTION_WAIT:
        return f"本 Issue 中提到的 PR {pr} 仍在评审中，尚未合入。"
    if classification == CLASS_MENTION_UNMERGED:
        return f"本 Issue 中提到的 PR {pr} 已关闭且未合入，请确认是否已有替代改动。"
    if classification == CLASS_INFERRED_MERGED:
        return (
            f"检索到 PR {pr} 可能对应本 Issue 且已合入。"
            "请确认该 PR 是否已完全覆盖本 Issue 描述的问题。"
        )
    if classification == CLASS_INFERRED_WAIT:
        return f"检索到可能对应的 PR {pr}，当前仍在评审中，尚未合入。"
    if classification == CLASS_INFERRED_UNMERGED:
        return f"检索到与本 Issue 相关的 PR {pr}，该 PR 已关闭且未合入，请确认是否需要另开改动。"
    return ""


def _cell(text: str, limit: int | None = None) -> str:
    value = text.replace("|", "\\|").replace("\n", " ")
    if limit is not None and len(value) > limit:
        value = value[:limit].rstrip() + "…"
    return value


def _render_table(report: dict[str, Any], classifications: tuple[str, ...], lines: list[str]) -> None:
    group = [item for item in report["pairs"] if item["classification"] in classifications]
    if not group:
        lines.extend(["未发现该类关联。", ""])
        return
    lines.append("| Issue | PR | 置信度 | 证据 |")
    lines.append("|---|---|---|---|")
    for item in group:
        evidence = _cell("；".join(item["evidence"]))
        lines.append(
            f"| [#{item['issue']}]({item['issue_url']}) {_cell(item['issue_title'], 40)} "
            f"| [#{item['pr']}]({item['pr_url']}) {_cell(item['pr_title'], 40)} "
            f"| {item['confidence']} | {evidence} |"
        )
    lines.append("")


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    funnel = report["funnel"]
    scope = report["issue_state"]
    if report.get("issue_filter"):
        scope = f"单 Issue 模式，仅 #{report['issue_filter']}（忽略状态过滤）"
    lines = [
        "# PR–Issue 关联扫描报告",
        "",
        f"- 仓库：`{report['repo']}`",
        f"- 扫描时间：{report['fetched_at']}",
        f"- Issue：{summary['issues']} 条（{scope}）",
        f"- PR：{summary['pulls']} 条（{report['pr_state']}）",
        "",
        "## 漏斗",
        "",
        "| 阶段 | Issue 数 |",
        "|---|---|",
        f"| 扫描范围 | {funnel['issues']} |",
        f"| ① Issue 明确声明修复 PR | {funnel['issues_declared']} |",
        f"| ② Issue 仅提及 PR | {funnel['issues_mentioned']} |",
        f"| ③ 未声明 → PR 侧反向引用 | {funnel['issues_matched_by_pr_reference']} |",
        f"| ④ 未声明 → 仅标题相似 | {funnel['issues_matched_by_similarity']} |",
        f"| 未发现任何关联 | {funnel['issues_unmatched']} |",
        "",
        f"可直接闭环：{funnel['closable_issues']} 个 Issue（{funnel['closable_pairs']} 个已合入 PR）。",
        "",
        "> 本报告为只读扫描结果，未向 GitCode 写入任何内容。`关联` 仅为文本证据推断，发布评论或关闭 Issue 前必须人工核对。",
        "",
    ]
    if not report["pairs"]:
        lines.append("未发现可关联的 Issue/PR 组合。")
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            "## ① Issue 明确声明修复 PR",
            "",
            "Issue 或其评论直接说明“本 Issue 由 PR #N 修复/已提交 PR #N”，按该 PR 自身状态判定，无需再匹配。",
            "",
        ]
    )
    _render_table(report, (CLASS_DECLARED_CLOSE, CLASS_DECLARED_WAIT, CLASS_DECLARED_UNMERGED), lines)

    lines.extend(
        [
            "## ② Issue 仅提及 PR",
            "",
            "Issue 提到某个 PR 但未声称由它修复（例如“在 PR #68 的提交上建索引”“与 PR #100 互补”）。合入也需人工确认覆盖范围，**不可直接关闭**。",
            "",
        ]
    )
    _render_table(report, (CLASS_MENTION_MERGED, CLASS_MENTION_WAIT, CLASS_MENTION_UNMERGED), lines)

    lines.extend(
        [
            "## ③ Issue 未声明，PR 侧反向引用",
            "",
            "Issue 本身没提 PR，由 PR 的关闭关键词、`Issue #N`、`#N:` 标题前缀或 `issue-N` 分支反向命中。",
            "",
        ]
    )
    _render_table(report, (CLASS_INFERRED_MERGED, CLASS_INFERRED_WAIT, CLASS_INFERRED_UNMERGED), lines)

    lines.extend(
        [
            "## ④ 仅标题相似",
            "",
            "两侧都没有显式引用，只按标题词重合推断。**不可直接关闭**，必须读 diff 确认。",
            "",
        ]
    )
    _render_table(report, (CLASS_SIMILARITY,), lines)

    if funnel["unmatched_list"]:
        lines.extend(["## 未发现任何关联的 Issue", "", "| Issue | 标题 |", "|---|---|"])
        for item in funnel["unmatched_list"]:
            lines.append(f"| [#{item['issue']}]({item['url']}) | {_cell(item['title'], 60)} |")
        lines.append("")

    drafts = [item for item in report["pairs"] if suggest_comment(item)]
    if drafts:
        lines.extend(["## 评论草稿（需人工确认后另行发布）", ""])
        for item in drafts:
            lines.extend([f"### Issue #{item['issue']} ← PR #{item['pr']}", "", suggest_comment(item), ""])
    return "\n".join(lines) + "\n"


def _request(url: str, token: str | None) -> Any:
    """GET one GitCode API URL.

    The token rides as the ``access_token`` query parameter, matching the
    vendored ``gitcode_client.py``: GitCode documents this form for v5 and
    some endpoints reject the ``PRIVATE-TOKEN`` header outright.
    """
    if token:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}access_token={urllib.parse.quote(token, safe='')}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def api_get(path: str, params: dict[str, Any], token: str | None) -> Any:
    query = urllib.parse.urlencode(params)
    url = f"{API_ROOT}{path}?{query}"
    for attempt in range(2):
        try:
            return _request(url, token)
        except urllib.error.HTTPError as error:
            if error.code in {429, 500, 502, 503, 504} and attempt == 0:
                time.sleep(24 if error.code == 429 else 3)
                continue
            raise
        except urllib.error.URLError:
            if attempt == 0:
                time.sleep(2)
                continue
            raise
    raise RuntimeError(f"request failed: {url}")


def paginate(
    path: str,
    token: str | None,
    max_pages: int,
    per_page: int = 100,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        query = {"per_page": per_page, "page": page}
        query.update(params or {})
        batch = api_get(path, query, token)
        if not isinstance(batch, list):
            raise RuntimeError(f"unexpected response for {path}: {type(batch).__name__}")
        collected.extend(item for item in batch if isinstance(item, dict))
        if len(batch) < per_page:
            break
        if page == max_pages:
            print(
                f"warning: {path} hit the --max-pages ceiling ({max_pages} pages); "
                "results are truncated, raise --max-pages for a full scan",
                file=sys.stderr,
            )
        time.sleep(0.5)
    return collected


def fetch_comments(
    repo: str, issues: list[dict[str, Any]], token: str | None, limit: int
) -> dict[int, list[str]]:
    comments: dict[int, list[str]] = {}
    candidates = [issue for issue in issues if issue.get("comments")][:limit]
    for issue in candidates:
        number = int(issue["number"])
        batch = api_get(f"/repos/{repo}/issues/{number}/comments", {"per_page": 100}, token)
        if isinstance(batch, list):
            comments[number] = [str(item.get("body") or "") for item in batch if isinstance(item, dict)]
        time.sleep(0.2)
    return comments


def write_outputs(
    output_dir: Path,
    report: dict[str, Any],
    issues: list[dict[str, Any]],
    pulls: list[dict[str, Any]],
    comments: dict[int, list[str]],
) -> None:
    raw = output_dir / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "issues.json").write_text(
        json.dumps(issues, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    (raw / "pulls.json").write_text(
        json.dumps(pulls, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    (raw / "comments.json").write_text(
        json.dumps({str(key): value for key, value in comments.items()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "pr-issue-links.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    (output_dir / "pr-issue-links.md").write_text(
        render_markdown(report), encoding="utf-8", newline="\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan GitCode issues and PRs for likely links (read-only).")
    parser.add_argument("--repo", required=True, help="owner/repo, e.g. cann/cannbot-knowledge")
    parser.add_argument("--issue-state", default="open", choices=["open", "closed", "all"])
    parser.add_argument(
        "--issue",
        type=int,
        help="scan a single issue number instead of the whole repository (state filter is ignored)",
    )
    parser.add_argument("--pr-state", default="all", choices=["open", "closed", "merged", "all"])
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--comment-limit", type=int, default=100, help="max issues whose comments are fetched")
    parser.add_argument("--output-dir", default=".cannbot/gitcode-issue-handler/data/pr-issue-links")
    parser.add_argument(
        "--from-raw",
        help="reuse previously saved raw JSON directory instead of calling the API (offline re-run)",
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable summary")
    args = parser.parse_args(argv)

    if args.from_raw:
        raw = Path(args.from_raw)
        issues = json.loads((raw / "issues.json").read_text(encoding="utf-8"))
        pulls = json.loads((raw / "pulls.json").read_text(encoding="utf-8"))
        comments = {
            int(key): list(value)
            for key, value in json.loads((raw / "comments.json").read_text(encoding="utf-8")).items()
        } if (raw / "comments.json").exists() else {}
    else:
        token = os.environ.get("GITCODE_TOKEN") or None
        if args.issue:
            try:
                single = api_get(f"/repos/{args.repo}/issues/{args.issue}", {}, token)
            except urllib.error.HTTPError as error:
                print(f"issue #{args.issue} not readable: HTTP {error.code}", file=sys.stderr)
                return 2
            if not isinstance(single, dict) or "number" not in single:
                print(f"issue #{args.issue} returned an unexpected payload", file=sys.stderr)
                return 2
            issues = [single]
        else:
            issues = paginate(
                f"/repos/{args.repo}/issues", token, args.max_pages, params={"state": args.issue_state}
            )
        pulls = paginate(
            f"/repos/{args.repo}/pulls", token, args.max_pages, params={"state": args.pr_state}
        )
        comments = fetch_comments(args.repo, issues, token, args.comment_limit)
    if args.issue and args.from_raw:
        issues = [issue for issue in issues if int(issue["number"]) == args.issue]
    if not issues:
        print(f"no issue matched: #{args.issue}" if args.issue else "no issue found", file=sys.stderr)
        return 2
    pairs, funnel = build_pairs(issues, pulls, comments, args.repo)

    report = {
        "repo": args.repo,
        "fetched_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "issue_state": args.issue_state,
        "pr_state": args.pr_state,
        "issue_filter": args.issue,
        "summary": {
            "issues": len(issues),
            "pulls": len(pulls),
            "pairs": len(pairs),
            "suggest_close": funnel["closable_pairs"],
        },
        "funnel": funnel,
        "pairs": pairs,
    }
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_outputs(output_dir, report, issues, pulls, comments)

    if args.json:
        print(json.dumps({"summary": report["summary"], "funnel": funnel}, ensure_ascii=False))
    else:
        summary = report["summary"]
        print(
            f"issues={summary['issues']} pulls={summary['pulls']} pairs={summary['pairs']} "
            f"declared={funnel['issues_declared']} mentioned={funnel['issues_mentioned']} "
            f"closable={funnel['closable_issues']} unmatched={funnel['issues_unmatched']}"
        )
        print(f"report: {output_dir / 'pr-issue-links.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
