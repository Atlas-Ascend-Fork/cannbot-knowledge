# 路径与 Frontmatter Profile

选择目标路径或构造候选卡时读取本文件；机器事实始终以知识仓 `governance/schemas/` 和统一 Contract 为准。

## 公共字段

所有 Concept 都需要 `type`、`title`、`description`、`tags`、`status`、`sources`、`created_at`、`updated_at`。Frontmatter 是无重复 key 的 YAML mapping；不要用后出现字段静默覆盖前值。

| 路径 Profile | OKF type | 额外必填 | 允许可选 |
|---|---|---|---|
| `concepts` | `Concept` | `platforms` | `cann_versions`, `aliases`, `verified`, `replaced_by`, `scope` |
| `apis` | `API` | `platforms` | `cann_versions`, `source_headers`, `aliases`, `verified`, `replaced_by` |
| `examples` | `Example` | `platforms` | `cann_versions`, `verified`, `replaced_by` |
| `guides` | `Guide` | `platforms` | `cann_versions`, `aliases`, `verified`, `replaced_by`, `scope` |
| `operators` | `Operator` | `platforms` | `cann_versions`, `verified`, `replaced_by` |
| `optimizations` | `Optimization` | `platforms` | `cann_versions`, `verified`, `replaced_by`, `scope` |
| `runbooks` | `Runbook` | `platforms` | `aliases`, `verified`, `replaced_by`, `scope` |
| `interoperability` | `Interoperability` | `platforms`, `source_technology`, `target_technology` | `cann_versions`, `verified`, `replaced_by` |
| `glossaries` | `Glossary` | 无 | `aliases`, `verified`, `replaced_by` |

路径选择 Profile，Profile 的 `okf_type` 生成卡片 `type`；不得手工创造另一种映射。平台无关写 `[agnostic]`，未知写 `[]` 并保持 `draft`。

## 场景适用条件

`scope` 可选且允许部分声明，只填写来源支持并有过滤价值的条件；未知维度省略，不以 `any` 或否定条件补齐。不同领域使用各自注册的 Schema、适用范围和维度语义，共享形状和三态协议。具体语法见治理 [Frontmatter](../../../../governance/specs/frontmatter.md#场景适用条件scope) 与 [机器契约](../../../../governance/specs/schemas.md)，不在 producer 中维护第二份词表。

## Trust

没有 `verified` 表示 unverified。只有真实执行验证或人工复核后，才记录带 actor 和时间的 OKF event：

```yaml
verified:
  by: human:reviewer_id
  at: "2026-08-15T08:00:00Z"
```

Actor 使用 `human:<id>`、`process:<id>` 或 `<producer>/<version>`。不得把来源固定、Lint 通过或旧的 provisional/verified 枚举转换成虚假 event。

## 路径附加层级

- 路径满足 domain-route 矩阵；Concept ID 相对 `knowledge/`，不带该前缀和 `.md`。
- Concept 与索引导航只能指向同一 `knowledge/` Bundle；知识卡还可引用 Registry 登记的 `kind: git` 固定提交源码文件作为本地来源链接，不形成图谱节点。`sources[].resource` 相对于知识仓根，正文链接相对于当前卡目录。
- `interoperability` 只能位于同领域 `shared`，并声明不同的 source/target technology。
- `concepts`、`apis`、`examples`、`guides` 和 `optimizations` 可以增加小写 `snake_case` 主题 section。
- 已停用 section 由 Registry 的 `paths.forbidden_sections` 按 domain/route/Profile 声明，卡片和索引共用检查；模型推理的 Guide 与 Optimization 不再使用 `experience` 层。具体职责与当前任务目录见治理路径 Spec。
- operator 使用 `operators/<call-mode>/<family>/<category>/<operator>.md`；`call-mode` 当前为 `aclnn` 或 `direct`。
- runbook 使用 `runbooks/<area>/<runbook>.md`。
- call mode、family、family 下的 category 和 area 的合法值从 `registries.yaml` 的 `paths` 分区读取。

## 创建脚本行为

- `--tag`、`--source`、`--platform`、`--cann-version`、`--alias` 可重复。
- `--source` 参数写入 OKF `sources[].resource`；第一项自动带 `role: primary`。来源可以是 HTTP(S)，也可以是 Registry 登记的文档归档或固定提交 Git 本地路径。
- `--verified-by` 与 `--verified-at` 必须同时出现，当前一次创建一个 event；多个 event 可在审阅后人工补充。
- `--dry-run` 输出完整 Markdown，但不创建目录、卡片、索引或日志。
- `--scope-file` 读取 JSON/YAML 格式的 Scope 对象本身，执行统一 Contract 校验后写入可选 Frontmatter `scope`。不要求每张卡填写；来源支持且有过滤价值的部分条件即可声明，未知维度省略，不为补齐字段写 `any`。Schema、维度和匹配方式按领域注册，不套用模型字段。
- 模型推理卡片可用 `parallelism.none_of` 声明来源明确排除的并行方式，不接受查询专用 `model_features.none_of`，不使用别名或自动推断条件。集合的 `all_of` 与 `none_of` 至少一项非空、可同时使用但不得相交；未提及不表示不存在。
- 非 dry-run 只创建不存在的卡片，不覆盖或更新已有文件。
