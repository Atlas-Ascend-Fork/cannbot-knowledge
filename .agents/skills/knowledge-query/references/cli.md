# CLI

需要组合过滤条件、解释输出或定位知识根时读取本文件。

## 知识根

Query 按 `--knowledge-root`、`CANNBOT_KNOWLEDGE_ROOT`、当前目录祖先中的 `.cannbot/knowledge.env`、仓内脚本位置依次解析知识仓。全局参数可以放在子命令前后；配置文件同时接受 `export CANNBOT_KNOWLEDGE_ROOT=...` 和不带 `export` 的形式。

## 索引

项目安装器自动验证并按需构建 `artifacts/indexes/knowledge.sqlite3`。知识仓维护者在卡片、Registry、Profile、Schema 或 Contract 变化后执行：

```bash
python3 <skill-dir>/scripts/knowledge_index.py --knowledge-root <repo> build
python3 <skill-dir>/scripts/knowledge_index.py --knowledge-root <repo> verify --level full
```

Query 只读索引；普通调用执行 quick stale check，写 search receipt 和校验 retrieval state 时执行完整内容指纹检查。缺失、损坏、卡片集合/时间戳变化或治理指纹变化都失败关闭，不退回逐文件搜索。

## Discover

```bash
python3 <skill-dir>/scripts/knowledge_query.py --knowledge-root <repo> discover [--json]
```

输出实际 Concept 总数及 domain、technology/scope、OKF type、路径 Profile 和 status 计数。结构占位目录和只有 Registry 的分类不计入覆盖。

## Search

```bash
python3 <skill-dir>/scripts/knowledge_query.py --knowledge-root <repo> search \
  --query <text> [--domain ops] [--technology ascendc] [--type apis] \
  [--task implementation] [--tag topic.data_movement] \
  --platform a2 [--cann-version 9.1.0] [--include-shared] \
  [--source-technology triton] [--target-technology ascendc] \
  [--status stable|draft|deprecated|all] [--match text|literal] \
  [--decision <id>] [-k 10] [--json|--text] [--receipt <new-json>]
```

`--type` 过滤路径 Profile ID（如 `apis`），输出中的 `type` 是 OKF type（如 `API`）。`-k`、`--k`、`--limit` 等价。Search 默认输出 JSON；`--text` 只用于人工查看。

### 过滤与匹配

- 重复的 tag、platform 和 CANN version 使用 AND。
- task 自动规范为 `task.*` 并校验 task 维度。
- domain、route、platform、tag 和跨技术端点必须注册；Profile 必须受支持。
- 普通搜索至少传一个 platform。`--technology platforms` 可在映射产品平台时不传；未定位 draft 使用 `--include-unlocated --status draft|all`，且不能同时传 platform。
- `--include-shared` 只与具体 technology 一起使用，并只附加同领域 shared。
- `text` 对 title、description、tags/aliases 和正文加权；`literal` 要求完整查询串出现在这些字段中。
- 默认 status 为 `stable`，limit 必须大于零。

### Receipt

`--receipt` 原子写入 schema、完整请求、canonical 请求指纹、知识仓状态、索引版本、语料/治理指纹、命中卡片指纹和原始结果。目标必须不存在。审计流程的 `--decision` 使用稳定 ID，并把文件放在调用方实验目录。State 校验会重新计算请求指纹，核对 receipt/result/request/index/hits 一致性；ready receipt 绑定每个 search receipt 的文件 SHA-256，outcome 校验会再次确认这些文件未变化。

每个命中包含 rank、score、Concept ID、绝对 `local_path`、正文行数、OKF type、Profile、trust tier、范围、生命周期、卡片 SHA-256 及最多两个 source。顶层 `results` 是规范字段，`hits` 是迁移兼容别名。退出码 `0` 包括零命中；非法过滤、索引陈旧、知识根不可用或 receipt 已存在时退出码为 `2`。

## 审计工具

冻结 `cannbot-retrieval-state.v1` 后校验 receipt、decision、当前索引和证据卡片，并只在全部 decision 为 `covered` 时生成 ready receipt：

```bash
python3 <skill-dir>/scripts/retrieval_state.py <absolute-state.json> \
  --knowledge-root <repo> --require-ready --receipt <new-ready.json>
```

工程验证结束后创建 `cannbot-retrieval-outcome.v1` manifest，绑定 state、ready receipt、每个 decision 的 outcome 与实验产物 SHA-256：

```bash
python3 <skill-dir>/scripts/retrieval_outcome.py <absolute-outcome.json> \
  --require-complete --receipt <new-outcome-receipt.json>
```

完整 state/outcome 形状与停止条件见[查询与证据工作流](query-workflows.md)。
