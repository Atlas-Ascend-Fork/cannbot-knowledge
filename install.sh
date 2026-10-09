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

VERSION="0.5.1"
REPOSITORY_URL="${CANNBOT_KNOWLEDGE_REPOSITORY_URL:-https://gitcode.com/cann/cannbot-knowledge.git}"
REPOSITORY_REF="${CANNBOT_KNOWLEDGE_REPOSITORY_REF:-master}"
SCRIPT_SOURCE="${BASH_SOURCE[0]:-}"
SCRIPT_DIR=""
if [[ -n "$SCRIPT_SOURCE" && -f "$SCRIPT_SOURCE" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")" && pwd)"
fi
KNOWLEDGE_ROOT=""
INDEX_TOOL=""
PYTHON_BIN="${CANNBOT_PYTHON:-}"
PROMPT_BEGIN="<!-- cannbot-knowledge:start -->"
PROMPT_END="<!-- cannbot-knowledge:end -->"
ALL_INSTALLABLE_SKILLS=(
  knowledge-ingest
  knowledge-query
  knowledge-lint
  ascendc-api-knowledge-query
  ops-knowledge-vv-ingest
  ops-knowledge-cv-ingest
)
managed_skill_removal_paths=()
managed_skill_removal_targets=()

show_help() {
  cat <<'EOF'
cannbot-knowledge project installer

Usage:
  bash install.sh <codex|claude|opencode|trae|cursor|copilot> \
    <project-path> [consumer|contributor] [options]

Installation modes:
  consumer       Install knowledge-query and ascendc-api-knowledge-query (default).
  contributor    Install the three base skills, ascendc-api-knowledge-query and both operator ingest skills.
                 The repository-internal trace ingest skill is not installed.

Options:
  --knowledge-root <path>
                  Clone or update the knowledge repository at this path. When
                  omitted, a local checkout containing this script is reused;
                  standalone/remote execution uses ~/.cannbot/cannbot-knowledge.
  --repository-url <url>
                  Override the repository URL used for a managed clone.
  --repository-ref <branch>
                  Override the branch used for a managed clone (default: master).
  --platform <platform>
                  Set the default platform used by knowledge-query when a search
                  omits --platform. Explicit search arguments still take precedence.
  --skip-repository-update
                  Reuse an existing --knowledge-root without fetching it. The
                  path must already be a valid knowledge repository.
  --skip-resources
                  Skip restoring local documentation and pinned source snapshots.
                  Use only for an explicitly offline, knowledge-only installation.
  --prompt-action <uninstall|reinstall>
                  Only remove or refresh the managed project instructions. Reinstall
                  reuses the mode recorded by the previous installation unless a
                  mode is explicitly provided.
  --help          Show this help message.

Standalone execution clones the repository or fast-forwards an existing managed
clone before restoring resources. The installer then creates canonical links under
.agents/skills; agent-specific directories contain adapter links to those entries.
The knowledge root is written to .cannbot/knowledge.env; no shell startup file is
changed. Missing Python runtime packages are installed from requirements.txt with
the selected interpreter's pip; other configuration is not changed.
EOF
}

fail() {
  echo "$1" >&2
  exit 2
}

preflight_destination() {
  "$PYTHON_BIN" - "$project_path" "$1" <<'PY'
import sys
from pathlib import Path

root, target = map(Path, sys.argv[1:])
try:
    # Existing leaf links are checked separately against their intended source.
    if not target.parent.resolve().is_relative_to(root):
        raise ValueError(f"destination parent leaves project: {target}")
    parent = target.parent
    while parent != root:
        if (parent.exists() or parent.is_symlink()) and not parent.is_dir():
            raise ValueError(f"destination parent is not a directory: {parent}")
        parent = parent.parent
except (OSError, RuntimeError, ValueError) as exc:
    print(f"error: {exc}", file=sys.stderr)
    raise SystemExit(2)
PY
}

select_python() {
  if [[ -z "$PYTHON_BIN" ]]; then
    if command -v python3 >/dev/null 2>&1; then
      PYTHON_BIN="$(command -v python3)"
    else
      fail "Python 3.10 or newer must be available as python3"
    fi
  fi
  command -v "$PYTHON_BIN" >/dev/null 2>&1 || \
    fail "configured Python interpreter is not executable: $PYTHON_BIN"
  "$PYTHON_BIN" - <<'PY' || fail "Python 3.10 or newer is required"
import sys

raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
}

canonical_path() {
  "$PYTHON_BIN" - "$1" <<'PY'
import sys
from pathlib import Path

print(Path(sys.argv[1]).expanduser().resolve(strict=False))
PY
}

is_knowledge_root() {
  local root="$1"
  [[ -d "$root/knowledge" && \
     -f "$root/governance/schemas/registries.yaml" && \
     -f "$root/.agents/skills/knowledge-query/scripts/knowledge_index.py" ]]
}

normalized_repository_url() {
  local value="${1%/}"
  printf '%s\n' "${value%.git}"
}

prepare_managed_repository() {
  local requested_root="$1"
  local skip_update="$2"
  local parent
  local actual_url
  local current_branch
  local current_revision
  local target_revision

  command -v git >/dev/null 2>&1 || fail "git is required to acquire the knowledge repository"
  git check-ref-format --branch "$REPOSITORY_REF" >/dev/null 2>&1 || \
    fail "invalid repository branch: $REPOSITORY_REF"
  [[ ! -L "$requested_root" ]] || fail "refusing to use a symlink knowledge root: $requested_root"

  if [[ ! -e "$requested_root" ]]; then
    [[ "$skip_update" != "true" ]] || \
      fail "knowledge root does not exist while repository update is disabled: $requested_root"
    parent="$(dirname "$requested_root")"
    mkdir -p "$parent"
    echo "Cloning cannbot-knowledge into $requested_root ..."
    git clone --branch "$REPOSITORY_REF" --single-branch -- \
      "$REPOSITORY_URL" "$requested_root"
  else
    [[ -d "$requested_root" ]] || fail "knowledge root is not a directory: $requested_root"
    git -C "$requested_root" rev-parse --is-inside-work-tree >/dev/null 2>&1 || \
      fail "existing knowledge root is not a Git checkout: $requested_root"
    if [[ "$skip_update" != "true" ]]; then
      actual_url="$(git -C "$requested_root" remote get-url origin 2>/dev/null || true)"
      [[ -n "$actual_url" ]] || fail "knowledge repository has no origin remote: $requested_root"
      if [[ "$(normalized_repository_url "$actual_url")" != \
            "$(normalized_repository_url "$REPOSITORY_URL")" ]]; then
        fail "knowledge repository origin mismatch: expected $REPOSITORY_URL, got $actual_url"
      fi
      current_branch="$(git -C "$requested_root" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
      [[ "$current_branch" == "$REPOSITORY_REF" ]] || \
        fail "knowledge repository branch mismatch: expected $REPOSITORY_REF, got ${current_branch:-detached HEAD}"
      [[ -z "$(git -C "$requested_root" status --porcelain --untracked-files=no)" ]] || \
        fail "refusing to update a knowledge repository with tracked local changes: $requested_root"
      echo "Updating cannbot-knowledge in $requested_root ..."
      git -C "$requested_root" fetch origin \
        "refs/heads/$REPOSITORY_REF:refs/remotes/origin/$REPOSITORY_REF"
      current_revision="$(git -C "$requested_root" rev-parse HEAD)"
      target_revision="$(git -C "$requested_root" rev-parse "refs/remotes/origin/$REPOSITORY_REF")"
      if [[ "$current_revision" != "$target_revision" ]]; then
        git -C "$requested_root" merge-base --is-ancestor \
          "$current_revision" "$target_revision" || \
          fail "managed knowledge repository cannot be fast-forwarded to origin/$REPOSITORY_REF"
        git -C "$requested_root" merge --ff-only "$target_revision"
      fi
    fi
  fi

  is_knowledge_root "$requested_root" || fail "invalid knowledge root: $requested_root"
  KNOWLEDGE_ROOT="$(canonical_path "$requested_root")"
}

resolve_knowledge_root() {
  local requested_root="$1"
  local root_explicit="$2"
  local skip_update="$3"

  if [[ "$root_explicit" != "true" && -n "$SCRIPT_DIR" ]] && \
      is_knowledge_root "$SCRIPT_DIR"; then
    KNOWLEDGE_ROOT="$(canonical_path "$SCRIPT_DIR")"
    echo "Using local knowledge checkout: $KNOWLEDGE_ROOT"
  else
    if [[ -z "$requested_root" ]]; then
      [[ -n "${HOME:-}" ]] || \
        fail "HOME is not set; provide --knowledge-root for the managed repository"
      requested_root="$HOME/.cannbot/cannbot-knowledge"
    fi
    prepare_managed_repository "$requested_root" "$skip_update"
  fi
  INDEX_TOOL="$KNOWLEDGE_ROOT/.agents/skills/knowledge-query/scripts/knowledge_index.py"
}

runtime_is_ready() {
  "$PYTHON_BIN" - >/dev/null 2>&1 <<'PY'
import yaml  # noqa: F401
import sys

def release(value: str) -> tuple[int, ...]:
    parts = []
    for part in value.split("."):
        digits = "".join(character for character in part if character.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


if not (release(yaml.__version__) >= (6, 0) and release(yaml.__version__) < (7,)):
    raise SystemExit(1)
if sys.version_info < (3, 11):
    import tomli

    if not (release(tomli.__version__) >= (2, 0) and release(tomli.__version__) < (3,)):
        raise SystemExit(1)
PY
}

check_runtime() {
  [[ -f "$KNOWLEDGE_ROOT/requirements.txt" ]] || \
    fail "missing runtime dependency manifest: $KNOWLEDGE_ROOT/requirements.txt"
  if runtime_is_ready; then
    return 0
  fi
  "$PYTHON_BIN" -m pip --version >/dev/null 2>&1 || \
    fail "Python runtime dependencies are missing and pip is unavailable for $PYTHON_BIN"
  echo "Installing Python runtime dependencies..."
  "$PYTHON_BIN" -m pip install -r "$KNOWLEDGE_ROOT/requirements.txt" || \
    fail "failed to install Python runtime dependencies from $KNOWLEDGE_ROOT/requirements.txt"
  if ! runtime_is_ready; then
    fail "Python runtime dependencies are still unavailable after installation"
  fi
}

link_matches() {
  local destination="$1"
  local expected="$2"
  [[ -L "$destination" ]] || return 1
  [[ "$(canonical_path "$destination" 2>/dev/null || true)" == \
     "$(canonical_path "$expected" 2>/dev/null || true)" ]]
}

preflight_link() {
  local source="$1"
  local destination="$2"
  local source_may_be_pending="${3:-false}"
  preflight_destination "$destination"
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
  if "$PYTHON_BIN" "$INDEX_TOOL" --knowledge-root "$KNOWLEDGE_ROOT" \
      verify --level quick >/dev/null 2>&1; then
    return 0
  fi
  echo "Preparing knowledge search index..."
  "$PYTHON_BIN" "$INDEX_TOOL" --knowledge-root "$KNOWLEDGE_ROOT" build >/dev/null
}

skill_is_selected() {
  local expected="$1"
  local selected
  for selected in "${skills[@]}"; do
    [[ "$selected" == "$expected" ]] && return 0
  done
  return 1
}

plan_unselected_managed_skills() {
  local skill
  local source_path
  local canonical_path_value
  local adapter
  local adapter_path

  managed_skill_removal_paths=()
  managed_skill_removal_targets=()
  for skill in "${ALL_INSTALLABLE_SKILLS[@]}"; do
    skill_is_selected "$skill" && continue
    source_path="$KNOWLEDGE_ROOT/.agents/skills/$skill"
    canonical_path_value="$canonical_root/$skill"
    # An adapter is managed only when its canonical link belongs to this
    # knowledge checkout. User directories and links to other sources are left
    # untouched, together with every adapter that points to them.
    link_matches "$canonical_path_value" "$source_path" || continue
    for adapter in "${all_adapter_roots[@]}"; do
      adapter_path="$adapter/$skill"
      if link_matches "$adapter_path" "$canonical_path_value"; then
        managed_skill_removal_paths+=("$adapter_path")
        managed_skill_removal_targets+=("$canonical_path_value")
      fi
    done
    managed_skill_removal_paths+=("$canonical_path_value")
    managed_skill_removal_targets+=("$source_path")
  done
}

preflight_managed_skill_removals() {
  local index
  local path
  local expected

  [[ "${#managed_skill_removal_paths[@]}" -eq \
     "${#managed_skill_removal_targets[@]}" ]] || \
    fail "internal error: incomplete managed Skill removal plan"
  for index in "${!managed_skill_removal_paths[@]}"; do
    path="${managed_skill_removal_paths[$index]}"
    expected="${managed_skill_removal_targets[$index]}"
    preflight_destination "$path"
    link_matches "$path" "$expected" || \
      fail "managed Skill link changed during cleanup preflight: $path"
  done
}

remove_unselected_managed_skills() {
  local path

  for path in "${managed_skill_removal_paths[@]}"; do
    rm -- "$path"
  done
}

write_project_env() {
  local target="$1"
  local profile="$2"
  local platform="${3:-}"
  local tmp
  local root_replacement
  local profile_replacement
  local platform_replacement=""
  local line
  local trimmed
  local root_found=0
  local profile_found=0
  local platform_found=0

  if [[ -L "$target" || ( -e "$target" && ! -f "$target" ) ]]; then
    fail "refusing to overwrite non-regular config path: $target"
  fi
  mkdir -p "$(dirname "$target")"
  tmp="$(mktemp "${target}.tmp.XXXXXX")"
  printf -v root_replacement 'export CANNBOT_KNOWLEDGE_ROOT=%q' "$KNOWLEDGE_ROOT"
  printf -v profile_replacement 'export CANNBOT_KNOWLEDGE_PROFILE=%q' "$profile"
  if [[ -n "$platform" ]]; then
    printf -v platform_replacement 'export CANNBOT_KNOWLEDGE_PLATFORM=%q' "$platform"
  fi
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
      elif [[ "$trimmed" =~ ^(export[[:space:]]+)?CANNBOT_KNOWLEDGE_PLATFORM= ]]; then
        if [[ -n "$platform" && "$platform_found" -eq 0 ]]; then
          printf '%s\n' "$platform_replacement" >> "$tmp"
          platform_found=1
        elif [[ "$platform_found" -eq 0 ]]; then
          printf '%s\n' "$line" >> "$tmp"
          platform_found=1
        fi
      else
        printf '%s\n' "$line" >> "$tmp"
      fi
    done < "$target"
  fi
  [[ "$root_found" -eq 1 ]] || printf '%s\n' "$root_replacement" >> "$tmp"
  [[ "$profile_found" -eq 1 ]] || printf '%s\n' "$profile_replacement" >> "$tmp"
  if [[ -n "$platform" && "$platform_found" -eq 0 ]]; then
    printf '%s\n' "$platform_replacement" >> "$tmp"
  fi
  if [[ -f "$target" ]]; then
    "$PYTHON_BIN" - "$target" "$tmp" <<'PY'
import os
import stat
import sys

os.chmod(sys.argv[2], stat.S_IMODE(os.stat(sys.argv[1]).st_mode))
PY
  fi
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
  local knowledge_root="$2"
  cat <<'EOF'
## cannbot-knowledge 使用入口

本项目已安装可检索、可溯源的 CANN 知识库。若安装时配置了 `--platform <id>`，该值会写入
`.cannbot/knowledge.env` 的 `CANNBOT_KNOWLEDGE_PLATFORM`，普通检索省略 `--platform` 时使用它；
任务目标与该值不一致时显式传入目标平台。先按问题是否已经绑定唯一知识卡选择入口：

| 当前问题 | 入口 |
|---|---|
EOF
  printf '| 用户给出了确定、唯一的知识卡路径，且问题只需要该卡内容 | 直接阅读全文，例如 `%s/knowledge/common/platforms/concepts/ascend_910_95.md` |\n' \
    "$knowledge_root"
  cat <<'EOF'
| Ascend C API 的契约、选型、相关知识或本地头文件 | `.agents/skills/ascendc-api-knowledge-query/SKILL.md` |
| 未知卡片路径、需要多卡综合，或涉及算子实现、调试、优化、测试与跨技术问题 | `.agents/skills/knowledge-query/SKILL.md` |

直接读卡不需要先运行检索；必须读取完整 Frontmatter 和正文，并核对平台、版本、状态与来源。如果
该卡不足以回答问题，再按新增的证据缺口进入对应 Skill。两个检索入口共用 Query 的索引和平台规则，
不需要重复启动。缺少入口时由项目安装流程补齐，不扫描知识树替代 Skill。

### 使用边界

- 没有明确单卡路径时，在 CANN、昇腾 NPU、算子 DSL、图、模型或 Runtime 的首次领域决策前进入
  对应检索 Skill。目标平台确认、候选召回、选卡全文阅读及按需补证依照所选 Skill 进行；加载入口
  本身不算完成检索。
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
5. 目录占位不代表知识覆盖。新增路径遵守仓库治理：所有注册的 domain 根保持完整，只有 `ops` 和
   `model` 预建注册 route，其他领域由对应维护者随首张真实知识创建下一层目录。
EOF
  fi
}

manage_prompt() {
  local action="$1"
  local target="$2"
  local profile="$3"
  local target_kind="$4"
  local knowledge_root="${5:-}"
  local prompt_tmp=""
  local prompt_status

  if [[ "$action" != "detect" ]]; then
    preflight_destination "$target"
    [[ ! -d "$target" ]] || fail "prompt path is a directory: $target"
    [[ ! -L "$target" ]] || fail "refusing to modify symlink prompt path: $target"
    prompt_tmp="$(mktemp)"
    generate_prompt "$profile" "$knowledge_root" > "$prompt_tmp"
  fi
  if "$PYTHON_BIN" - "$action" "$target" "$prompt_tmp" "$PROMPT_BEGIN" "$PROMPT_END" "$target_kind" <<'PY'
from __future__ import annotations

import os
import stat
import sys
import tempfile
from pathlib import Path


action, target_value, prompt_value, begin_value, end_value, target_kind = sys.argv[1:]
target = Path(target_value)
prompt = Path(prompt_value).read_bytes().rstrip(b"\r\n") if prompt_value else b""
begin = begin_value.encode()
end = end_value.encode()
try:
    existing = target.read_bytes() if target.exists() else b""
except OSError as exc:
    print(f"error: cannot read prompt file {target}: {exc}", file=sys.stderr)
    raise SystemExit(2)
original_existing = existing
managed = begin + b"\n" + prompt + b"\n" + end + b"\n"
trae_preamble = b"---\nalwaysApply: true\n---\n"


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

if action == "detect":
    raise SystemExit(0 if current is not None else 1)

def trae_frontmatter_is_always(data: bytes) -> bool:
    lines = data.splitlines()
    if not lines or lines[0].strip() != b"---":
        return False
    try:
        finish = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == b"---")
    except StopIteration:
        return False
    return any(line.strip() == b"alwaysApply: true" for line in lines[1:finish])


if action == "validate":
    if target_kind == "trae-rule" and existing and not trae_frontmatter_is_always(existing):
        if current is None or existing.lstrip().startswith(b"---"):
            print(
                f"error: existing TRAE rule must contain 'alwaysApply: true' frontmatter: {target}",
                file=sys.stderr,
            )
            raise SystemExit(2)
    raise SystemExit(0)
if action == "uninstall":
    updated = remove_block(existing, *current) if current else existing
    status = "uninstalled" if updated != existing else "already absent"
else:
    if target_kind == "trae-rule" and not trae_frontmatter_is_always(existing):
        existing = trae_preamble + (b"\n" + existing.lstrip(b"\r\n") if existing else b"")
        current = locate(existing)
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

if updated != original_existing:
    mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o644
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=target.name + ".", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, target)
    finally:
        try:
            Path(temporary).unlink()
        except FileNotFoundError:
            pass
print(f"Prompt {target}: {status}")
PY
  then
    prompt_status=0
  else
    prompt_status=$?
  fi
  [[ -z "$prompt_tmp" ]] || rm -f "$prompt_tmp"
  return "$prompt_status"
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
knowledge_platform_input="${CANNBOT_KNOWLEDGE_PLATFORM:-}"
knowledge_platform_explicit="false"
knowledge_root_input="${CANNBOT_KNOWLEDGE_INSTALL_ROOT:-}"
knowledge_root_explicit="false"
skip_repository_update="false"
if [[ -n "$knowledge_root_input" ]]; then
  knowledge_root_explicit="true"
fi
if [[ "${1:-}" == "consumer" || "${1:-}" == "contributor" ]]; then
  profile="$1"
  profile_explicit="true"
  shift
fi
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --knowledge-root)
      [[ "$#" -ge 2 ]] || fail "--knowledge-root requires a value"
      knowledge_root_input="$2"
      knowledge_root_explicit="true"
      shift 2
      ;;
    --knowledge-root=*)
      knowledge_root_input="${1#--knowledge-root=}"
      knowledge_root_explicit="true"
      shift
      ;;
    --repository-url)
      [[ "$#" -ge 2 ]] || fail "--repository-url requires a value"
      REPOSITORY_URL="$2"
      shift 2
      ;;
    --repository-url=*)
      REPOSITORY_URL="${1#--repository-url=}"
      shift
      ;;
    --repository-ref)
      [[ "$#" -ge 2 ]] || fail "--repository-ref requires a value"
      REPOSITORY_REF="$2"
      shift 2
      ;;
    --repository-ref=*)
      REPOSITORY_REF="${1#--repository-ref=}"
      shift
      ;;
    --platform)
      [[ "$#" -ge 2 ]] || fail "--platform requires a value"
      knowledge_platform_input="$2"
      knowledge_platform_explicit="true"
      shift 2
      ;;
    --platform=*)
      knowledge_platform_input="${1#--platform=}"
      knowledge_platform_explicit="true"
      shift
      ;;
    --skip-repository-update)
      skip_repository_update="true"
      shift
      ;;
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

[[ -n "$REPOSITORY_URL" ]] || fail "repository URL cannot be empty"
if [[ "$knowledge_platform_explicit" == "true" && -z "$knowledge_platform_input" ]]; then
  fail "--platform requires a non-empty value"
fi
if [[ -n "$knowledge_platform_input" && "$knowledge_platform_input" =~ [[:space:]] ]]; then
  fail "platform must be a single registered platform id"
fi
if [[ "$knowledge_root_explicit" == "true" ]]; then
  [[ -n "$knowledge_root_input" ]] || fail "knowledge root cannot be empty"
fi

[[ -d "$project_input" ]] || fail "project path is not a directory: $project_input"
select_python
project_path="$(canonical_path "$project_input")"
case "$agent" in
  codex)
    adapter_root=""
    prompt_file="$project_path/AGENTS.md"
    prompt_kind="markdown"
    ;;
  claude)
    adapter_root="$project_path/.claude/skills"
    prompt_file="$project_path/CLAUDE.md"
    prompt_kind="markdown"
    ;;
  opencode)
    adapter_root="$project_path/.opencode/skills"
    prompt_file="$project_path/AGENTS.md"
    prompt_kind="markdown"
    ;;
  trae)
    adapter_root="$project_path/.trae/skills"
    prompt_file="$project_path/.trae/rules/cannbot-knowledge.md"
    prompt_kind="trae-rule"
    ;;
  cursor)
    adapter_root="$project_path/.cursor/skills"
    prompt_file="$project_path/AGENTS.md"
    prompt_kind="markdown"
    ;;
  copilot)
    adapter_root="$project_path/.github/skills"
    prompt_file="$project_path/.github/copilot-instructions.md"
    prompt_kind="markdown"
    ;;
  *) fail "unknown agent: $agent" ;;
esac
case "$prompt_action" in
  ""|uninstall|reinstall) ;;
  *) fail "unknown prompt action: $prompt_action" ;;
esac

canonical_root="$project_path/.agents/skills"
knowledge_env="$project_path/.cannbot/knowledge.env"
all_adapter_roots=(
  "$project_path/.claude/skills"
  "$project_path/.opencode/skills"
  "$project_path/.trae/skills"
  "$project_path/.cursor/skills"
  "$project_path/.github/skills"
)
managed_prompt_files=(
  "$project_path/AGENTS.md"
  "$project_path/CLAUDE.md"
  "$project_path/.trae/rules/cannbot-knowledge.md"
  "$project_path/.github/copilot-instructions.md"
)
managed_prompt_kinds=(markdown markdown trae-rule markdown)

prompt_has_managed_marker() {
  local target="$1"
  local target_kind="$2"
  local status

  [[ -f "$target" ]] || return 1
  if manage_prompt detect "$target" "$profile" "$target_kind"; then
    return 0
  else
    status=$?
  fi
  [[ "$status" -eq 1 ]] && return 1
  fail "cannot inspect managed prompt markers: $target"
}

if [[ "$prompt_action" == "reinstall" && "$profile_explicit" == "false" ]]; then
  profile="$(installed_profile "$knowledge_env" "$canonical_root")"
fi
case "$profile" in
  consumer) skills=(knowledge-query ascendc-api-knowledge-query) ;;
  contributor) skills=(knowledge-ingest knowledge-query knowledge-lint ascendc-api-knowledge-query ops-knowledge-vv-ingest ops-knowledge-cv-ingest) ;;
  *) fail "unknown installation mode: $profile" ;;
esac

if [[ "$prompt_action" == "uninstall" ]]; then
  manage_prompt uninstall "$prompt_file" "$profile" "$prompt_kind" || fail "prompt uninstall failed"
  exit 0
fi
if [[ "$prompt_action" == "reinstall" ]]; then
  [[ -f "$project_path/.agents/skills/knowledge-query/SKILL.md" ]] || \
    fail "knowledge-query is not installed at $project_path/.agents/skills/knowledge-query"
  prompt_knowledge_root="$("$PYTHON_BIN" - "$knowledge_env" <<'PY'
import shlex
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit(2)
for raw in path.read_text(encoding="utf-8").splitlines():
    try:
        tokens = shlex.split(raw, comments=True, posix=True)
    except ValueError:
        continue
    if tokens and tokens[0] == "export":
        tokens = tokens[1:]
    for token in tokens:
        if token.startswith("CANNBOT_KNOWLEDGE_ROOT="):
            print(Path(token.split("=", 1)[1]).expanduser().resolve(strict=False))
            raise SystemExit(0)
raise SystemExit(2)
PY
)" || fail "cannot resolve the installed knowledge root from $knowledge_env"
  is_knowledge_root "$prompt_knowledge_root" || \
    fail "invalid installed knowledge root: $prompt_knowledge_root"
  manage_prompt reinstall "$prompt_file" "$profile" "$prompt_kind" "$prompt_knowledge_root" || \
    fail "prompt reinstall failed"
  exit 0
fi

resolve_knowledge_root \
  "$knowledge_root_input" "$knowledge_root_explicit" "$skip_repository_update"
check_runtime
preflight_destination "$knowledge_env"
[[ -d "$KNOWLEDGE_ROOT/knowledge" ]] || fail "invalid knowledge root: $KNOWLEDGE_ROOT"
[[ -f "$KNOWLEDGE_ROOT/governance/schemas/registries.yaml" ]] || \
  fail "invalid knowledge root: $KNOWLEDGE_ROOT"
[[ -f "$INDEX_TOOL" ]] || fail "missing index tool: $INDEX_TOOL"
if [[ -n "$knowledge_platform_input" ]] && ! "$PYTHON_BIN" - \
    "$KNOWLEDGE_ROOT/governance/schemas/registries.yaml" "$knowledge_platform_input" <<'PY'
import sys
from pathlib import Path

import yaml

registries = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
platforms = registries.get("platforms") if isinstance(registries, dict) else None
if not isinstance(platforms, dict) or sys.argv[2] not in platforms:
    raise SystemExit(1)
PY
then
  fail "unknown platform: $knowledge_platform_input"
fi

if [[ -L "$knowledge_env" || ( -e "$knowledge_env" && ! -f "$knowledge_env" ) ]]; then
  fail "refusing to overwrite non-regular config path: $knowledge_env"
fi
[[ ! -d "$prompt_file" ]] || fail "prompt path is a directory: $prompt_file"
[[ ! -L "$prompt_file" ]] || fail "refusing to modify symlink prompt path: $prompt_file"
manage_prompt validate "$prompt_file" "$profile" "$prompt_kind" "$KNOWLEDGE_ROOT" || \
  fail "prompt marker preflight failed"
for prompt_index in "${!managed_prompt_files[@]}"; do
  managed_prompt_file="${managed_prompt_files[$prompt_index]}"
  [[ "$managed_prompt_file" != "$prompt_file" ]] || continue
  if prompt_has_managed_marker "$managed_prompt_file" \
      "${managed_prompt_kinds[$prompt_index]}"; then
    manage_prompt validate "$managed_prompt_file" "$profile" \
      "${managed_prompt_kinds[$prompt_index]}" "$KNOWLEDGE_ROOT" || \
      fail "managed prompt preflight failed: $managed_prompt_file"
  fi
done
for skill in "${skills[@]}"; do
  source_path="$KNOWLEDGE_ROOT/.agents/skills/$skill"
  canonical_path="$canonical_root/$skill"
  preflight_link "$source_path" "$canonical_path"
  if [[ -n "$adapter_root" ]]; then
    preflight_link "$canonical_path" "$adapter_root/$skill" true
  fi
done
plan_unselected_managed_skills
preflight_managed_skill_removals

if [[ "$skip_resources" != "true" ]]; then
  CANNBOT_PYTHON="$PYTHON_BIN" bash "$KNOWLEDGE_ROOT/get_resources.sh"
fi
prepare_search_index
preflight_managed_skill_removals
remove_unselected_managed_skills
for skill in "${skills[@]}"; do
  source_path="$KNOWLEDGE_ROOT/.agents/skills/$skill"
  canonical_path="$canonical_root/$skill"
  install_link "$source_path" "$canonical_path"
  if [[ -n "$adapter_root" ]]; then
    install_link "$canonical_path" "$adapter_root/$skill"
  fi
done
write_project_env "$knowledge_env" "$profile" "$knowledge_platform_input"
manage_prompt install "$prompt_file" "$profile" "$prompt_kind" "$KNOWLEDGE_ROOT" || \
  fail "prompt install failed"

for prompt_index in "${!managed_prompt_files[@]}"; do
  managed_prompt_file="${managed_prompt_files[$prompt_index]}"
  [[ "$managed_prompt_file" != "$prompt_file" ]] || continue
  if prompt_has_managed_marker "$managed_prompt_file" \
      "${managed_prompt_kinds[$prompt_index]}"; then
    manage_prompt reinstall "$managed_prompt_file" "$profile" \
      "${managed_prompt_kinds[$prompt_index]}" "$KNOWLEDGE_ROOT" || \
      fail "prompt synchronization failed: $managed_prompt_file"
  fi
done

echo "Installed cannbot-knowledge $VERSION"
echo "  agent:          $agent"
echo "  mode:           $profile"
echo "  project:        $project_path"
echo "  canonical root: $canonical_root"
echo "  knowledge root: $KNOWLEDGE_ROOT"
echo "  project config: $knowledge_env"
echo "For direct shell access, run: source $knowledge_env"
