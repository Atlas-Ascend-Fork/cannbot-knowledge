#!/usr/bin/env bash
# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

set -euo pipefail

VERSION="0.4.3"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KNOWLEDGE_ROOT="$(realpath "$SCRIPT_DIR")"
INDEX_TOOL="$KNOWLEDGE_ROOT/.agents/skills/knowledge-query/scripts/knowledge_index.py"
PROMPT_BEGIN="<!-- cannbot-knowledge:start -->"
PROMPT_END="<!-- cannbot-knowledge:end -->"

show_help() {
  cat <<'EOF'
cannbot-knowledge project installer

Usage:
  bash init.sh <agents|codex|claude|opencode|trae|cursor|copilot> \
    <project-path> [consumer|contributor] [options]

Profiles:
  consumer       Install knowledge-query and ascendc-api-knowledge-query (default).
  contributor    Install the three base skills, ascendc-api-knowledge-query and both operator ingest skills.
                 The repository-internal trace ingest skill is not installed.

Options:
  --skip-resources
                  Skip restoring local documentation and pinned source snapshots.
                  Use only for an explicitly offline, knowledge-only installation.
  --prompt-action <uninstall|reinstall>
                  Only remove or refresh the managed project instructions. Reinstall
                  reuses the profile recorded by the previous installation unless a
                  profile is explicitly provided.
  --help          Show this help message.

The installer always creates canonical links under .agents/skills. Agent-specific
directories contain adapter links to those canonical entries. The knowledge root
is written to .cannbot/knowledge.env; no global configuration is changed.
EOF
}

fail() {
  echo "$1" >&2
  exit 2
}

link_matches() {
  local destination="$1"
  local expected="$2"
  [[ -L "$destination" ]] || return 1
  [[ "$(realpath "$destination" 2>/dev/null || true)" == "$(realpath "$expected")" ]]
}

preflight_link() {
  local source="$1"
  local destination="$2"
  local source_may_be_pending="${3:-false}"
  if [[ "$source_may_be_pending" != "true" ]]; then
    [[ -d "$source" ]] || fail "missing skill source: $source"
  fi
  if [[ -e "$destination" || -L "$destination" ]]; then
    link_matches "$destination" "$source" && return 0
    fail "refusing to overwrite existing path: $destination"
  fi
}

install_link() {
  local source="$1"
  local destination="$2"
  link_matches "$destination" "$source" && return 0
  mkdir -p "$(dirname "$destination")"
  ln -s "$source" "$destination"
}

prepare_search_index() {
  if python3 "$INDEX_TOOL" --knowledge-root "$KNOWLEDGE_ROOT" \
      verify --level quick >/dev/null 2>&1; then
    return 0
  fi
  echo "Preparing knowledge search index..."
  python3 "$INDEX_TOOL" --knowledge-root "$KNOWLEDGE_ROOT" build >/dev/null
}

write_project_env() {
  local target="$1"
  local profile="$2"
  local tmp
  local root_replacement
  local profile_replacement
  local line
  local trimmed
  local root_found=0
  local profile_found=0

  if [[ -L "$target" || ( -e "$target" && ! -f "$target" ) ]]; then
    fail "refusing to overwrite non-regular config path: $target"
  fi
  mkdir -p "$(dirname "$target")"
  tmp="$(mktemp "${target}.tmp.XXXXXX")"
  printf -v root_replacement 'export CANNBOT_KNOWLEDGE_ROOT=%q' "$KNOWLEDGE_ROOT"
  printf -v profile_replacement 'export CANNBOT_KNOWLEDGE_PROFILE=%q' "$profile"
  if [[ -f "$target" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      trimmed="${line#"${line%%[![:space:]]*}"}"
      if [[ "$trimmed" =~ ^(export[[:space:]]+)?CANNBOT_KNOWLEDGE_ROOT= ]]; then
        if [[ "$root_found" -eq 0 ]]; then
          printf '%s\n' "$root_replacement" >> "$tmp"
          root_found=1
        fi
      elif [[ "$trimmed" =~ ^(export[[:space:]]+)?CANNBOT_KNOWLEDGE_PROFILE= ]]; then
        if [[ "$profile_found" -eq 0 ]]; then
          printf '%s\n' "$profile_replacement" >> "$tmp"
          profile_found=1
        fi
      else
        printf '%s\n' "$line" >> "$tmp"
      fi
    done < "$target"
  fi
  [[ "$root_found" -eq 1 ]] || printf '%s\n' "$root_replacement" >> "$tmp"
  [[ "$profile_found" -eq 1 ]] || printf '%s\n' "$profile_replacement" >> "$tmp"
  mv "$tmp" "$target"
}

installed_profile() {
  local target="$1"
  local canonical_root="$2"
  local line
  local trimmed
  local value

  if [[ -f "$target" && ! -L "$target" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      trimmed="${line#"${line%%[![:space:]]*}"}"
      if [[ "$trimmed" =~ ^(export[[:space:]]+)?CANNBOT_KNOWLEDGE_PROFILE= ]]; then
        value="${trimmed#*=}"
        value="${value#\"}"
        value="${value%\"}"
        value="${value#\'}"
        value="${value%\'}"
        if [[ "$value" == "consumer" || "$value" == "contributor" ]]; then
          printf '%s\n' "$value"
          return 0
        fi
      fi
    done < "$target"
  fi
  if [[ -f "$canonical_root/knowledge-ingest/SKILL.md" && \
        -f "$canonical_root/knowledge-lint/SKILL.md" ]]; then
    printf '%s\n' "contributor"
  else
    printf '%s\n' "consumer"
  fi
}

generate_prompt() {
  local profile="$1"
  cat <<'EOF'
## cannbot-knowledge 使用入口

本项目已安装可检索、可溯源的 CANN 知识库消费 Skill。负责整体任务的 Agent 在 CANN、昇腾 NPU、
算子 DSL、图、模型或 Runtime 的首次领域决策前，通过 Skill 能力加载对应入口：

| 当前问题 | 入口 |
|---|---|
| Ascend C API 的契约、选型、相关知识或本地头文件 | [ascendc-api-knowledge-query](.agents/skills/ascendc-api-knowledge-query/SKILL.md) |
| 其他 CANN 知识、算子实现、调试、优化、测试或跨技术问题 | [knowledge-query](.agents/skills/knowledge-query/SKILL.md) |

两个入口共用 Query 的索引和平台规则，不需要重复启动。缺少入口时由项目安装流程补齐，不用
扫描知识树替代 Skill。收到明确子任务的 Agent 可以复用主 Agent 已取得的适用证据；只有检索子任务
或出现新的领域证据缺口时，才再次进入检索。

### 使用边界

- 加载入口前只取得任务需求和目标环境信息，不先凭经验做 API 选型、读参考实现或设计实现方案。
  目标平台确认、候选召回、选卡全文阅读及按需补证，依照所选 Skill 进行；加载入口本身不算完成检索。
- 知识仓通过项目配置定位，不把业务工程当成知识仓。实际覆盖由 Query 确认，目录占位、导航数量或
  搜索零命中都不证明技术能力是否存在。
- 消费流程保持只读：必要权限被拒绝、索引缺失或陈旧时停止并报告，不绕过检索、不临时重建索引，
  也不自动下载、编译或修改知识、源码、SDK 与全局环境。
- 已读证据足够回答当前问题时结束；出现新的领域证据缺口时定向重入。需要工程实验或贡献知识时，
  必须属于用户本次授权，不因为检索 Skill 提到验证方法就自动执行。

平台识别、草稿补搜、相关链接、来源路径、输出范围和复杂任务审计的具体规则只在对应 Skill 及其
按需参考中维护。本安装提示仅负责触发、路由和使用边界，不另定义检索步骤；用户明确要求不使用
知识库时遵从该要求。
EOF
  if [[ "$profile" == "contributor" ]]; then
    cat <<'EOF'

### 贡献者附加流程

1. 新增、更新、拆分、合并或升级知识前，先用 `knowledge-query` 查重并打开相邻卡，明确本次
   decision 是 create、update、merge、split、deprecate 还是 defer。
2. 通用新来源、官方 reference、增量同步和版本升级使用 `knowledge-ingest`；从固定源码提取完整
   Operator 卡时，全部可达节点不含 Cube/AIC 或 MIX_CV 使用 `ops-knowledge-vv-ingest`，否则使用
   `ops-knowledge-cv-ingest`。producer 一次只处理一个逻辑算子，只写任务指定的最终卡。
3. 生产后使用 `knowledge-lint` 检查目标卡及受影响导航，再运行全库检查。需要形成 Issue 材料
   时使用 Lint 内置的 issue-report 工作流，不新增独立 Skill，也不由 Lint 自动创建外部 Issue。
4. 知识和治理变更完成后，通过仓库统一质量入口重建并验证持久索引；不要手工编辑 SQLite
   产物。再次使用 Query 验证目标场景能够在正确 platform、technology 和 status 下召回。
5. 目录占位不代表知识覆盖。新增路径遵守仓库治理：五个 domain 根保持完整，只有 `ops` 和
   `model` 预建注册 route，其他领域由对应维护者随首张真实知识创建下一层目录。
EOF
  fi
}

manage_prompt() {
  local action="$1"
  local target="$2"
  local profile="$3"
  local prompt_tmp

  [[ ! -d "$target" ]] || fail "prompt path is a directory: $target"
  [[ ! -L "$target" ]] || fail "refusing to modify symlink prompt path: $target"
  prompt_tmp="$(mktemp)"
  generate_prompt "$profile" > "$prompt_tmp"
  if ! python3 - "$action" "$target" "$prompt_tmp" "$PROMPT_BEGIN" "$PROMPT_END" <<'PY'
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


action, target_value, prompt_value, begin_value, end_value = sys.argv[1:]
target = Path(target_value)
prompt = Path(prompt_value).read_bytes().rstrip(b"\r\n")
begin = begin_value.encode()
end = end_value.encode()
existing = target.read_bytes() if target.exists() else b""
managed = begin + b"\n" + prompt + b"\n" + end + b"\n"


def locate(data: bytes) -> tuple[int, int] | None:
    starts = []
    ends = []
    offset = 0
    for line in data.splitlines(keepends=True):
        value = line.rstrip(b"\r\n")
        if value == begin:
            starts.append((offset, offset + len(line)))
        if value == end:
            ends.append((offset, offset + len(line)))
        offset += len(line)
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) != 1 or starts[0][0] >= ends[0][0]:
        raise ValueError(
            f"malformed cannbot-knowledge prompt markers in {target} "
            f"(begin={len(starts)} end={len(ends)})"
        )
    return starts[0][0], ends[0][1]


def remove_block(data: bytes, start: int, finish: int) -> bytes:
    prefix = data[:start].rstrip(b"\r\n")
    suffix = data[finish:].lstrip(b"\r\n")
    if prefix and suffix:
        return prefix + b"\n" + suffix
    return prefix or suffix


try:
    current = locate(existing)
except ValueError as exc:
    print(f"error: {exc}", file=sys.stderr)
    raise SystemExit(2)

if action == "validate":
    raise SystemExit(0)
if action == "uninstall":
    updated = remove_block(existing, *current) if current else existing
    status = "uninstalled" if updated != existing else "already absent"
else:
    if current:
        start, finish = current
        updated = existing[:start] + managed + existing[finish:]
        status = "reinstalled"
    else:
        updated = existing.rstrip(b"\r\n")
        if updated:
            updated += b"\n\n"
        updated += managed
        status = "reinstalled" if action == "reinstall" else "installed"

if updated != existing:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=target.name + ".", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        try:
            Path(temporary).unlink()
        except FileNotFoundError:
            pass
print(f"Prompt {target}: {status}")
PY
  then
    rm -f "$prompt_tmp"
    return 1
  fi
  rm -f "$prompt_tmp"
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi
[[ "$#" -ge 2 ]] || { show_help >&2; exit 2; }

agent="$1"
project_input="$2"
shift 2
profile="consumer"
profile_explicit="false"
prompt_action=""
skip_resources="false"
if [[ "${1:-}" == "consumer" || "${1:-}" == "contributor" ]]; then
  profile="$1"
  profile_explicit="true"
  shift
fi
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --skip-resources)
      skip_resources="true"
      shift
      ;;
    --prompt-action)
      [[ "$#" -ge 2 ]] || fail "--prompt-action requires a value"
      prompt_action="$2"
      shift 2
      ;;
    --prompt-action=*)
      prompt_action="${1#--prompt-action=}"
      shift
      ;;
    --help|-h)
      show_help
      exit 0
      ;;
    *) fail "unknown option: $1" ;;
  esac
done

[[ -d "$project_input" ]] || fail "project path is not a directory: $project_input"
project_path="$(realpath "$project_input")"
case "$agent" in
  agents|codex)
    adapter_root=""
    prompt_file="$project_path/AGENTS.md"
    ;;
  claude)
    adapter_root="$project_path/.claude/skills"
    prompt_file="$project_path/CLAUDE.md"
    ;;
  opencode)
    adapter_root="$project_path/.opencode/skills"
    prompt_file="$project_path/AGENTS.md"
    ;;
  trae)
    adapter_root="$project_path/.trae/skills"
    prompt_file="$project_path/AGENTS.md"
    ;;
  cursor)
    adapter_root="$project_path/.cursor/skills"
    prompt_file="$project_path/AGENTS.md"
    ;;
  copilot)
    adapter_root="$project_path/.github/skills"
    prompt_file="$project_path/AGENTS.md"
    ;;
  *) fail "unknown agent: $agent" ;;
esac
case "$prompt_action" in
  ""|uninstall|reinstall) ;;
  *) fail "unknown prompt action: $prompt_action" ;;
esac

canonical_root="$project_path/.agents/skills"
knowledge_env="$project_path/.cannbot/knowledge.env"
if [[ "$prompt_action" == "reinstall" && "$profile_explicit" == "false" ]]; then
  profile="$(installed_profile "$knowledge_env" "$canonical_root")"
fi
case "$profile" in
  consumer) skills=(knowledge-query ascendc-api-knowledge-query) ;;
  contributor) skills=(knowledge-ingest knowledge-query knowledge-lint ascendc-api-knowledge-query ops-knowledge-vv-ingest ops-knowledge-cv-ingest) ;;
  *) fail "unknown profile: $profile" ;;
esac

if [[ "$prompt_action" == "uninstall" ]]; then
  manage_prompt uninstall "$prompt_file" "$profile" || fail "prompt uninstall failed"
  exit 0
fi
if [[ "$prompt_action" == "reinstall" ]]; then
  [[ -f "$project_path/.agents/skills/knowledge-query/SKILL.md" ]] || \
    fail "knowledge-query is not installed at $project_path/.agents/skills/knowledge-query"
  manage_prompt reinstall "$prompt_file" "$profile" || fail "prompt reinstall failed"
  exit 0
fi

[[ -d "$KNOWLEDGE_ROOT/knowledge" ]] || fail "invalid knowledge root: $KNOWLEDGE_ROOT"
[[ -f "$KNOWLEDGE_ROOT/governance/schemas/registries.yaml" ]] || \
  fail "invalid knowledge root: $KNOWLEDGE_ROOT"
[[ -f "$INDEX_TOOL" ]] || fail "missing index tool: $INDEX_TOOL"

if [[ -L "$knowledge_env" || ( -e "$knowledge_env" && ! -f "$knowledge_env" ) ]]; then
  fail "refusing to overwrite non-regular config path: $knowledge_env"
fi
[[ ! -d "$prompt_file" ]] || fail "prompt path is a directory: $prompt_file"
[[ ! -L "$prompt_file" ]] || fail "refusing to modify symlink prompt path: $prompt_file"
manage_prompt validate "$prompt_file" "$profile" || fail "prompt marker preflight failed"
for skill in "${skills[@]}"; do
  source_path="$KNOWLEDGE_ROOT/.agents/skills/$skill"
  canonical_path="$canonical_root/$skill"
  preflight_link "$source_path" "$canonical_path"
  if [[ -n "$adapter_root" ]]; then
    preflight_link "$canonical_path" "$adapter_root/$skill" true
  fi
done

if [[ "$skip_resources" != "true" ]]; then
  bash "$KNOWLEDGE_ROOT/get_resources.sh"
fi
prepare_search_index
for skill in "${skills[@]}"; do
  source_path="$KNOWLEDGE_ROOT/.agents/skills/$skill"
  canonical_path="$canonical_root/$skill"
  install_link "$source_path" "$canonical_path"
  if [[ -n "$adapter_root" ]]; then
    install_link "$canonical_path" "$adapter_root/$skill"
  fi
done
write_project_env "$knowledge_env" "$profile"
manage_prompt install "$prompt_file" "$profile" || fail "prompt install failed"

echo "Installed cannbot-knowledge $VERSION"
echo "  agent:          $agent"
echo "  profile:        $profile"
echo "  project:        $project_path"
echo "  canonical root: $canonical_root"
echo "  knowledge root: $KNOWLEDGE_ROOT"
