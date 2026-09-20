# 安装与使用 cannbot-knowledge

`install.sh` 是 cannbot-knowledge 的统一安装入口。首次使用按“安装 → 确认位置 → 验证并查询”完成；已有安装可直接查看[高级安装选项](#高级安装选项)、[更新与移除](#更新与移除)或[常见问题](#常见问题)。

## 安装

### 前置条件

- Bash、Python 3.10 或更高版本、Git 和 `mktemp`；默认资源恢复还需要 `curl`、`tar` 与网络；
- 安装器默认使用 `python3`，自定义解释器见 [Python 环境](#python-环境)；运行依赖缺失时，所选 Python 需要提供 `pip`，安装器会自动按 `requirements.txt` 安装运行依赖；
- 已存在的目标项目目录，以及支持符号链接的目标文件系统。

下面统一以 Claude Code 和 `consumer` 查询模式为例。将 `/path/to/project` 替换为实际业务项目目录；安装器不会创建这个目录。其他客户端只需替换 `claude`，对应标识见[客户端与安装产物](#客户端与安装产物)。

### 在线安装

```bash
bash -c '
set -euo pipefail
installer_file=$(mktemp)
trap "rm -f \"$installer_file\"" EXIT
curl -fsSL https://raw.gitcode.com/cann/cannbot-knowledge/raw/master/install.sh \
  -o "$installer_file"
bash "$installer_file" "$@"
' -- claude /path/to/project consumer
```

命令先完整下载脚本，再交给 Bash 执行；下载失败会直接返回非零状态。安装器默认取得官方知识仓，补齐 Python 依赖，运行 `get_resources.sh` 恢复文档归档与固定提交源码，再准备检索索引和项目配置。首次安装会下载知识仓之外的资源，也可能安装 Python 包，需要保持网络可用。

无法访问 `raw.gitcode.com` 时，使用下方本地安装方式。需要指定安装位置、仓库或分支时，见[高级安装选项](#高级安装选项)。

### 本地安装

先克隆知识仓，再从仓内执行安装器：

```bash
git clone --branch master https://gitcode.com/cann/cannbot-knowledge.git
cd cannbot-knowledge
bash install.sh claude /path/to/project consumer
```

已经取得仓库时，在该仓库根目录执行最后一条命令即可。未显式指定其他知识仓位置时，安装器复用这个 checkout，不自动切换或更新分支。本地执行仍默认补齐依赖和恢复资源；断网环境需按[离线安装](#离线安装)准备。

## 安装位置与产物

### 知识仓放在哪里

知识仓目录保存完整仓库、知识卡、来源资源和检索索引；目标项目是使用这些知识的业务工程。安装器按下表从上到下选择知识仓位置，命中一项即停止：

| 优先级 | 条件 | 使用的位置 |
|---|---|---|
| 1 | 传入 `--knowledge-root <路径>` | 参数指定的目录 |
| 2 | 设置非空 `CANNBOT_KNOWLEDGE_INSTALL_ROOT` | 环境变量指定的目录 |
| 3 | 从完整知识仓中的 `install.sh` 执行 | 该脚本所在的知识仓根目录 |
| 4 | 远程执行或单独下载脚本执行 | `$HOME/.cannbot/cannbot-knowledge`，即 `~/.cannbot/cannbot-knowledge` |

显式指定位置或使用远程默认位置时，安装器会克隆缺失的仓库，或对已有仓库做快进更新。已有仓库必须来源匹配、当前分支正确、已跟踪文件无本地修改且可以快进；离线复用见下文。

`CANNBOT_KNOWLEDGE_INSTALL_ROOT` 用于选择安装位置；安装器解析后的路径写入项目配置中的 `CANNBOT_KNOWLEDGE_ROOT`，供查询使用。这两个变量用途不同。

### 客户端与安装产物

所有客户端都会在目标项目中生成以下内容：

| 项目内路径 | 用途 |
|---|---|
| `.cannbot/knowledge.env` | 保存知识仓绝对路径和安装模式 |
| `.agents/skills/<skill>` | 指向知识仓中对应 Skill 的符号链接 |
| 下表中的客户端使用入口 | 写入带标记、可重复安装和移除的知识库使用说明 |

将安装命令中的 `claude` 换成对应标识即可。这个参数只选择目录与使用入口的适配方式，不会启动客户端。

| 客户端标识 | 项目内 Skill 入口 | 项目内使用说明 |
|---|---|---|
| `claude` | `.claude/skills/`，链接到 `.agents/skills/` 中的对应项 | `CLAUDE.md` |
| `codex` | 直接使用 `.agents/skills/` | `AGENTS.md` |
| `opencode` | `.opencode/skills/`，链接到 `.agents/skills/` 中的对应项 | `AGENTS.md` |
| `trae` | `.trae/skills/`，链接到 `.agents/skills/` 中的对应项 | `.trae/rules/cannbot-knowledge.md` |
| `cursor` | `.cursor/skills/`，链接到 `.agents/skills/` 中的对应项 | `AGENTS.md` |
| `copilot` | `.github/skills/`，链接到 `.agents/skills/` 中的对应项 | `.github/copilot-instructions.md` |

Skill 通过符号链接复用同一知识仓及其相邻依赖，安装器不会向业务项目复制 `knowledge/` 正文。多个项目可以共享知识仓；更新它会影响所有引用它的项目，移动或删除它会使原有链接失效。单独复制 Skill 目录或只修改知识根变量不能修复这些依赖。

安装器不会修改 shell 启动文件；除通过所选 Python 的 `pip` 补齐运行依赖外，也不修改其他全局配置。资源恢复失败、路径冲突或托管标记异常时，会在写入目标项目之前停止；此前已完成的仓库获取或依赖安装可能保留。

## 验证安装并开始使用

### 验证安装

1. 查看安装命令末尾的 `project`、`knowledge root` 和 `project config`，确认分别指向目标项目、预期知识仓和项目配置。
2. 进入目标项目，并在该项目中打开 Agent 客户端。若安装前已有会话且未识别新 Skill，重新打开项目或会话后再验证。
3. 先查看知识覆盖，再执行一次真实查询，检查下述结果。

查看覆盖：

> 使用 `knowledge-query` 查看当前知识库实际包含哪些内容。

应返回从索引取得的知识卡统计，而不只是目录列表。随后用明确的平台和问题验证查询，例如：

> 使用 `ascendc-api-knowledge-query` 查询 950 平台上的 `DataCopyPad`。请选择相关知识卡并阅读全文，说明签名、约束和适用范围，并给出实际读过的卡片链接；证据不足的部分请明确说明。

这个例子只用于验证查询流程；实际任务请换成自己的目标平台和问题。成功标准是返回相关卡片、读取正文并给出可追溯回答；若返回有效零命中，按[没有结果时怎么办](#没有结果时怎么办)处理，不能仅凭覆盖统计认定目标问题已有答案。

正常通过 Agent 使用时无需手动 `source .cannbot/knowledge.env`，查询会从项目配置定位知识仓。下面直接读卡示例中的 `source` 只用于在终端展开路径。

### 先选择入口

| 问题形态 | 推荐入口 |
|---|---|
| 已知准确路径，答案只依赖一张确定的知识卡 | 把路径提供给 Agent，直接阅读全文 |
| 不知道卡片路径，或结论需要多张知识卡综合 | `knowledge-query` |
| Ascend C API 的契约、选型、相关卡片或本地头文件 | `ascendc-api-knowledge-query`，复用通用检索的索引和平台规则 |
| 新增、更新或检查知识 | 使用 `contributor` 模式，参照[贡献知识](../recipes/contribute_knowledge.md) |

查询时提供具体问题、目标技术和目标硬件平台；涉及版本差异或本机实现时，再提供 CANN 版本与组件包位置。平台或技术范围不明确时先补充信息。

各入口都应依据选中卡片的完整正文作答，并核对平台、版本、生命周期和来源。标题、摘要或来源链接本身不构成已核验证据；详细方法见[形成可追溯回答](../recipes/answer_with_evidence.md)，检索与补证细节由对应 Skill 维护。

### 方式一：直接读取确定的单张知识卡

已知卡片时，可在目标项目的 Bash 终端中取得其绝对路径：

```bash
cd /path/to/project
source .cannbot/knowledge.env
printf '%s\n' "$CANNBOT_KNOWLEDGE_ROOT/knowledge/common/platforms/concepts/ascend_910_95.md"
```

把输出路径提供给 Agent，例如：

> 请阅读全文 `/absolute/path/to/cannbot-knowledge/knowledge/common/platforms/concepts/ascend_910_95.md`，基于这张卡说明 Ascend 910 95 的基础硬件信息，并注明平台、版本和来源边界。

若一张卡不足以回答，转入对应检索 Skill 查找补充证据。

### 方式二：通过通用 Skill 检索和综合

需要组合多张知识卡，或分析实现、调试、优化、测试、模型、图和 Runtime 问题时，使用 `knowledge-query`。例如：

> 使用 `knowledge-query` 查询 950 平台上实现 Softmax 时可复用的算子设计、API 约束和已知性能问题。请选择相关知识卡，核对来源后综合回答。

### 方式三：查询 Ascend C API

Ascend C API 查询使用 `ascendc-api-knowledge-query`，示例见[验证安装](#验证安装)。需要本机声明或实现证据时，补充工程实际使用的 CANN 版本和 Ascend C 组件包路径，Agent 再按问题需要核验头文件。仅阅读知识卡不要求安装本机 SDK。

ACLNN 查询和完整算子实现分析使用 `knowledge-query`。更多场景见[查询 API](../recipes/api_search.md)。

### 怎样理解查询结果

| 看到的信息 | 含义与边界 |
|---|---|
| 覆盖情况 | 当前实际存在的知识卡；目录或注册分类不等于已有内容 |
| 候选卡 | 供 Agent 选择并继续阅读全文的入口，不能直接当作最终答案 |
| `status` | 草稿、稳定或废弃的生命周期，不保证技术正确性 |
| `verified` | 记录真实复核事件，不保证适用于所有平台和版本 |
| `sources` | 核对原始证据的入口，仍需判断是否支持当前结论 |
| 零结果 | 当前条件下没有找到卡片，不代表相关技术或 API 不存在 |

## 高级安装选项

以下 `bash install.sh` 命令均从已有知识仓根目录执行；也可将 `install.sh` 改为脚本的实际路径。完整参数说明可运行 `bash install.sh --help` 查看。

### 选择安装模式

| 需求 | 模式 | 安装内容 |
|---|---|---|
| 查询知识、回答技术问题 | `consumer`（默认） | `knowledge-query`、`ascendc-api-knowledge-query` |
| 新增或修改知识 | `contributor` | 上述两项，以及 `knowledge-ingest`、`knowledge-lint`、`ops-knowledge-vv-ingest`、`ops-knowledge-cv-ingest` |

```bash
bash install.sh claude /path/to/project contributor
```

模式只决定安装器托管的可用 Skill，不改变知识卡内容或可信程度。从 `contributor` 改为 `consumer` 后重跑安装器，会移除本知识仓对应的贡献类 Skill 链接，并同步已有的托管客户端入口。

`ops-knowledge-trace-ingest` 只用于知识仓内的 trace → Runbook 生产，不安装到业务项目。贡献流程见[贡献知识](../recipes/contribute_knowledge.md)，正式要求见 [CONTRIBUTING.md](../CONTRIBUTING.md)。

### 自定义位置、仓库与分支

指定托管知识仓位置：

```bash
bash install.sh claude /path/to/project consumer \
  --knowledge-root /data/cannbot-knowledge
```

也可以通过环境变量指定位置：

```bash
CANNBOT_KNOWLEDGE_INSTALL_ROOT=/data/cannbot-knowledge \
  bash install.sh claude /path/to/project consumer
```

托管克隆默认使用官方仓库 `https://gitcode.com/cann/cannbot-knowledge.git` 的 `master` 分支。仓库来源和分支也可配置：

| 命令行参数 | 对应环境变量 | 默认值 |
|---|---|---|
| `--repository-url` | `CANNBOT_KNOWLEDGE_REPOSITORY_URL` | 上述官方仓库 |
| `--repository-ref` | `CANNBOT_KNOWLEDGE_REPOSITORY_REF` | `master` |

命令行参数优先于对应环境变量。`--repository-ref` 接受分支名；更新已有托管仓库时，当前分支必须与请求分支一致，安装器不会切换分支或更新 detached HEAD。

测试其他仓库或分支时，建议使用独立知识仓和目标项目。先创建测试项目目录，再替换下列路径、仓库地址和分支占位符：

```bash
bash install.sh claude /path/to/test-project consumer \
  --knowledge-root /data/cannbot-knowledge-test \
  --repository-url '<仓库 HTTPS 地址>' \
  --repository-ref '<目标分支>'
```

下载脚本的地址与脚本随后克隆的仓库、分支分别配置。从某个分支下载脚本不会自动修改托管克隆的默认来源；使用上面的参数显式指定。在线安装时，可将这些参数追加到在线命令最后一行的 `consumer` 后面。

### Python 环境

需要指定解释器时使用 `CANNBOT_PYTHON`：

```bash
CANNBOT_PYTHON=/path/to/venv/bin/python \
  bash install.sh claude /path/to/project consumer
```

该变量选择安装器及其资源恢复步骤使用的 Python，不会把解释器路径写入项目配置。后续 Agent 查询也应使用装有这些依赖的 Python 环境；若安装时使用虚拟环境，启动客户端时也应确保查询可以使用该环境。

### 离线安装

断网前准备好完整的本地知识仓、上述命令行工具，以及所选 Python 环境中满足 `requirements.txt` 的依赖。需要核对原始文档或源码时，还应提前恢复对应资源。

```bash
bash install.sh claude /path/to/project consumer \
  --knowledge-root /data/cannbot-knowledge \
  --skip-repository-update \
  --skip-resources
```

`--skip-repository-update` 复用已有 Git checkout，不获取或核对远端 origin；`--skip-resources` 跳过文档和源码的恢复。**这两个参数不跳过 Python 依赖检查或安装**：缺依赖时仍会调用 `pip`，可能尝试联网。依赖提前满足后，才能按上述方式完成离线安装；索引仍会在本地验证或构建。

已有且符合来源要求的本地资源仍可用于核验；资源缺失时，只能使用现有知识卡，不能声称已核验缺失的原始材料。通常的在线安装应保留默认资源恢复。

## 更新与移除

安装和更新可能共用一个知识仓，操作前先确认项目配置中的知识仓路径。下面各项作用不同：

| 目的 | 操作 | 影响 |
|---|---|---|
| 更新在线安装的托管知识仓 | 重跑[在线安装](#在线安装)命令，保留原有客户端、模式及自定义参数 | 快进更新知识仓，再恢复资源、准备索引和刷新项目安装 |
| 更新显式指定位置的托管知识仓 | 重跑带 `--knowledge-root` 及匹配来源、分支的安装命令 | 与在线安装相同；受来源、分支和工作区检查约束 |
| 更新本地 checkout 后刷新安装 | 自行更新当前分支，再从仓内运行安装器 | 仓内执行本身不会更新知识仓，即使它位于远程默认目录 |
| 获取当前官方文档归档 | 在知识仓运行 `bash get_resources.sh --docs --refresh` | 更新本地文档来源，不自动更新知识卡或固定源码 |
| 刷新客户端托管提示词 | 使用 `--prompt-action reinstall` | 重建提示块，不重新安装 Skill；未指定模式时沿用原安装模式 |
| 移除客户端托管提示词 | 使用 `--prompt-action uninstall` | 只移除所选客户端的提示块，不删除 Skill、知识仓或项目配置 |

本地 checkout 在工作区和当前分支确认无误后，可按下面的方式更新；拉取失败时先处理原因，不继续安装：

```bash
cd /path/to/cannbot-knowledge
git pull --ff-only && bash install.sh claude /path/to/project consumer
```

普通重复安装会复用已完成的文档缓存。显式刷新归档后，维护者仍需按 Ingest 流程审查来源变化，才能更新知识卡。

只操作提示词时，在知识仓中按需执行以下一条命令：

```bash
bash install.sh claude /path/to/project --prompt-action reinstall
```

```bash
bash install.sh claude /path/to/project --prompt-action uninstall
```

安装器目前没有完整卸载命令。共享知识仓仍被其他项目使用时，应保留它；迁移位置时，需要同步处理引用它的项目配置和 Skill 链接，单独刷新提示词不能修复失效链接。

## 常见问题

先在目标项目的 Bash 终端中确认知识仓配置和 Skill 入口：

```bash
cd /path/to/project
cat .cannbot/knowledge.env
ls -l .agents/skills/knowledge-query .agents/skills/ascendc-api-knowledge-query
test -f .agents/skills/knowledge-query/SKILL.md && echo 'knowledge-query 可读取'
test -f .agents/skills/ascendc-api-knowledge-query/SKILL.md && echo 'ascendc-api-knowledge-query 可读取'
```

这些检查只确认配置与文件可访问，实际查询仍按[验证安装](#验证安装)执行。

| 问题 | 检查与处理 |
|---|---|
| 目标项目不存在 | 将示例路径替换为真实项目目录，并先创建或取得该项目 |
| 仓库来源或分支不匹配 | 在知识仓运行 `git remote get-url origin`、`git branch --show-current` 和 `git status --short`；核对安装参数并保留本地修改，需要另一分支时使用独立目录 |
| 仓库无法克隆或快进 | 保留 Git 错误输出；检查网络、权限和分支状态，不能快进时先人工处理 |
| `No module named yaml` 或其他运行依赖缺失 | 在 Agent 使用的环境中运行 `python3 -c 'import sys; print(sys.executable)'`，确认与安装时的 Python 一致，再用同一解释器补齐 `requirements.txt` 依赖；Python 3.10 还需要 `tomli` |
| `pip` 不可用、无权限或环境限制导致安装失败 | 使用允许安装依赖的 Python 环境，通过 `CANNBOT_PYTHON` 重跑安装，并确保查询也使用该环境 |
| 资源恢复失败 | 查看报错中具体资源和目录；修复网络或权限问题后重试。不完整目录或带本地修改的源码需先检查、保留内容，脚本不会覆盖它们 |
| Skill 路径冲突或链接失效 | 用 `ls -l` 检查报错路径指向，确认原知识仓是否移动；先保留用户文件，再处理明确属于旧安装的链接并重装。只改 `knowledge.env` 不能修复 Skill 链接 |
| 安装成功但客户端未识别 Skill | 确认打开的是目标项目；对照客户端表检查适配链接和使用说明，重新打开项目或会话后验证 |
| 查询使用了意外的知识仓 | 核对查询中显式指定的知识根、进程中的 `CANNBOT_KNOWLEDGE_ROOT` 和项目 `.cannbot/knowledge.env`；显式参数和环境变量会优先于项目配置 |
| 索引缺失、损坏或过期 | 对正确的知识仓重跑安装器以准备索引；只刷新提示词不会修复索引。仍失败时保留错误交给维护者 |
| 多张卡片结论冲突 | 比较平台、版本、生命周期和来源；证据仍不足时明确冲突和未确认部分 |

### 没有结果时怎么办

先区分索引错误和有效零命中。索引不可用时按上表修复，本次查询不能当作“没有知识”。

索引正常时，核对目标范围的实际覆盖、API 名或错误码，以及平台、技术和版本条件；由对应 Skill 按其流程补搜。仍无结果时，回答应说明已检查的范围、具体知识缺口，以及是否需要用户提供材料或允许核对其他来源。不要用其他平台或 DSL 的卡片替代目标证据。

## 继续阅读

- [设计原则](design_principles.md)
- [形成可追溯回答](../recipes/answer_with_evidence.md)
- [使用知识库进行算子开发](../recipes/operator_development.md)
- [贡献知识](../recipes/contribute_knowledge.md)
- [Knowledge Skills](../governance/specs/skills.md)
