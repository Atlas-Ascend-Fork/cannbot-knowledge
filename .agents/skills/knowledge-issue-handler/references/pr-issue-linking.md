# PR–Issue 关联扫描

处理“Issue 看起来已经由 PR 解决、但没有关联也没有关单”的情况时读取。扫描器只读，不评论、不指派、不关单。

## 何时运行

- 批量分诊前先跑一次，把“已有合并 PR”的 Issue 从首次分析队列中分流。
- 处理单个 Issue 前，先确认是否已有 PR 或历史尝试，避免重复拟稿。
- 定期巡检时只跑扫描，人工挑出需要回复或关闭的条目。

## 命令

```bash
python3 .agents/skills/knowledge-issue-handler/scripts/scan_pr_issue_links.py \
  --repo cann/cannbot-knowledge \
  --issue-state open \
  --pr-state all \
  --output-dir .cannbot/gitcode-issue-handler/data/pr-issue-links
```

常用参数：

| 参数 | 作用 |
|---|---|
| `--issue-state open\|closed\|all` | 默认 `open`，只看未闭环 Issue |
| `--issue N` | 只扫单个 Issue：只取该条的正文与评论，PR 侧仍取全量用于反向匹配；与 `--issue-state` 互斥 |
| `--pr-state open\|closed\|merged\|all` | 默认 `all`，需要同时看已合并与进行中 |
| `--max-pages` | 单类对象最多抓取页数，默认 20 页 × 100 条 |
| `--comment-limit` | 最多读取多少条 Issue 的评论，默认 100 |
| `--from-raw DIR` | 复用 `raw/` 快照离线重跑，不访问 API |
| `--json` | 在 stdout 输出机器可读摘要 |

单条复核示例：

```bash
python3 .agents/skills/knowledge-issue-handler/scripts/scan_pr_issue_links.py \
  --repo cann/cannbot-knowledge --issue 53 \
  --output-dir .cannbot/gitcode-issue-handler/data/issue-53
```

`GITCODE_TOKEN` 可选；公开仓可匿名读取，但匿名配额低，正式巡检应提供只读 Token。Token 只从环境变量读取，不写入报告。

## 处理顺序

匹配不是对称投票，而是**按证据强度逐级下降**：上一级命中就不再进入下一级。

| 阶段 | 判定 | 说明 |
|---|---|---|
| ① 声明 | Issue 说"本 Issue 由 PR #N 修复" | 直接按该 PR 状态决定能否关闭 |
| ② 提及 | Issue 提到 PR，但没说是它修的 | 合入也只算待核对，不能据此关单 |
| ③ 反查 | Issue 完全没提 PR，由 PR 侧命中 | 需要读 diff 确认覆盖范围 |
| ④ 相似 | 两侧都没引用，只剩标题重合 | 仅作线索，永不进入可关闭清单 |

一条 Issue 一旦有①，就不再上报它的②③④——避免同一 Issue 被七八个"相关 PR"刷屏，也避免弱证据污染强证据。

### ① 声明（唯一可关闭来源）

满足任一条件即视为声明：

- `关联 PR:` / `对应 PR:` / `修复 PR:` 模板字段；
- 同一句里既有"本 Issue / 该问题"又有"已提交 / 已修复 / 已合入"等动词；
- `已提交 PR #N`、`已合入 PR #N` 这类动词与 PR 紧邻的表述。

判定只看 PR 自身状态：

| PR 状态 | 结论 |
|---|---|
| 已合并 | 可直接闭环 |
| 仍在评审 | 暂不具备关闭条件 |
| 已关闭未合入 | 声明失效，需确认是否走了其他改动 |

"已关闭"不等于"已修复"：只有 `merged_at` 非空才算合入；关闭未合入的 PR 不能作为关闭 Issue 的依据。

### ② 提及

`在 PR #68 的固定提交上构建索引`、`与已合入导航层（PR #100）互补`、`该 PR 已并入 PR #100` 都属于提及：说明了关系，没有说明"已经修好"。即使 PR 已合并，也只落到"待核对闭环"。

### ③ PR 侧反查

Issue 本身没提 PR 时，再让 PR 反向命中：

| 证据 | 置信度 | 是否闭环证据 |
|---|---|---|
| `fix/fixes/close/closes/resolve/修复/解决/关闭/关联` 后紧跟 `#N` 或 Issue 链接 | high | 是 |
| PR 正文中的 Issue 完整链接 | high | 是 |
| PR 标题以 `#N:` 开头 | high | 是 |
| 正文 `Issue #N` 提及 | medium | 否 |
| 源分支名包含 `issue-<N>` | medium | 否 |

### ④ 标题相似

两侧都没有显式引用时才启用。先剥掉 `[Bug-Report|缺陷反馈]:` 模板前缀和 `feat(scope):` 约定式前缀，再用 latin 标识符 + 中文二元组计算 IDF 加权覆盖率，要求覆盖率 ≥ 0.34、共享词 ≥ 2、且至少一个词的 IDF ≥ 1.8。阈值在 `cann/cannbot-knowledge`（79 Issue / 239 PR）上校准。

结果固定为 `low` 置信、`疑似匹配` 分类，**永远不进入可关闭清单**。

## 刻意不采用的信号

- **裸 `#N`（PR 正文）**：编号空间独立，"Depends on #15" 往往指另一个 PR，误报率高。
- **计数句**：`已合入 PR 9 个` 不是引用。
- **"已并入 PR #N" 的主语是另一个 PR**：`原 PR #99 已并入 PR #100` 说的是 PR 合并，不是 Issue 修复。
- **`本 Issue： #225` 里的编号**：`Issue： #N` 会被误读成 Issue 编号，实际是句子后接的 PR 号，需要排除前导的"本/该/此"。

模板占位符（`<!-- #123 -->`）在匹配前整体移除。

## 置信度与分类

| 分类 | 含义 | 建议动作 |
|---|---|---|
| `可直接闭环（Issue 已声明）` | Issue 声明的 PR 已合入 | 人工核对后回复并关闭 |
| `PR 进行中（Issue 已声明）` | 声明的 PR 未合入 | 等待，不重复拟稿 |
| `PR 已关闭未合入（Issue 已声明）` | 声明的 PR 关闭但没合入 | 确认是否被其他改动替代 |
| `PR 已合并，待核对闭环（Issue 仅提及）` | Issue 提到过该 PR 且已合入 | 读 PR diff 判断覆盖范围 |
| `PR 已合并，待核对闭环（PR 侧引用）` | PR 反向命中且已合入 | 同上 |
| `PR 进行中（…）` | 关联 PR 未合入 | 记录，等合入 |
| `PR 已关闭未合入（…）` | 关联 PR 已关闭 | 确认是否另有改动 |
| `疑似匹配，需人工判断` | 仅标题相似 | 只作检索线索 |
| `无需处理（Issue 已关闭）` | Issue 本身已关闭 | 仅补关联记录 |

`confidence` 只表示文本证据强度，不表示技术结论正确性。

## 输出

```text
pr-issue-links/
├── pr-issue-links.md      # 漏斗 + 四阶段分组 + 评论草稿
├── pr-issue-links.json    # 结构化结果，含 phase / evidence / classification / 时间戳
└── raw/
    ├── issues.json
    ├── pulls.json
    └── comments.json      # 供 --from-raw 离线复跑与审计
```

`pr-issue-links.json` 的 `funnel` 记录每个阶段的 Issue 数，五项之和应等于扫描总数；数量对不上说明有 Issue 被重复归类。

报告中的“评论草稿”只是文本，脚本没有任何发布能力。

## 后续动作边界

- 发布评论、指派或关闭必须另走原 Handler 的授权与回查，不能由本次扫描推导。
- 只有 `可直接闭环（Issue 已声明）` 可以作为关单候选，且仍需人工确认 PR 覆盖了全部诉求。
- 扫描结果不修改知识卡、索引、`.gitcode/`，也不写入 Issue 状态。
- 同一 Issue 可能命中多个 PR；声明阶段只保留声明本身，其余阶段保留全部组合。
