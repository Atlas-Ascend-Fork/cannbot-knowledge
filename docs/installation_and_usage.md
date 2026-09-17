# 安装与使用 cannbot-knowledge

`install.sh` 是 cannbot-knowledge 的统一安装入口。本指南说明如何完成安装与验证，以及如何在直接读卡、通用检索和 Ascend C API 专用检索之间选择。

## 安装

### 前置条件

- Bash 和 Python 3.10 或更高版本；安装器默认使用 `python3`，也可通过 `CANNBOT_PYTHON` 指定解释器；
- 远程取得或更新知识仓需要 Git；在线安装和默认资源恢复还需要 `curl`、`tar`、`mktemp` 与网络；
- 运行依赖缺失时，所选 Python 需要提供 `pip`，安装器会自动按 `requirements.txt` 安装运行依赖；
- 已存在的目标项目目录；
- 目标文件系统支持符号链接。

这里不限定操作系统。Windows 下应在能够提供上述命令和符号链接能力的 Bash 环境中执行。安装器和资源脚本不依赖 GNU `realpath`、`sha256sum` 或 Bash 4 的 `readarray`。

### 在线安装

下面以 Claude Code 和只读消费模式为例：

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

命令先把脚本完整下载到临时文件，再交给 Bash 执行；下载失败会直接返回非零状态。若当前网络策略不允许访问 `raw.gitcode.com`，请改用下方的本地安装方式。

把 `claude` 换成当前客户端对应的安装器标识即可。支持 `codex`、`claude`、`opencode`、`trae`、`cursor` 和 `copilot`。第一个参数只选择目录与提示词适配方式，不会执行客户端命令。

远程执行时，安装器默认把官方仓库克隆到 `$HOME/.cannbot/cannbot-knowledge`。该目录已经存在时，只有来源匹配、当前分支正确、已跟踪文件无本地修改且可以快进，安装器才会更新。随后依次完成：

1. 检查当前 Python，并在缺少模块时按 `requirements.txt` 补齐运行依赖；
2. 运行 `get_resources.sh`，恢复官方文档归档并校验固定提交源码；
3. 验证或构建只读检索索引；
4. 在目标项目的 `.agents/skills/` 创建规范 Skill 链接，并为所选客户端创建适配链接；
5. 把 `CANNBOT_KNOWLEDGE_ROOT` 和安装模式写入项目级 `.cannbot/knowledge.env`；
6. 向所选客户端的持久指令文件写入带 marker、可重复安装和移除的使用入口。

安装器不会复制 `knowledge/` 正文或修改 shell 启动文件。除使用所选 Python 的 `pip` 补齐运行依赖外，也不修改其他全局配置。Skill 通过符号链接复用同一知识仓 checkout，确保相邻 Skill 与 `governance/contracts/` 版本一致；单独复制 Skill 目录并设置知识根不构成完整安装。资源恢复失败、路径冲突或托管 marker 异常时，安装器会在修改目标项目之前停止。

### 本地安装

无法访问上述 Raw 地址时，先克隆知识仓再执行安装器：

```bash
git clone https://gitcode.com/cann/cannbot-knowledge.git
cd cannbot-knowledge
bash install.sh claude /path/to/project consumer
```

已经取得仓库时，直接进入知识仓根目录执行最后一条命令。这种方式使用当前 checkout，不自动切换或更新分支。

### 选择安装模式

| 需求 | 模式 | 安装内容 |
|---|---|---|
| 查询知识、回答技术问题 | `consumer` | `knowledge-query`、`ascendc-api-knowledge-query` |
| 新增或修改知识 | `contributor` | 三项基础 Skill、`ascendc-api-knowledge-query`、`ops-knowledge-vv-ingest` 和 `ops-knowledge-cv-ingest` |

`consumer` 是默认模式。仓内 trace → Runbook 生产使用 `ops-knowledge-trace-ingest`，它不安装到业务项目。安装模式只决定安装器托管的可用 Skill，不改变知识卡内容或可信程度；从 `contributor` 切换为 `consumer` 时，安装器会移除自己创建的贡献类 Skill 链接，并同步已有的托管客户端入口。

### 自定义仓库位置与离线安装

指定托管知识仓位置：

```bash
bash install.sh codex /path/to/project consumer \
  --knowledge-root /data/cannbot-knowledge
```

测试分支或镜像可以显式传入 `--repository-url` 和 `--repository-ref`。更新已有托管知识仓时，当前分支必须与 `--repository-ref` 一致；安装器不会切换其他分支，也不会更新 detached HEAD。

已有知识仓需要完全离线使用时，同时传入 `--knowledge-root`、`--skip-repository-update` 和 `--skip-resources`。这种模式只验证本地 checkout 和仓库结构，不访问或核对远端 origin。跳过资源后，依赖官方文档归档或固定源码的证据核验不可用，因此不应作为普通安装方式。

```bash
bash install.sh codex /path/to/project consumer \
  --knowledge-root /data/cannbot-knowledge \
  --skip-repository-update \
  --skip-resources
```

已完成的本地文档缓存默认复用。维护者需要显式获取当前滚动文档归档时，在知识仓中运行：

```bash
bash get_resources.sh --docs --refresh
```

刷新只更新 Git 忽略的本地来源，不会自动更新知识卡；后续仍需按 Ingest 流程审查正文、结构和平台差异。

### 验证安装

安装成功后，目标项目应包含 `.cannbot/knowledge.env` 和对应的 Skill 链接。然后在当前 Agent 客户端中发起一次覆盖查询：

> 使用 `knowledge-query` 查看当前知识库实际包含哪些内容。

客户端正常返回真实知识卡统计，即表示托管入口、知识根、索引和运行依赖可用。目录存在或 Skill 链接存在本身不代表索引可用。

通过在线脚本或显式托管目录安装时，重复执行安装命令可以快进更新知识仓并刷新安装；从本地 checkout 执行时，应先自行更新当前分支。只刷新或移除 Agent 托管提示词时使用：

```bash
bash install.sh codex /path/to/project --prompt-action reinstall
bash install.sh codex /path/to/project --prompt-action uninstall
```

`uninstall` 只移除托管提示块，不删除 Skill、知识仓或项目配置；`reinstall` 只重建提示块，不重新安装 Skill。

## 使用

### 先选择入口

| 问题形态 | 推荐入口 |
|---|---|
| 已知准确路径，答案只依赖一张确定的知识卡 | 直接把知识卡路径提供给 Agent，阅读全文 |
| 不知道卡片路径，或结论需要多张知识卡综合 | `knowledge-query` |
| Ascend C API 的契约、选型、相关卡片或本地头文件 | `ascendc-api-knowledge-query`，它复用 `knowledge-query` 的索引和平台规则 |
| 新增、更新或检查知识 | 使用 `contributor` 模式中的生产与治理 Skill |

核心判断不是问题长短，而是证据是否已经明确绑定到唯一知识卡。明确单卡时直接读路径最短；需要发现候选、做范围过滤或组合证据时，应进入检索 Skill，不手工遍历知识目录。

### 方式一：直接读取确定的单张知识卡

硬件基础信息、固定概念等内容，如果已经知道唯一知识卡，可以直接给出路径。安装器写入客户端托管入口时，会把知识根解析成实际绝对路径，因此 Agent 不需要继承 shell 环境变量。例如 Ascend 910 95 的平台概念卡对应：

```bash
cd /path/to/project
source .cannbot/knowledge.env
printf '%s\n' "$CANNBOT_KNOWLEDGE_ROOT/knowledge/common/platforms/concepts/ascend_910_95.md"
```

把命令输出的绝对路径提供给 Agent，例如：

> 请阅读全文 `/absolute/path/to/cannbot-knowledge/knowledge/common/platforms/concepts/ascend_910_95.md`，基于这张卡说明 Ascend 910 95 的基础硬件信息，并注明平台、版本和来源边界。

直接读卡时仍要读取完整 Frontmatter 和正文，核对 `platforms`、生命周期、版本、限制与 `sources`，不能只使用标题或摘要。如果这张卡不足以支持答案，或者问题开始涉及其他 API、算子、调试经验或跨平台比较，应转入相应检索 Skill。

### 方式二：通过通用 Skill 检索和综合

不知道知识路径、需要多个事实共同支撑，或要解决实现、调试、优化、测试、模型、图和 Runtime 问题时，使用 `knowledge-query`。提问时至少说明具体问题、目标技术和目标硬件平台；相关时再补充 CANN 版本。

例如：

> 使用 `knowledge-query` 查询 950 平台上实现 Softmax 时可复用的算子设计、API 约束和已知性能问题。请选择并阅读全文，核对来源后再综合回答。

Skill 返回的路径、标题和摘要只是候选。Agent 必须选择相关卡片、阅读全文并核对平台、版本、限制和来源，之后才能形成结论；不需要打开所有命中或遍历所有链接。

### 方式三：查询 Ascend C API

Ascend C API 查询优先使用 `ascendc-api-knowledge-query`。它负责先确认硬件平台，再复用通用索引召回 API 卡，按需继续读取相关卡片和当前 CANN 包中的头文件。

例如：

> 使用 `ascendc-api-knowledge-query` 查询 950 平台上的 `DataCopyPad`。请阅读全文，说明签名、约束和适用范围；正文不足时再沿相关卡片或我提供的 CANN 包路径核验头文件。

如果需要本机声明或实现证据，还应提供工程实际使用的 CANN 版本和组件包路径。不要把 ACLNN 查询或完整算子实现分析交给这个专用 Skill；这些场景使用 `knowledge-query`。

### 查询前准备的信息

- 要解决的具体问题，例如 API 选型、错误排查或性能优化；
- 目标技术，例如 Ascend C 或 Triton；
- 目标硬件平台；
- 相关时的 CANN 版本和本地包位置；
- 零命中后是报告知识缺口，还是允许核对其他材料。

平台或技术范围不明确时，应先补充信息，不通过省略过滤条件扩大搜索范围。完整的可追溯回答方法见[形成可追溯回答](../recipes/answer_with_evidence.md)。

### 怎样理解查询结果

| 看到的信息 | 它表示什么 | 它不表示什么 |
|---|---|---|
| 覆盖情况 | 当前有哪些真实知识卡 | 所有目录和注册分类都有内容 |
| 候选卡 | 建议继续打开阅读的知识 | 可以直接使用的最终答案 |
| `status` | 卡片是草稿、稳定还是废弃 | 卡片一定正确或经过人工复核 |
| 由 `verified` 派生的信任层级 | 是否记录了机器或人工复核 | 卡片适用于所有平台和版本 |
| `sources` | 可以去哪里核对原始材料 | 来源一定支持正文全部结论 |
| 零结果 | 当前条件下没有找到卡片 | 相关技术不存在 |

### 没有结果时怎么办

先区分索引错误和有效零命中。索引缺失、损坏或过期时，本次查询无效，应重新运行安装器或由知识仓维护者准备索引。

索引正常时，再检查目标范围是否确有知识、平台/状态/技术条件是否正确、正文版本边界是否适用，以及 API 名、错误码或关键词是否准确。不要用其他平台或 DSL 的卡片填补结果。仍无结果时，应说明查询范围、已检查条件和下一步建议，不能据此判断相关技术不存在。

## 贡献知识

贡献知识使用 `contributor` 模式。开始前先用 `knowledge-query` 搜索同一主题并阅读已有卡片，明确采用 create、update、merge、split、deprecate 或 defer；随后使用匹配的生产 Skill，更新导航和日志，并通过 `knowledge-lint` 与目标查询验证。

完整流程见[贡献知识](../recipes/contribute_knowledge.md)，正式要求以 [CONTRIBUTING.md](../CONTRIBUTING.md) 为准。仓内 `ops-knowledge-trace-ingest` 仅用于从开发轨迹生产 Runbook，不是业务项目安装项。

## 常见问题

| 问题 | 处理方式 |
|---|---|
| 仓库无法克隆或更新 | 检查网络、仓库地址与分支；现有托管 checkout 有本地改动或无法快进时先人工处理，不由安装器覆盖 |
| `No module named yaml` | 重新执行安装命令让安装器补齐依赖；若自动安装失败，检查当前 Python 的 `pip` 是否可用及其错误输出 |
| 资源恢复失败 | 保留错误输出；检查网络或已存在但不完整的对应资源目录，不要让安装器覆盖它 |
| Skill 路径冲突 | 检查目标项目中的同名路径；安装器不会覆盖非本次安装创建的文件或目录 |
| 索引不可用 | 重新执行安装命令；仍失败时由知识仓维护者重建或检查索引 |
| 平台或技术不明确 | 补充真实目标范围，不扩大查询 |
| 多张卡片结论冲突 | 比较平台、版本、生命周期和来源；证据仍不足时保留冲突 |

## 继续阅读

- [设计原则](design_principles.md)
- [形成可追溯回答](../recipes/answer_with_evidence.md)
- [使用知识库进行算子开发](../recipes/operator_development.md)
- [贡献知识](../recipes/contribute_knowledge.md)
- [使用知识库查询 API](../recipes/api_search.md)
- [Knowledge Skills](../governance/specs/skills.md)
