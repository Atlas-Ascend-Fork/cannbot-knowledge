# Schema、Registry 与 Contract

`governance/schemas/` 保存声明式机器规则，`governance/contracts/` 负责组合和执行这些规则。所有 YAML mapping 拒绝重复 key，避免解析时静默覆盖规则或卡片字段。Spec 解释语义和贡献边界，但不是另一套机器事实源。

## 唯一职责

| 文件 | 负责 | 不负责 |
|---|---|---|
| `schemas/frontmatter.schema.json` | OKF 与扩展字段白名单、数据类型、数组形状和基础枚举 | 不按路径 Profile 选择字段，不保存平台或标签词表 |
| `schemas/profiles.yaml` | 八个公共必选字段、Profile 到 OKF `type` 的映射、各 Profile 字段组合 | 不定义字段数据类型，不判断路径是否合法 |
| `schemas/registries.yaml` | domain、route、platform、标签、受控附加路径值和固定归档本地来源 | 不保存知识正文、逐卡来源、发布版本或变更历史 |
| `contracts/knowledge.py` | 路径推导、声明组合、跨字段/文件关系和导航 | 不复制平行枚举，不判断技术结论是否正确 |

同一规则只能有一个机器事实源：字段形状归 JSON Schema，字段组合和 `okf_type` 归 Profile，受控值归 Registry，依赖路径、其他字段或其他文件的关系归 Contract。

## Registry 分区

`registries.yaml` 是多个消费者共享的小型受控词表。“已注册”表示工具能识别，不表示 `knowledge/` 必须预建对应路径或已有 Concept。Contract 只强制 domain 根和 `ops`/`model` 的注册 route 作为协作骨架。

| 分区 | 保存内容 | 主要用途 |
|---|---|---|
| `domains` | 顶层领域、允许直辖的 `direct_types` 及是否 `precreate_routes` | 路径校验、domain 过滤、协作骨架 |
| `technologies` | DSL、语言、框架或引擎及允许的 domain | route、technology 和跨技术端点校验 |
| `scopes` | `shared`、平台、工具链、推理/训练等非技术 route | route、scope 和 shared 过滤 |
| `paths` | Operator family/category 和 Runbook area | 受控附加层级校验 |
| `platforms` | 卡片适用平台 ID | Frontmatter 校验和 platform 过滤 |
| `tags` | task、topic、paradigm 三个维度的规范标签 | 标签校验、任务映射、过滤和召回 |

technology 与 scope 的 ID 不得重叠；每个 route 必须声明允许出现的 domain；`precreate_routes` 只能是布尔值；标签 ID 前缀必须与其维度一致。完整结构由 Contract 在加载时检查。

新增注册值必须同时满足：现有值无法准确表达需求、归属和语义明确、有真实知识或确定性消费者即将使用，并在同一变更补充接受/拒绝测试和检索回归。若属于 `ops` 或 `model`，还要同步其 route 结构入口；其他领域由维护者随真实内容创建路径。不要只为来源别名、任意占位或一次性任务扩充 Registry。

## 执行关系

```text
                         frontmatter.schema.json：字段形状
知识路径 + Frontmatter ── profiles.yaml：Profile、OKF type、字段组合
                         registries.yaml：受控路径和值
                                      │
                                      ▼
                            governance Contract
                     组合路径、字段、引用与导航规则
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
                 Ingest             Query              Lint
                 写前拒绝           加载失败关闭        只读报告
                                      │
                                      ▼
                              本地图谱构建前校验
```

图谱不是第四套规则解释器；它只从通过同一 Contract 的 Concept 和显式链接生成本地产物。

## 为什么需要 Contract

JSON Schema 只能检查单个对象的形状，不能独立完成：

- 从路径推导 domain、technology/scope、Profile 和 Bundle 相对 Concept ID；
- 校验卡片 `type` 等于 Profile 的 `okf_type`；
- 判断 route 与 domain 是否允许组合；
- 校验 Operator 和 Runbook 附加层级；
- 要求 `tags` 同时覆盖 task 和 topic；
- 限制 `agnostic` 与具体平台混用；
- 比较 `created_at` 与 `updated_at`；
- 判断来源位于已登记本地根目录或使用 HTTP(S)，并判断识别出的 Git URL 是否固定到 commit；
- 校验 `verified` actor、`replaced_by` 和跨技术端点；
- 校验 Bundle 根版本、必需协作骨架、逐层索引和 Bundle 内 Markdown 链接。

这些规则统一放在 Contract，不通过某个 Skill 的局部例外实现。

## 机器检查与人工审阅

机器规则可以证明结构一致、取值受控和引用目标存在，但不能证明：

- 来源当前可访问且充分支持正文；
- 技术语义、实验和平台边界正确；
- shared 知识足够通用；
- 两种 DSL 的行为真正等价；
- `verified` 事件对应的复核实际发生。

后一类问题必须由贡献者和 reviewer 判断。机器声明、Contract 和 Spec 不一致时，应在同一变更修复事实源、执行逻辑、文档和回归，而不是选择其中一份绕过。

## 修改规则

| 变更 | 至少同步 |
|---|---|
| Frontmatter 字段 | JSON Schema、相关 Profile、Contract 消费、Frontmatter 文档、正反测试 |
| 路径 Profile | Profile、路径深度或特殊规则、路径/Frontmatter 文档、检索回归 |
| domain、technology 或 scope | Registry、路径接受/拒绝测试、Query 过滤、导航 |
| platform、标签或附加路径值 | Registry、真实消费卡、Lint/Query 回归、相关文档 |
| 删除、重命名或收紧规则 | 全部知识卡、evals、三个 Skill 和兼容性说明 |

修改后运行仓库统一质量检查。新增规则必须覆盖至少一个接受案例和一个拒绝案例，不能只修改声明让当前样例通过。
