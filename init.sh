#!/usr/bin/env bash
set -euo pipefail

VERSION="0.4.2"
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
  consumer       Install knowledge-query only (default).
  contributor    Install knowledge-query, knowledge-ingest, and knowledge-lint.

Options:
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

`cannbot-knowledge` 把 CANN、昇腾 NPU、算子 DSL、图、模型和 Runtime 的受治理知识整理成
可检索、可溯源的知识卡。`knowledge-query` 是统一消费入口：它从经过校验的持久化索引返回
候选标题、摘要、平台、版本、信任信息和 `local_path`；有命中时负责当前任务的 Agent 必须打开
正文并按需核验固定来源，零命中时必须明确记录覆盖缺口，再用固定权威来源和当前工程证据推进。

### 入口硬门禁

- 以下规则约束负责整体任务的主 Agent。收到明确子任务的子 Agent 可直接使用主 Agent 提供的
  证据；只有子任务本身是知识检索，或出现阻塞子任务的新领域缺口时才调用 `knowledge-query`，
  否则把缺口和新事实返回主 Agent。
- 只要任务涉及 CANN、昇腾 NPU、算子生成或实现、Ascend C/Triton/TileLang/PyPTO、图编译、
  模型训练或推理、Runtime，以及相关 API 核验、调试、优化、测试、迁移、评审或技术问答，
  必须在首次领域决策前通过 Agent 的 Skill 能力加载 `knowledge-query`。调用了其他 Skill 也
  不能跳过或推迟这个入口。
- 加载 Query 前，只读取用户任务、任务规格和用于确定目标平台的设备信息。平台确定后，下一项
  领域动作应是加载 Query；首次完成检索前，不探索参考实现或工程源码，不创建设计文档、
  STATE 或任务清单，也不开始 API 选型、编码和调试。
- 只加载 Skill、只看候选摘要或只取得文件路径，都不算完成入口。有命中时至少打开与第一个
  decision 相关的 `local_path`，核对正文范围和 sources；零命中时保留查询条件并明确报告知识
  缺口，然后才转向固定权威来源或工程证据。
- Query 只消费已准备且未过期的索引。索引缺失或陈旧时停止检索，向用户或知识仓维护者报告，
  由项目安装器或维护流程构建；不得临时扫描全库、静默重建或取消过滤来绕过失败。
- 本段与项目内其他非用户级调用顺序冲突时，以本段为准；系统、开发者和用户明确指令仍然
  优先。只有用户明确要求不使用知识库时，才跳过该入口。

### 知识库中有什么

先用 Query 的 `discover` 区分真实卡片覆盖与 Registry、`index.md` 或预建目录表示的规划范围。
目录存在不等于其中已经有可检索知识。

| 领域或路径 | 当前含义 | 适合支持的决策 |
|---|---|---|
| `common` | 仅保留 domain 根，当前没有下层路径或知识卡 | 由 `discover` 确认空覆盖；不要假设存在平台、工具链或术语知识 |
| `ops` | 预建 `ascendc`、`triton`、`tilelang`、`pypto`、`shared` route，当前都没有知识卡或 Profile 目录 | 识别目标 DSL 和覆盖缺口；不要把结构入口或其他 DSL 当作证据 |
| `model` | 预建 `inference`、`training`、`shared` route，当前没有知识卡 | 区分模型场景并明确报告空覆盖 |
| `graph`、`runtime` | 仅保留 domain 根，下层路径随首张真实知识创建 | 没有卡片时选择固定权威来源或工程证据，不虚构知识库结论 |

知识卡是蒸馏后的入口，不是原始资料镜像。正文用于技术判断，显式 Markdown 链接组成可浏览的
关系，`sources` 指向固定版本的文档或代码。默认只消费 `stable`；draft、deprecated、未定位平台
内容以及 shared 追加都必须显式请求。没有 `verified` 不是已验证，machine-confirmed 也不等于
human-reviewed。零命中只表示当前过滤条件下未召回，不证明技术或能力不存在。

### 什么时候调用或重新调用

| 触发场景 | 本轮要查的重点 | 要支持的 decision |
|---|---|---|
| 新需求、算子、图、模型或 Runtime 任务 | 同名/相似知识、语义、平台和工程边界 | 明确输入输出、shape/dtype/layout、版本、失败边界和候选路线 |
| 只给出芯片型号、SocVersion 或 NPU 架构 | 平台识别参考、用户/设备事实和固定权威来源 | 得到可证明的目标平台；无法唯一映射时向用户确认 |
| 新增、替换或不确定 API | 目标 technology 的 API、概念、样例和固定来源 | 核验名称、签名、参数单位、内存位置、dtype、平台/版本与替代接口 |
| Kernel、Tiling、图优化或执行流程设计 | concepts、operators、examples、interoperability | 选择数据流、切分、内存、同步、模板或跨技术路线，并保留验证点 |
| 编译、链接、加载、运行、越界、卡死或超时 | 原始错误短语、runbook、相关 API 和平台约束 | 根据完整信号缩小声明、资源、地址、同步、切分或兼容性根因 |
| 精度或一致性失败 | 失败 workload、语义、数据搬运、累积精度和边界知识 | 区分公式、布局、搬运、数值精度和平台行为问题 |
| 性能优化 | 先取得基线或 Profiling 信号，再查优化、样例和硬件概念 | 把瓶颈映射为可测量的搬运、流水、内存、指令、并行或模板候选 |
| 版本、平台或 DSL 迁移 | 平台、版本、interoperability 和受影响 API | 识别弃用、替代、架构差异和不能跨环境照搬的实现 |
| 代码评审、测试设计或技术问答 | 与具体结论对应的语义、契约、平台和验证依据 | 判断结论是否有目标范围证据，并指出风险、缺口和验证方式 |

任务任一阶段出现新的 API 契约、实现分支、错误信号、精度现象、性能瓶颈、平台差异或用户约束
时，带着新增事实定向重入 `knowledge-query`。已有证据足以支持当前 decision 时结束本轮检索，
不要为了增加查询次数重复搜索。

### 每次执行的基本流程

1. 把当前任务拆成一个明确的知识问题和一个待决定的 decision，并取得目标平台证据。只有产品
   型号、SocVersion 或 NPU 架构时，按 Skill 的平台识别流程映射；不得凭记忆猜测，也不得通过
   省略 `--platform` 扩大搜索。
2. 先运行 `discover`，再按 domain、technology、路径 Profile、CANN 版本和 platform 使用最窄
   过滤条件。跨领域问题拆成独立查询，不把关键词相似的其他 DSL 自动作为证据。
3. 根据候选的标题、摘要、平台、版本、信任信息和路径选卡，并用原生文件工具打开相关
   `local_path`。摘要只用于选卡，未打开的链接和正文行数都不是技术结论；零命中时记录完整
   过滤条件和覆盖缺口，不虚构候选卡。
4. 正文足够时，提取公式、API 契约、适用范围、候选方案、风险和验证方法；正文不足时先沿
   显式关系或 `sources` 定向读取固定上游，再考虑已安装 SDK 或其他外部资料。
5. 区分硬约束和候选实现：语义、API 契约、平台/版本限制需要遵守；生产卡、样例和优化卡只是
   候选路线，不自动等于当前工程或 workload 的最优方案。
6. 回到工程任务，在目标平台执行构建、正确性、边界和必要的 Profiling 验证。工程结果产生新
   知识问题时重新查询，不能用任务开头的旧搜索替代。
7. 复杂实现、故障、性能、多 decision 或需要交接的任务，为每个 decision 保存独立且不可覆盖
   的 search receipt；按 Query 工作流冻结 state、生成 ready receipt，并在工程验证后校验
   outcome manifest。只针对未解决 gap 改变查询角度。

### 需要立即纠正的行为

| 错误行为 | 应执行的动作 |
|---|---|
| 准备先调用其他技术 Skill、读参考实现或写方案 | 只取得任务规格和平台事实，先加载 Query、搜索并打开相关卡 |
| 看到芯片型号或 NPU 架构后凭经验选择平台 | 打开平台识别参考；共享架构不能单独证明具体产品平台 |
| 查询时省略平台，或用 `--include-unlocated` 扩大普通搜索 | 恢复平台硬过滤；未定位 draft 只用于明确的受控研究 |
| 索引缺失或 stale 后改为遍历知识树 | 停止并报告，由安装器或维护者构建索引，不在查询路径静默修复 |
| 把候选摘要、标题或未打开链接当作结论 | 打开 `local_path`，核对正文和固定来源 |
| 任务开始查过一次，后续不再查 | 新 API、分支、失败证据、性能信号或平台信息出现时定向重入 |
| 因同名或算法相似使用其他平台、版本或 DSL 的卡 | 停止套用，按目标范围重新过滤；跨技术只使用显式 shared/interoperability 证据 |
| 有生产实现或样例就直接照搬 | 保留约束，将实现作为候选，与工程形态、workload 和测量结果比较 |
| 卡片没展开完整签名或源码就全盘搜索 SDK | 先沿卡片固定 source 定向核验缺失细节，并记录实际版本和路径 |
| 没有同名卡就宣称知识不存在 | 改查语义、关键 API、平台、Runbook 或相似机制，并明确零命中的边界 |

具体命令、输出 schema、过滤规则、平台识别和审计步骤以 `knowledge-query` 的 `SKILL.md` 及其
渐进式 references/modes 为准。
EOF
  if [[ "$profile" == "contributor" ]]; then
    cat <<'EOF'

### 贡献者附加流程

1. 新增、更新、拆分、合并或升级知识前，先用 `knowledge-query` 查重并打开相邻卡，明确本次
   decision 是 create、update、merge、split、deprecate 还是 defer。
2. 所有新来源、官方 reference、增量同步、版本升级和单卡生产都统一加载 `knowledge-ingest`
   路由；不要绕过入口直接调用尚未发布的 Ingest producer。Ingest 只生成或更新候选，不自动
   覆盖冲突内容，也不执行 commit、push、merge 或发布。
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
if [[ "${1:-}" == "consumer" || "${1:-}" == "contributor" ]]; then
  profile="$1"
  profile_explicit="true"
  shift
fi
while [[ "$#" -gt 0 ]]; do
  case "$1" in
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
  consumer) skills=(knowledge-query) ;;
  contributor) skills=(knowledge-ingest knowledge-query knowledge-lint) ;;
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
