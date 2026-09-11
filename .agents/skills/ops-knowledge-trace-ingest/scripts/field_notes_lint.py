#!/usr/bin/env python3
"""runbook OKF 卡片正文 validator（runbooks 落库契约 §6 正文类 HARD 约束实现）。

frontmatter 结构与受控词表校验由本仓统一 Contract（governance/contracts/knowledge.py，
经 knowledge-lint 执行）承载；本脚本对 ``--card`` / ``--staged-card`` 调用同一
Contract 做严格卡片校验，并补充 runbook **正文** 专属约束：
  ㉑ 正文必须含 `## 适用场景`（存量全扫聚合为 warn；`--card` 新/改卡按 HARD 拦截）
  ⑫ 完整配方类 runbook 完整性（## 系统信息 + ## 完整代码 + ## 设计决策）
  ⑲ 验证信号逐条标来源平台与证据等级（tool_observed / artifact_verified）
  ⑳ okf:attachment 禁用（存量全扫记 warn；`--card` 新/改卡按 HARD 拦截）
  ③ 文件名纯 slug / 无 session 前缀
  ⑦ 普通正文链接由治理 Contract 校验，不要求图谱块或构图

违反任一 HARD 约束 → 退出码非零。只读只报。
frontmatter 不设 evidence/confidence/transfer_scope/quality_score/reproduce_count
等字段——证据强度由正文 `## 验证信号` 与内部 ledger/manifest 复现判定派生。
"""
import argparse
import re
import sys
from pathlib import Path

from yaml import YAMLError

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from governance.contracts.knowledge import (  # noqa: E402
    Contract,
    split_frontmatter,
)

DEFAULT_ROOT = ROOT
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")
SESSION_PREFIX_RE = re.compile(r"^(?:s[0-9a-f]{6,}|s\d{4}-\d{2})")
RECIPE_REQUIRED = ("## 系统信息", "## 完整代码", "## 设计决策")


def has_platform_annotation(line: str, platforms: list[str]) -> bool:
    if re.search(r"来源平台\s*[:：]", line):
        return True
    aliases = {
        "950": r"(?i)(?:ascend[ -]?)?950(?:pr|dt)?",
        "a3": r"(?i)(?:atlas[ -]?)?a3|ascend910_93",
        "a2": r"(?i)(?:atlas[ -]?)?a2|ascend910b",
    }
    return any(
        re.search(aliases.get(platform, rf"(?i)\b{re.escape(platform)}\b"), line)
        for platform in platforms
    )


def has_evidence_level(line: str) -> bool:
    return bool(re.search(r"\b(?:tool_observed|artifact_verified)\b", line))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "knowledge_root",
        nargs="?",
        type=Path,
        default=DEFAULT_ROOT,
        help="cannbot-knowledge root; defaults to the enclosing repository",
    )
    parser.add_argument(
        "--card",
        action="append",
        type=Path,
        default=[],
        help="strictly validate a new/changed AscendC runbook; repeatable",
    )
    parser.add_argument(
        "--staged-card",
        action="append",
        type=Path,
        default=[],
        help="strictly validate a staged Runbook body outside knowledge/; repeatable",
    )
    args = parser.parse_args()
    root = args.knowledge_root.resolve()
    contract = Contract(root)
    errs: list[str] = []
    warns: list[str] = []
    missing_scope: list[str] = []
    strict_cards: set[Path] = set()
    contract_relatives: dict[Path, Path] = {}

    knowledge_root = root / "knowledge"
    if not knowledge_root.is_dir():
        print(f"FAIL: no knowledge tree at {knowledge_root}", file=sys.stderr)
        return 1
    runbooks_root = knowledge_root / "ops/ascendc/runbooks"
    if args.card or args.staged_card:
        for raw in args.card:
            card_path = raw if raw.is_absolute() else root / raw
            card_path = card_path.resolve()
            try:
                card_path.relative_to(runbooks_root.resolve())
            except ValueError:
                print(f"FAIL: --card must be inside {runbooks_root}: {raw}", file=sys.stderr)
                return 1
            if not card_path.is_file() or card_path.name == "index.md":
                print(f"FAIL: --card is not a runbook card: {raw}", file=sys.stderr)
                return 1
            strict_cards.add(card_path)
            contract_relatives[card_path] = card_path.relative_to(root)
        for raw in args.staged_card:
            card_path = raw if raw.is_absolute() else root / raw
            card_path = card_path.resolve()
            if (
                not card_path.is_file()
                or card_path.suffix != ".md"
                or card_path.name == "index.md"
                or card_path.parent.parent.name != "staged-cards"
            ):
                print(
                    "FAIL: --staged-card must be staged-cards/<area>/<slug>.md: "
                    f"{raw}",
                    file=sys.stderr,
                )
                return 1
            strict_cards.add(card_path)
            contract_relatives[card_path] = (
                Path("knowledge/ops/ascendc/runbooks")
                / card_path.parent.name
                / card_path.name
            )
        card_paths = sorted(strict_cards)
    else:
        card_paths = sorted(
            path for path in runbooks_root.rglob("*.md") if path.name != "index.md"
        )
    runbook_directories = sorted({path.parent for path in card_paths})
    for card_path in card_paths:
        text = card_path.read_text(encoding="utf-8")
        try:
            fm, body = split_frontmatter(text)
        except (ValueError, YAMLError) as error:
            errs.append(f"{card_path.name}: frontmatter 解析失败：{error} [机器契约]")
            continue
        if not fm:
            errs.append(f"{card_path}: 无 frontmatter")
            continue
        slug = card_path.stem
        strict = card_path in strict_cards
        if strict:
            for issue in contract.validate_card(
                contract_relatives[card_path], fm, body
            ):
                errs.append(
                    f"{card_path.name}: {issue.code}: {issue.message} [机器契约]"
                )
        if not SLUG_RE.fullmatch(slug):
            errs.append(f"{card_path.name}: 文件名非纯 slug [约束③]")
        if SESSION_PREFIX_RE.match(slug):
            errs.append(f"{card_path.name}: 文件名含 session 前缀 [约束③]")
        if "## 适用场景" not in text:
            if strict:
                errs.append(f"{card_path.name}: 缺 `## 适用场景` [约束㉑]")
            else:
                missing_scope.append(card_path.name)
        if "## 完整代码" in text and "## 系统信息" in text:
            for needed in RECIPE_REQUIRED:
                if needed not in text:
                    errs.append(f"{card_path.name}: 完整配方类 runbook 缺 `{needed}` [约束⑫]")
        validation = re.search(
            r"^## 验证信号\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
        )
        if validation:
            for line in validation.group(1).splitlines():
                if not line.startswith("- "):
                    continue
                platforms = [str(value) for value in fm.get("platforms", [])]
                platform_ok = (
                    bool(re.search(r"来源平台\s*[:：]", line))
                    if strict
                    else has_platform_annotation(line, platforms)
                )
                if not platform_ok:
                    errs.append(f"{card_path.name}: 验证信号未逐条标来源平台：{line} [约束⑲]")
                level = re.search(r"证据等级\s*[:：]\s*([a-z_]+)", line)
                level_ok = (
                    bool(level and level.group(1) in {"tool_observed", "artifact_verified"})
                    if strict
                    else has_evidence_level(line)
                )
                if not level_ok:
                    errs.append(f"{card_path.name}: 验证信号未逐条标可用证据等级：{line} [约束⑲]")
        if "okf:attachment" in text:
            message = f"{card_path.name}: 正文含已弃用的 `okf:attachment` 标记 [约束⑳]"
            (errs if strict else warns).append(message)

    n_cards = len(card_paths)
    if missing_scope:
        sample = ", ".join(missing_scope[:5])
        warns.append(
            f"{len(missing_scope)} 张缺 `## 适用场景`（存量容忍，新卡须含）[约束㉑]，示例前 5 张：{sample}"
        )
    if warns:
        print(f"WARN: {len(warns)} 条提示（不阻塞）：")
        for warn in warns:
            print(f"  - {warn}")
    if errs:
        print(f"FAIL: {len(errs)} 个 HARD 违反（共 {n_cards} 张卡）:")
        for err in errs:
            print(f"  - {err}")
        return 1
    print(
        f"PASS: {len(runbook_directories)} 个 runbooks 目录、{n_cards} 张卡全过正文 HARD 约束"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
