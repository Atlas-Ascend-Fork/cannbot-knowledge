# cannbot-knowledge

`cannbot-knowledge` 是 CANNBot 使用的知识库。它不把算子工程或模型代码作为知识正文提交，而是把经过整理、能够追溯到固定来源或卡内原始观测的工程知识保存成 Markdown 知识卡，例如：

- 某个 CANN API 的语义和使用限制；
- 某种算子 DSL 的编程模型；
- 一个算子的设计、实现或优化方法；
- 某类编译、运行、精度或性能问题的排查步骤。

CANNBot 通过本仓提供的 Skill 生产、检索和检查这些知识，从而在回答问题或执行工程任务时复用经过治理、可以追溯来源的结论。

## 设计参考

本仓知识正文的文件化设计参考 Google 的 [Open Knowledge Format（OKF）v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/fe3268a70e8ca5110a43a8f1dfdf6d1a458cf79f/okf/SPEC.md)：知识使用带 YAML Frontmatter 的 Markdown 表达，通过目录和 `index.md` 渐进浏览，通过普通 Markdown 链接形成可重建关系，并使用 Git 分发和审计。

`knowledge/` 是本仓唯一且符合 OKF v0.2 的 Knowledge Bundle 根目录，其下所有卡片共享同一个 Concept ID 命名空间。`common/`、`ops/` 等只是 Bundle 内的分类，不是独立 Bundle；仓库根目录的 Skill、治理、测试和日志设施不属于 Bundle。详细边界见 [OKF Bundle 与 CANNBot Profile](governance/specs/okf.md)。

## 当前知识状态

当前 `knowledge/` 共有 4,856 张知识卡，覆盖 Ascend C、Triton-Ascend、公共平台与模型场景：

- 2,809 张 API 卡，其中 Ascend C 2,681 张、Triton 128 张；
- 465 张 Guide 卡，其中 Ascend C 274 张、Triton 157 张、模型场景 34 张；
- 611 张 Operator 卡，其中 559 张 ACLNN 全链路卡、52 张 Direct Invoke 卡；
- 565 张 Runbook 卡，其中 Ascend C 459 张、Triton 12 张、模型场景 94 张；
- 193 张 Concept 卡，其中公共平台 5 张、模型场景 188 张；
- 202 张 Optimization 卡，其中 Triton 92 张、模型场景 110 张；
- 11 张 Triton Example 卡；
- Ascend C API/Guide 来源指向 Registry 登记的 `cann-docs-raw/` 固定归档，恢复时必须同时通过归档和最终内容树 SHA-256 校验；模型 Guide 来源固定到托管仓 40 位 Commit 和具体文件，Operator 来源固定到 CANN 官方 Git 仓 40 位 Commit 和具体文件。

上述数量是当前版本快照。Registry 中注册的所有 domain 根目录始终保留；`ops` 和 `model` 额外预建已注册 route，其他领域的下一层路径由领域维护者在首批真实知识落库时创建。只有 `index.md` 的结构入口不算正式知识卡，也不会出现在 Query 的实际覆盖统计中。“存在目录”不表示“已有知识”，实时数量以 Query `discover` 为准。

本地来源不提交到 Git。需要核对卡片证据时，在仓库根执行：

```bash
bash get_resources.sh
```

脚本默认恢复文档及 `ops-nn`、`ops-math`、`ops-transformer`、`ops-cv` 源码；也可用 `--docs` 或 `--code` 单独恢复。源码按 Registry 中的固定 40 位提交统一放在 `cann-ops-raw/ascendc/<仓库名>/<commit>/`，当前每仓只登记一个提交，Direct Invoke 与 ACLNN 共用同仓基线；复用前校验提交、来源和工作区，拒绝覆盖本地修改。Operator 的本地 `sources` 路径相对于知识仓根，本地化只改写可用文件，对缺失来源明确报告，不自动切换版本。安装器默认准备这些资源；显式离线安装可传 `--skip-resources`。源码与归档均不提交。

API 卡片通过普通 Markdown 链接引用算子知识。需要发现新引用时，可按需生成基于固定源码调用或正文示例的建议；建议区分证据来源和扫描范围，不证明运行时可达性，也不限制卡片已有链接的数量。

图谱按需读取卡片之间的现有链接；API 引用建议单独按需执行，不作为知识入库或 CI 构图的前置步骤。

文档恢复时，脚本校验固定归档 SHA-256 后恢复到 `cann-docs-raw/`，并以固定文件、token 和数量幂等修复该批发布器误扩展到代码围栏中的链接；即使完成标记匹配，复用前也会重新计算整个最终内容树的 SHA-256，其他已有目标失败关闭。官方 API/Guide 只为含独立技术事实的来源页建卡，README、发布占位、纯链接目录和接口清单由逐层 `index.md` 统一导航；保留页的“产品支持情况”先写入 Frontmatter `platforms` 再从正文省略，其余正文保持完整并修正失效链接，可通过普通 Markdown 链接导航到使用相关 API 的算子知识。

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

本仓维护七项 Skill：六项可安装到业务项目，`ops-knowledge-trace-ingest` 只用于本知识仓内的 trace → Runbook 生产。

| Skill | 作用 | 是否修改知识仓 |
|---|---|---|
| `knowledge-query` | 查看实际知识覆盖，检索知识卡，并可保存不可覆盖的审计 receipt | 除指定 receipt 外只读 |
| `ascendc-api-knowledge-query` | 复用 Query 按硬件平台检索 Ascend C API，阅读全文并按需追踪相关卡片和本地 CANN 头文件 | 否 |
| `knowledge-ingest` | 统一路由新来源、增量、版本升级和通用建卡，支持按需链接图谱 | 创建候选卡；构图只读正文，产物始终 ignored |
| `knowledge-lint` | 检查目录、Frontmatter、来源、正文、导航和日志；整理 Issue 材料 | 否 |
| `ops-knowledge-trace-ingest` | 从算子开发 trace 蒸馏 Runbook，并按当前 Schema、索引和Lint 和检索门禁收口 | 仓内使用；只写经审查的 Runbook、导航和日志 |
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
| `.agents/skills/` | 三项基础 Skill、Ascend C API 专用消费流程、仓内 trace producer 与两项源码级 Operator producer 的规范源 |
| `docs/` | 知识库设计原则和用户指南 |
| `recipes/` | 面向具体任务的知识库最佳实践 |
| `evals/` | 检索、治理、文档和安装回归 |
| `OAT.xml` | GitCode 开源扫描使用的 CANN 2.0 许可策略和 matcher |
| `init.sh` | 把 Skill 安装到目标项目 |
| `check.sh` | 运行仓库完整质量检查 |
| `artifacts/` | 本地生成且可重建的产物，默认不提交 |
| `logs/` | 已实施的知识和治理变更记录 |

## 使用知识库

安装 Skill 后，可以直接向 Agent 描述任务：

- “使用 `knowledge-query` 查看当前知识库包含哪些内容。”
- “使用 `ascendc-api-knowledge-query` 查询目标硬件上的 Ascend C API；必要时沿相关卡片和当前 CANN 包头文件核验。”
- “使用 `knowledge-query` 检索目标平台上的某项 CANN API；精确 API 名零命中时独立补搜未定位 draft，仍无结果再明确报告当前知识缺口。”
- “使用 `knowledge-ingest` 把这份固定版本文档整理成候选知识卡。”
- “使用 `ops-knowledge-vv-ingest` 从固定源码提取非 Cube Operator 卡。”
- “使用 `ops-knowledge-cv-ingest` 从固定源码提取含 Cube/MIX_CV 的 Operator 卡。”
- “使用 `knowledge-lint` 检查本次知识修改。”

查询结果只是候选知识。形成技术结论前，Agent 仍需读取知识卡正文，核对适用平台、版本、信任层级和来源。

进一步了解知识库的设计和使用方式：

- [设计原则](docs/design_principles.md)：知识根、治理分层、范围隔离、证据和失败关闭等关键取舍。
- [用户指南](docs/user_guide.md)：consumer 与 contributor 的使用方式，以及如何理解查询结果。
- [形成可追溯回答](recipes/answer_with_evidence.md)、[贡献知识](recipes/contribute_knowledge.md)和[使用知识库查询 API](recipes/api_search.md)：面向具体任务的场景化实践。
- [使用知识库进行算子开发](recipes/operator_development.md)：把知识检索、实现与验证串联到算子开发任务中。

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

使用知识仓根目录的 `init.sh` 时，目标项目必须已经存在。`consumer` 安装 `knowledge-query` 和 `ascendc-api-knowledge-query`；`contributor` 安装三项基础 Skill、`ascendc-api-knowledge-query` 和两项 Operator producer，共6项。仓内专用的 `ops-knowledge-trace-ingest` 不安装到业务项目：

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

该入口先恢复并校验登记资源，再执行知识 Lint、固定归档受控转换复验、Runbook 正文检查、检索回归、单元测试、Ruff 和 Shell 语法检查。官方 `LICENSE` 原文不参与通用差异空白检查；固定归档 API/Guide 只对保留的来源正文行豁免 Git 空白提示，Frontmatter 与追加的普通链接仍执行通用检查。图谱按需从卡片间现有链接生成，API 引用建议也按需执行，两者都不是入库门禁；CI 保留同一轻量链接构图入口。

## 治理规范

- [OKF Bundle 与 CANNBot Profile](governance/specs/okf.md)：Bundle 边界、OKF 对应关系和严格作者门禁。
- [知识路径](governance/specs/paths.md)：domain、technology/scope、路径 Profile、Concept ID 和索引规则。
- [Frontmatter 与证据](governance/specs/frontmatter.md)：字段组合、生命周期、来源、标签、平台和版本。
- [Schema、Registry 与 Contract](governance/specs/schemas.md)：机器事实源、受控词表和规则执行关系。
- [Knowledge Skills](governance/specs/skills.md)：Query、通用 Ingest、仓内 trace producer、Operator producer、Lint 和安装模式。

本仓采用 [CANN Open Software License Agreement 2.0](LICENSE)。
