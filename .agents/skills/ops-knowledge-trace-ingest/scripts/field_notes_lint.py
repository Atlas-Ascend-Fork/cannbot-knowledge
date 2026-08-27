#!/usr/bin/env python3
"""runbook OKF 卡片正文 validator（runbooks 落库契约 §6 正文类 HARD 约束实现）。

frontmatter 结构与受控词表校验由本仓统一 Contract（governance/contracts/knowledge.py，
经 knowledge-lint 执行）承载；本脚本只做 runbook **正文** 专属约束：
  ㉑ 正文必须含 `## 适用场景`（缺失记 warn，聚合单条输出；新卡由审查门禁按 blocker 拦截）
  ⑫ 完整配方类 runbook 完整性（## 系统信息 + ## 完整代码 + ## 设计决策）
  ⑲ 验证信号逐条标来源平台与证据等级（tool_observed / artifact_verified）
  ⑳ okf:attachment 禁用（新卡正文出现即 warn）
  ③ 文件名纯 slug / 无 session 前缀
  ⑦ 「## 相关」双向闭合（okf:related 块 markdown 文件超链接，支持跨树回链）

违反任一 HARD 约束 → 退出码非零。只读只报。
frontmatter 不设 evidence/confidence/transfer_scope/quality_score/reproduce_count
等字段——证据强度由正文 `## 验证信号` 与内部 ledger/manifest 复现判定派生。
"""
import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

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


def parse_fm(text: str) -> dict:
    metadata, _ = split_frontmatter(text)
    return metadata or {}


def parse_related_files(text: str, base_dir: Path) -> set[Path]:
    match = re.search(
        r"<!-- okf:related:start -->(.*?)<!-- okf:related:end -->", text, re.DOTALL
    )
    if not match:
        return set()
    return {
        (base_dir / unquote(target)).resolve()
        for target in re.findall(
            r"\[(?:[^\[\]]|\[[^\]]*\])*\]\(([^)]+)\)", match.group(1)
        )
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "knowledge_root",
        nargs="?",
        type=Path,
        default=DEFAULT_ROOT,
        help="cannbot-knowledge root; defaults to the enclosing repository",
    )
    args = parser.parse_args()
    root = args.knowledge_root.resolve()
    Contract(root)
    errs: list[str] = []
    warns: list[str] = []
    missing_scope: list[str] = []
    cards: dict[str, tuple[Path, dict, str]] = {}

    knowledge_root = root / "knowledge"
    if not knowledge_root.is_dir():
        print(f"FAIL: no knowledge tree at {knowledge_root}", file=sys.stderr)
        return 1
    runbook_directories = sorted(
        {
            path.parent
            for path in knowledge_root.rglob("*.md")
            if "runbooks" in path.parts and path.name != "index.md"
        }
    )
    for card_path in sorted(
        path
        for path in knowledge_root.rglob("*.md")
        if path.name != "index.md" and "runbooks" in path.parts
    ):
        text = card_path.read_text(encoding="utf-8")
        fm = parse_fm(text)
        if not fm:
            errs.append(f"{card_path}: 无 frontmatter")
            continue
        slug = card_path.stem
        cards[slug] = (card_path, fm, text)
        if not SLUG_RE.fullmatch(slug):
            errs.append(f"{card_path.name}: 文件名非纯 slug [约束③]")
        if SESSION_PREFIX_RE.match(slug):
            errs.append(f"{card_path.name}: 文件名含 session 前缀 [约束③]")
        if "## 适用场景" not in text:
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
                if not re.search(r"来源平台\s*[:：]", line):
                    errs.append(f"{card_path.name}: 验证信号未逐条标来源平台：{line} [约束⑲]")
                level = re.search(r"证据等级\s*[:：]\s*([a-z_]+)", line)
                if not level or level.group(1) not in {"tool_observed", "artifact_verified"}:
                    errs.append(f"{card_path.name}: 验证信号未逐条标可用证据等级：{line} [约束⑲]")
        if "okf:attachment" in text:
            warns.append(
                f"{card_path.name}: 正文含已弃用的 `okf:attachment` 标记（存量卡遗留容忍，新卡须正文内联）[约束⑳]"
            )

    for slug, (path, _, text) in cards.items():
        targets = parse_related_files(text, path.parent)
        for target in targets:
            if not target.is_file():
                errs.append(f"{path.name}: 相关链接 `{target.name}` 对侧文件不存在 [约束⑦]")
                continue
            back = parse_related_files(target.read_text(encoding="utf-8"), target.parent)
            if path.resolve() not in back:
                errs.append(f"{path.name}: 相关链接 `{target.name}` 对侧未回链 [约束⑦]")

    n_cards = len(cards)
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
