# Checks

需要解释错误、选择局部/全库模式或审阅 Lint 覆盖边界时读取本文件。

## 确定性检查

每项检查在 `governance/contracts/checks/` 中独立实现，并在 `__init__.py` 静态注册。P0 阻断门禁，P1 建议修改，P2 提供提示。

| ID | 等级 | 检查内容 |
|---|---|---|
| `path` | P0 | domain-route、Profile、内容型 section、Operator/Runbook 附加层级和小写 snake_case 卡名合法 |
| `profile` | P0 | YAML mapping 无重复 key；JSON Schema、公共/Profile 必选字段、非空标题摘要和路径到 OKF type 的映射一致；缺失与空白分别报告 |
| `body` | P0 | 正文非空且围栏外至少有一个 H1；除 Registry 文档归档主来源的 API/Guide 受控转换可保留来源中的多个 H1 外，其余卡恰有一个 H1；摘要不含发布占位，正文无 Git 冲突标记或压平到单行的 Markdown 表格 |
| `images` | P0 | Markdown/HTML 图片使用含 40 位 commit 和具体文件路径的 HTTPS Git raw URL，忽略代码中的伪图片 |
| `tags` | P0 | 标签受控、无重复，且至少包含一个 task 和一个 topic |
| `sources` | P0 | 非 draft 且非 Runbook 的卡必须有来源；Runbook 允许空来源，轨迹证据由专用 producer 审查；资源安全；Git 文件和目录固定到 40 位 commit，GitCode/GitHub PR/Issue 使用规范工作项 URL |
| `time` | P0 | 时间为有效 UTC 秒精度，且 `updated_at >= created_at` |
| `trust` | P0 | `verified` actor 合法 |
| `platforms` | P0 | 非 Glossary 的平台字段必填、值受控，`agnostic` 不混用，非 draft 范围非空；Glossary 不使用该字段；文档归档 Frontmatter 与恢复后的来源产品支持表、能力枚举或明确限定整卡/接口范围一致，配置为省略的产品支持章节不得残留在卡片正文；不把全为“不支持”或“实际功能不生效”的产品族加入检索范围，也不把架构演进、章节内局部能力或工作模式限制提升为整卡范围；没有可解析明确范围证据时必须为 `draft` 与空范围，不自动写 `agnostic` |
| `lifecycle` | P0 | `replaced_by` 使用规范 Concept ID，目标为 Bundle 内合法路径的现有非索引卡，拒绝自引用与符号链接越界 |
| `interoperability` | P0 | source/target 是不同的已注册 technology |
| `source_navigation` | P0 | strict 模式下，宽 tree 来源具有同 revision 的精确 blob 导航 |
| `navigation` | P0 | Bundle 根、注册 route、逐层 index、缺失/空目录和重复导航合法；非结构目录至少含合法直接卡或合法子 index |
| `index_entry_description` | P1 | 每个索引条目带有摘要 |
| `local_sources` | P0 | 本地来源获取脚本、归档标记或 Git 固定提交/来源/干净工作区、已恢复文件合法 |
| `links` | P0 | 代码块（含列表缩进围栏）、行内代码和图片之外的 Markdown 本地目标位于 `knowledge/` 且存在并为文件；知识卡可额外链接登记的固定提交源码文件，未恢复时只检查登记路径，索引无此例外；Finding 保留引用行号和原始目标 |
| `logs` | P0 | 日志文件名、H1、entry 和 Summary/Details 合法 |
| `log_order` | P1 | 同一天的日志条目按时间倒序；同一时间允许并列 |
| `index_sync` | P0 | 生成式索引与知识树同步；仅在其他检查无 P0 时执行 |

当前没有 P2 格式检查项。

正文和平台检查只屏蔽代码围栏，链接和图片检查同时屏蔽行内代码；四类检查共用 `contracts/checks/links.py` 的边界解析并保留原文行号。围栏必须由相同字符、不短于起始长度且行尾无其他内容的标记闭合。

## 运行模式

- 无 card/sample：扫描全部知识 Markdown，执行结构、导航和日志检查。
- 一个或多个 `--card`：只检查指定卡和相对链接，不检查完整树。
- `--sample N`：按稳定路径散列选择 N 张卡，只用于快速抽样；不能与 `--card` 同用。
- `--strict-navigation`：加强代码来源导航准入，可与局部、抽样或全库模式组合。
- `--json`：输出 `root`、`checked` 和完整 `findings`。每条 Finding 固定包含 `check`、`tier`、`path`、`line`、`code`、`message` 和 `details`；没有行号或具体值时为 `null`。

退出码 `0` 表示完整执行且没有 P0，`1` 表示至少一个 P0，`2` 表示参数、规则、知识根或输入不可用。P1/P2 不改变退出码。

Lint 使用本 Skill 所属仓的 Contract 校验目标根；`knowledge.py` 提供兼容门面，`contracts/checks/` 按类别静态注册实现。两边 Contract 文件不一致时以退出码 `2` 失败，不导入或执行目标根的 Python。

## 人工审阅边界

机器检查不能证明 URL 可访问、source 足以支持正文、平台实验真实发生或结论正确。来源 claim mapping、同名 API 边界、因果证据和版本冲突仍需独立审阅。
