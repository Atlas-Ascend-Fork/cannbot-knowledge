# 路径与 Frontmatter Profile

选择目标路径或构造候选卡时读取本文件；机器事实始终以知识仓 `governance/schemas/` 和统一 Contract 为准。

## 公共字段

所有 Concept 都需要 `type`、`title`、`description`、`tags`、`status`、`sources`、`created_at`、`updated_at`。Frontmatter 是无重复 key 的 YAML mapping；不要用后出现字段静默覆盖前值。

| 路径 Profile | OKF type | 额外必填 | 允许可选 |
|---|---|---|---|
| `concepts` | `Concept` | `platforms` | `cann_versions`, `aliases`, `verified`, `replaced_by` |
| `apis` | `API` | `platforms` | `cann_versions`, `aliases`, `verified`, `replaced_by` |
| `examples` | `Example` | `platforms` | `cann_versions`, `verified`, `replaced_by` |
| `guides` | `Guide` | `platforms` | `cann_versions`, `aliases`, `verified`, `replaced_by` |
| `operators` | `Operator` | `platforms` | `cann_versions`, `verified`, `replaced_by` |
| `optimizations` | `Optimization` | `platforms` | `cann_versions`, `verified`, `replaced_by` |
| `runbooks` | `Runbook` | `platforms` | `cann_versions`, `aliases`, `verified`, `replaced_by` |
| `interoperability` | `Interoperability` | `platforms`, `source_technology`, `target_technology` | `cann_versions`, `verified`, `replaced_by` |
| `glossaries` | `Glossary` | 无 | `aliases`, `verified`, `replaced_by` |

路径选择 Profile，Profile 的 `okf_type` 生成卡片 `type`；不得手工创造另一种映射。平台无关写 `[agnostic]`，未知写 `[]` 并保持 `draft`。

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
- 卡片正文和索引中的本地 Markdown 链接只能指向同一 `knowledge/` Bundle。
- `interoperability` 只能位于同领域 `shared`，并声明不同的 source/target technology。
- `concepts`、`apis`、`examples`、`guides` 和 `optimizations` 可以增加小写 `snake_case` 主题 section。
- operator 使用 `operators/<call-mode>/<family>/<category>/<operator>.md`；`call-mode` 当前为 `aclnn` 或 `direct`。
- runbook 使用 `runbooks/<area>/<runbook>.md`。
- call mode、family、family 下的 category 和 area 的合法值从 `registries.yaml` 的 `paths` 分区读取。

## 创建脚本行为

- `--tag`、`--source`、`--platform`、`--cann-version`、`--alias` 可重复。
- `--source` 参数写入 OKF `sources[].resource`；第一项自动带 `role: primary`。来源可以是 HTTP(S)，也可以是位于 Registry 登记根目录、由固定归档获取流程提供的本地路径。
- `--verified-by` 与 `--verified-at` 必须同时出现，当前一次创建一个 event；多个 event 可在审阅后人工补充。
- `--dry-run` 输出完整 Markdown，但不创建目录、卡片、索引或日志。
- 非 dry-run 只创建不存在的卡片，不覆盖或更新已有文件。
