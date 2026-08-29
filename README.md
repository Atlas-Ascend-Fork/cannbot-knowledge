# cannbot-knowledge

`cannbot-knowledge` 是 CANNBot 使用的知识库。它不保存算子工程或模型代码，而是把经过整理、能够追溯到固定来源或卡内原始观测的工程知识保存成 Markdown 知识卡，例如：

- 某个 CANN API 的语义和使用限制；
- 某种算子 DSL 的编程模型；
- 一个算子的设计、实现或优化方法；
- 某类编译、运行、精度或性能问题的排查步骤。

CANNBot 通过本仓提供的 Skill 生产、检索和检查这些知识，从而在回答问题或执行工程任务时复用经过治理、可以追溯来源的结论。

## 设计参考

本仓知识正文的文件化设计参考 Google 的 [Open Knowledge Format（OKF）v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/fe3268a70e8ca5110a43a8f1dfdf6d1a458cf79f/okf/SPEC.md)：知识使用带 YAML Frontmatter 的 Markdown 表达，通过目录和 `index.md` 渐进浏览，通过普通 Markdown 链接形成可重建关系，并使用 Git 分发和审计。

`knowledge/` 是本仓唯一且符合 OKF v0.2 的 Knowledge Bundle 根目录，其下所有卡片共享同一个 Concept ID 命名空间。`common/`、`ops/` 等只是 Bundle 内的分类，不是独立 Bundle；仓库根目录的 Skill、治理、测试和日志设施不属于 Bundle。详细边界见 [OKF Bundle 与 CANNBot Profile](governance/specs/okf.md)。

## 当前知识状态

当前 `knowledge/` 共有 4,495 张知识卡，覆盖 Ascend C 与模型场景：

- 2,810 张 API 卡；
- 304 张 Guide 卡，其中 Ascend C 270 张、模型场景 34 张；
- 612 张 Operator 卡，其中 559 张 ACLNN 全链路卡、53 张 Direct Invoke 卡；
- 471 张 Runbook 卡，其中 Ascend C 377 张、模型场景 94 张；
- 188 张 Concept 卡和 110 张 Optimization 卡，均位于模型各 route；
- Ascend C API/Guide 来源指向 Registry 登记的 `cann-docs-raw/` 固定归档，恢复时必须通过 SHA-256 校验；模型 Guide 来源固定到托管仓 40 位 Commit 和具体文件，Operator 来源固定到 CANN 官方 Git 仓 40 位 Commit 和具体文件。

上述数量是当前版本快照。五个 domain 根目录始终保留；`ops` 和 `model` 额外预建已注册 route，其他领域的下一层路径由领域维护者在首批真实知识落库时创建。只有 `index.md` 的结构入口不算正式知识卡，也不会出现在 Query 的实际覆盖统计中。“存在目录”不表示“已有知识”，实时数量以 Query `discover` 为准。

本地来源不提交到 Git。需要核对卡片证据时，在仓库根执行：

```bash
bash fetch-cann-docs.sh
```

脚本校验固定归档 SHA-256 后恢复到 `cann-docs-raw/`；带有匹配完成标记的目标会直接复用，其他已有目标会失败关闭。怀疑本地内容被修改时，应先检查并移走该目录，再重新获取固定归档。

## 这个仓库如何工作

```text
官方文档 / 固定版本源码 / 可复现实验
                    │
                    ▼
    knowledge-ingest / trace / VV / CV
                    │
                    ▼
               Markdown 知识卡
                 │        │
                 │        └── knowledge-lint 检查结构和治理规则
                 ▼
            knowledge-query
                    │
                    ▼
          CANNBot 读取正文并核对来源
```

本仓维护六项 Skill：五项是可安装的通用贡献能力，`ops-knowledge-trace-ingest` 只用于本知识仓内的 trace → Runbook 生产。

| Skill | 作用 | 是否修改知识仓 |
|---|---|---|
| `knowledge-query` | 查看实际知识覆盖，检索知识卡，并可保存不可覆盖的审计 receipt | 除指定 receipt 外只读 |
| `knowledge-ingest` | 统一路由新来源、增量、版本升级、通用建卡和图谱完整生命周期 | 可以创建候选卡并同步可提交的受管关系块；图谱 JSON 等产物始终 ignored |
| `knowledge-lint` | 检查目录、Frontmatter、来源、正文、导航和日志；整理 Issue 材料 | 否 |
| `ops-knowledge-trace-ingest` | 从算子开发 trace 蒸馏 Runbook，并按当前 Schema、索引和全库图谱门禁收口 | 仓内使用；只写经审查的 Runbook、导航和日志 |
| `ops-knowledge-vv-ingest` | 从固定版本源码提取不含可达 Cube/AIC 或 MIX_CV 节点的完整 Operator 卡 | 只写任务指定的最终卡 |
| `ops-knowledge-cv-ingest` | 从固定版本源码提取含可达 Cube/AIC 或 MIX_CV 节点的完整 Operator 卡 | 只写任务指定的最终卡 |

## 知识如何组织

大多数知识卡使用下面的路径：

```text
knowledge/<领域>/<技术或作用域>/<路径 Profile>/<知识卡>.md
```

例如，当前 API 卡可以采用分层主题目录：

```text
knowledge/ops/ascendc/apis/basic_api/data_copy/datacopy.md
```

其中：

- `ops` 表示算子领域；
- `ascendc` 表示这条知识只适用于 Ascend C；
- `apis` 是路径 Profile，表示它是一张 API 知识卡；
- `basic_api/data_copy` 是便于浏览的主题 section；
- bundle 内的 `ops/ascendc/apis/basic_api/data_copy/datacopy` 是 OKF Concept ID；移动卡片会改变该标识；
- Frontmatter `type: API` 是路径 Profile 的确定性投影，供 OKF consumer 读取。

不同 DSL 的专属知识分开保存。只有确实不依赖某个 DSL 的结论才能进入 `shared/`；两种技术之间哪些内容可以复用、哪些必须重新推导，则写入 `shared/interoperability/`。

Operator 卡按 `operators/<aclnn|direct>/<cv|math|nn|transformer>/<category>/<operator>.md` 组织；`aclnn` 保存公开 ACLNN/API 到 Kernel 的完整链路，`direct` 保存独立 Direct Invoke 路线，category 沿用 Registry 登记的官方源码一级分类。

每张知识卡的正文解释结论、适用条件和失效边界；文件开头的 Frontmatter 保存检索、平台、版本、生命周期和来源等结构化信息。详细规则见[治理规范](#治理规范)。

## 仓库目录

| 路径 | 用途 |
|---|---|
| `knowledge/` | 知识卡和逐层导航，是唯一知识正文目录 |
| `governance/schemas/` | 机器可读的字段、路径 Profile 和受控值规则 |
| `governance/specs/` | 对治理规则的完整文字说明 |
| `governance/contracts/` | Ingest、Query、Lint 和图谱共同使用的校验实现 |
| `.agents/skills/` | 三项基础 Skill、仓内 trace producer 与两项源码级 Operator producer 的规范源 |
| `docs/` | 知识库设计原则和用户指南 |
| `recipes/` | 面向具体任务的知识库最佳实践 |
| `evals/` | 检索、治理、文档和安装回归 |
| `init.sh` | 把 Skill 安装到目标项目 |
| `check.sh` | 运行仓库完整质量检查 |
| `artifacts/` | 本地生成且可重建的产物，默认不提交 |
| `logs/` | 已实施的知识和治理变更记录 |

## 使用知识库

安装 Skill 后，可以直接向 Agent 描述任务：

- “使用 `knowledge-query` 查看当前知识库包含哪些内容。”
- “使用 `knowledge-query` 检索目标平台上的某项 CANN API；零命中时明确报告当前知识缺口。”
- “使用 `knowledge-ingest` 把这份固定版本文档整理成候选知识卡。”
- “使用 `ops-knowledge-vv-ingest` 从固定源码提取非 Cube Operator 卡。”
- “使用 `ops-knowledge-cv-ingest` 从固定源码提取含 Cube/MIX_CV 的 Operator 卡。”
- “使用 `knowledge-lint` 检查本次知识修改。”

查询结果只是候选知识。形成技术结论前，Agent 仍需读取知识卡正文，核对适用平台、版本、信任层级和来源。

进一步了解知识库的设计和使用方式：

- [设计原则](docs/design_principles.md)：知识根、治理分层、范围隔离、证据和失败关闭等关键取舍。
- [用户指南](docs/user_guide.md)：consumer 与 contributor 的使用方式，以及如何理解查询结果。
- [形成可追溯回答](recipes/answer_with_evidence.md)、[贡献知识](recipes/contribute_knowledge.md)和[使用知识库查询 API](recipes/api_search.md)：面向具体任务的场景化实践。

## 环境准备

要求 Python 3.10 或更高版本。只使用知识库时安装运行依赖：

```bash
python3 -m pip install -r requirements.txt
```

参与知识、治理或 Skill 贡献时安装开发依赖即可；它已经包含运行依赖：

```bash
python3 -m pip install -r requirements-dev.txt
```

## 安装到项目

使用知识仓根目录的 `init.sh` 时，目标项目必须已经存在。`consumer` 只安装查询 Skill，`contributor` 安装三项基础 Skill 和两项 Operator producer，共5项。仓内专用的 `ops-knowledge-trace-ingest` 不安装到业务项目：

```bash
bash init.sh claude /path/to/project consumer
bash init.sh agents /path/to/project contributor
```

支持 `agents`、`codex`、`claude`、`opencode`、`trae`、`cursor` 和 `copilot`。安装器始终在目标项目的 `.agents/skills/` 创建规范链接，再按客户端创建适配链接；同时验证或构建只读检索索引、把知识根和安装 profile 写入项目级 `.cannbot/knowledge.env`，并向 `AGENTS.md` 或 `CLAUDE.md` 注入可卸载的托管使用入口。所有已知路径冲突和托管 marker 异常都在写入前失败，不复制知识正文，也不修改用户全局配置。

只刷新或移除托管入口时使用 `--prompt-action reinstall|uninstall`。`reinstall` 默认复用 `.cannbot/knowledge.env` 中记录的 profile；旧安装没有该字段时根据已安装的基础贡献 Skill 推导，也可以显式传 `consumer|contributor` 覆盖。复制安装 Skill 时，仍需在项目配置 `CANNBOT_KNOWLEDGE_ROOT` 或 `.cannbot/knowledge.env` 指向独立知识仓；Query 不在业务项目复制知识正文。

## 贡献和检查

贡献知识前阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。它说明如何查重、选择路径、准备来源、编写知识卡、更新导航和提交 Skill 变更。

提交前运行：

```bash
bash check.sh
```

该入口覆盖本仓知识 Lint（含严格 Git 来源导航）、Ascend C Runbook 正文门禁、检索回归、单元测试、Ruff、Shell 语法、基于现有 Agent 判定缓存的图谱合成/校验和 `git diff --check`。重新产生关系判定时，仍须按 Ingest 的多 Agent 全量流程执行。

## 治理规范

- [OKF Bundle 与 CANNBot Profile](governance/specs/okf.md)：Bundle 边界、OKF 对应关系和严格作者门禁。
- [知识路径](governance/specs/paths.md)：domain、technology/scope、路径 Profile、Concept ID 和索引规则。
- [Frontmatter 与证据](governance/specs/frontmatter.md)：字段组合、生命周期、来源、标签、平台和版本。
- [Schema、Registry 与 Contract](governance/specs/schemas.md)：机器事实源、受控词表和规则执行关系。
- [Knowledge Skills](governance/specs/skills.md)：Query、通用 Ingest、仓内 trace producer、Operator producer、Lint 和安装模式。

本仓采用 [CANN Open Software License Agreement 2.0](LICENSE)。
