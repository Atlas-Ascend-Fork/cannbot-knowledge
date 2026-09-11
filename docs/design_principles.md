# 知识库设计原则

cannbot-knowledge 不只是一个 Markdown 文件夹。它希望把工程经验整理成可以查询、可以核对来源、也可以长期维护的知识。

下面介绍仓库最重要的设计原则。字段和路径的详细规则见[治理规范](../README.md#治理规范)。

## 1. 技术知识统一放在 `knowledge/`

[`knowledge/`](../knowledge/index.md) 是仓库中唯一保存技术知识正文的目录。

其他目录各有自己的用途：

- `governance/` 保存规则；
- `.agents/skills/` 保存工作流程；
- `evals/` 保存测试；
- `docs/` 保存说明文档；
- `recipes/` 保存场景化操作指南。

这样可以避免同一条技术知识散落在多个地方。查询工具也只需要从一个位置读取知识。

## 2. 知识既要方便人读，也要方便工具处理

每张知识卡由两部分组成：

- Markdown 正文：说明结论、适用条件和限制；
- 文件开头的 Frontmatter：保存类型、平台、版本、状态和来源等结构化信息。

人可以直接阅读正文，工具可以根据 Frontmatter 进行过滤和检查。仓库使用 OKF v0.2 作为基础格式，再通过 CANNBot Profile 这套仓库规则增加更严格的要求。详细关系见 [OKF Bundle 与 CANNBot Profile](../governance/specs/okf.md)。

## 3. 先确认范围，再使用结论

同一个 API 或实现方法，在不同 DSL、平台或版本上可能有不同表现。因此，查询知识时必须先确认：

- 属于哪个领域；
- 使用哪种技术或作用范围；
- 面向哪个平台；
- 是否受 CANN 版本影响。

一个 DSL 的经验不能直接当成另一个 DSL 的结论。只有真正不依赖单一技术的知识才能放进 `shared`。跨技术对比则放进 `interoperability`。路径规则见[知识路径](../governance/specs/paths.md)。

## 4. 规则不仅要写清楚，还要能自动检查

仓库把规则分成几类：

| 位置 | 负责什么 |
|---|---|
| Schema 和 Profile | 定义字段格式、必填字段和知识类型 |
| Registry（注册表） | 列出允许使用的平台、技术、标签和路径值 |
| Contract（统一校验） | 检查路径、字段、链接和导航之间的关系 |
| Spec | 用文字解释规则和使用边界 |
| Skill | 在查询、摄入和检查时使用这些规则 |

同一条规则只在一个机器文件中定义。发现文档和程序行为不一致时，应修正规则及相关实现，不能只在某个 Skill 中增加例外。详细说明见 [Schema、Registry 与 Contract](../governance/specs/schemas.md)。

## 5. “稳定”“有来源”“经过复核”不是一回事

一张知识卡可以有来源，也可以进入 `stable` 状态，但这不代表它一定经过人工复核，更不代表它适用于所有平台和版本。

- `status` 表示卡片处于草稿、稳定还是废弃状态；
- `verified` 记录真实发生的复核；
- `sources` 记录结论来自哪里。

使用者需要同时查看这几项，而不是只看其中一个。完整定义见 [Frontmatter 与证据](../governance/specs/frontmatter.md)。

## 6. Query 只提供候选知识

Query 会先按平台和技术范围过滤，再返回最相关的知识卡。当前不按 CANN 版本过滤；使用者需要打开候选卡正文，核对版本边界和来源。

索引缺失、损坏或过期时，Query 会直接停止。没有搜索结果时，也只能说明“当前条件下没有找到”，不能说明相关技术不存在。

## 7. 查询、写入和检查分开处理

仓库维护三项基础 Skill、一项 Ascend C API 专用消费流程、一项仓内 trace producer 和两项源码级 Operator producer：

| Skill | 用途 |
|---|---|
| `knowledge-query` | 查看覆盖情况、搜索知识卡 |
| `ascendc-api-knowledge-query` | 复用 Query 按平台查询 API，阅读全文并按需核验相关卡和本地头文件 |
| `knowledge-ingest` | 根据来源创建候选知识卡 |
| `knowledge-lint` | 检查知识卡、导航、链接和日志 |
| `ops-knowledge-trace-ingest` | 从算子开发 trace 生产 Runbook，只在本知识仓使用 |
| `ops-knowledge-vv-ingest` | 提取不含可达 Cube/AIC 或 MIX_CV 节点的源码级 Operator 卡 |
| `ops-knowledge-cv-ingest` | 提取含可达 Cube/AIC 或 MIX_CV 节点的源码级 Operator 卡 |

Query 和 Lint 保持只读。Ingest 可以创建候选卡；trace producer 只在本仓生产 Runbook；VV/CV 只写任务指定的最终 Operator 卡。三类生产能力都不会自动提交或发布。完整边界见 [Knowledge Skills](../governance/specs/skills.md)。

## 8. 索引和图谱都可以重新生成

检索索引和本地图谱都是可重建的工具产物，默认不提交。图谱只把知识卡作为节点、卡片之间的普通 Markdown 链接作为有向边，API 与算子关联也来自这些链接；目录索引仍只承担导航。构图按需执行，不回写卡片、不依赖关系缓存，不是知识入库的必做步骤。源码扫描仅在需要 API 引用建议时单独执行，建议不会直接成为图谱边。

这样只需要维护知识正文和规则，不需要再手工维护另一份索引或关系数据。

## 需要记住的边界

- 结构检查通过，不代表技术结论一定正确。
- 有来源，不代表来源一定充分。
- 搜索命中，不代表结论适用于所有平台和版本。
- 目录存在，不代表目录中已经有知识卡。
- 高风险结论仍然需要检查源码、运行实验或进行性能分析。

这些边界可以避免把知识库当成“自动给出正确答案”的系统。
