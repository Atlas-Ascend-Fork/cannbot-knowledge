# MCP 工具参考

本文是三个只读工具的逐参数参考与典型调用流程；服务器启动、传输、认证与部署见 [README.md](README.md)，各客户端配置样例见 [MCP_CONFIG.md](MCP_CONFIG.md)。参数语义以 `server.py` 为唯一事实源，本文与其逐字段对照维护。

三个工具共享以下纪律：

- **只读**：不写知识仓、不写 receipt 或 artifacts,调用日志只落仓外目录；
- **平台 fail-closed**:`platform` 可选,但省略且无环境变量缺省时 `search` 会报错并指导补参,而不是静默混合各平台结果——这是设计行为,不是故障;
- **返回定位符,不是答案**:`search` 返回候选卡定位符,任何结论必须建立在 `read_card` 读到的卡片全文上。

## discover

无参数。首次接入一个知识仓时先调用它,返回各维度真实覆盖计数与索引 provenance。

- 是最便宜的端到端健康检查:调用成功即证明知识根与检索索引有效且新鲜;
- 各维度计数证明注册覆盖,**不证明**某个具体组合(如某平台×某算子)已有卡片。

返回结构(节选,真实输出):

```json
{
  "schema_version": "knowledge-discovery.v1",
  "cards": 8982,
  "domains": { "common": 21, "contrib": 579, "model": 507, "ops": 7359, "runtime": 516 },
  "technologies": { "ascendc": 7300, "triton": 496, "training": 86, "...": "..." },
  "types": { "API": 3633, "Concept": 238, "Guide": 1247, "Runbook": 2210, "...": "..." },
  "profiles": { "apis": 3633, "guides": 1247, "runbooks": 2210, "...": "..." },
  "statuses": { "deprecated": 26, "draft": 2817, "stable": 6139 },
  "index": {
    "schema_version": "cannbot-knowledge-index.v1",
    "index_version": 3,
    "content_fingerprint": "0047983f...",
    "card_count": 8982,
    "built_repository_state": { "commit": "dc00ca6e...", "dirty": false }
  }
}
```

`index.built_repository_state.commit` 是构建索引时的仓库提交;索引相对当前提交过期时工具会拒绝服务(fail-closed),见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)。

## search

返回排序后的候选卡列表。每条结果含 `rank / score / match_basis / path / title / description / status / platforms / tags / sources(最多两条)`;**`path` 是后续 `read_card` 的句柄**。

### 参数

| 参数 | 类型 | 必填 | 默认 | 语义 |
|---|---|---|---|---|
| `query` | string | 是 | — | 检索词。`match=literal` 时**整串原样匹配**(不是多词 AND);默认 `text` 按词法相关性排序并带短语加成 |
| `platform` | string[] | 否* | — | 目标平台。合法值:`a2 / a3 / 950 / 310p / 910 / kirin_x90 / kirin_9030 / agnostic`;多值 AND(要求卡片同时支持全部);未知值直接拒绝。*省略且无缺省平台时报错指导补参(fail-closed) |
| `match` | string | 否 | `text` | `literal`(整串原样匹配,适合确切 API 名/类名)或 `text`(词法相关排序,适合概念性问题) |
| `limit` | int | 否 | — | 返回条数上限。从 5 起步,目标没找到再逐步调大;`count` 是本次返回条数,不是全库匹配总数 |
| `decision` | string | 否 | — | 本次检索支持的决策的一句话说明;只进审计日志,不影响排序 |
| `domain` | string | 否 | — | 知识域过滤:`ops / model / common / contrib / runtime` |
| `technology` | string | 否 | — | 技术过滤:`ascendc / triton / tilelang / catlass / platforms / ...` |
| `type` | string | 否 | — | 知识类型(路径 Profile):`apis / operators / guides / examples / optimizations / runbooks / glossaries` |
| `task` | string | 否 | — | 任务维度:`design / implementation / debugging / optimization / testing / migration / lookup` |
| `tag` | string[] | 否 | — | 已注册主题标签过滤;多标签 AND |
| `status` | string | 否 | `stable` | 生命周期:`stable / draft / deprecated / all` |
| `include_unlocated` | bool | 否 | `false` | 包含未声明平台的 draft 卡(要求 status 为 draft 或 all;不能与 platform 同用) |
| `include_shared` | bool | 否 | `false` | 包含跨技术 shared 卡(要求显式 technology) |
| `source_technology` | string | 否 | — | 互操作卡按来源技术过滤 |
| `target_technology` | string | 否 | — | 互操作卡按目标技术过滤 |

所有过滤参数与知识仓 CLI 一一映射,零默认值注入、零参数改写(除 `platform` 在 CLI 侧的 `.cannbot/knowledge.env` 缺省回退)。

### 返回示例(节选)

```json
{
  "schema_version": "knowledge-search.v5",
  "request_sha256": "82fa529b...",
  "query": "DataCopy 对齐要求",
  "match": "text",
  "count": 2,
  "results": [
    {
      "rank": 1,
      "score": 21.2,
      "path": "ops/triton/apis/ir/memory_management/memory_alignment",
      "title": "内存对齐 Memory Alignment(...)",
      "description": "NPU 硬件对齐约束的编译期保障:...",
      "domain": "ops", "technology": "triton", "type": "API",
      "status": "stable", "trust_tier": "unverified",
      "platforms": ["950"],
      "sources": [ { "resource": "https://gitcode.com/...", "role": "implementation" } ]
    }
  ],
  "index": { "...": "同 discover 的 index 块" }
}
```

零命中是合法结果:换关键词、放宽过滤或提高 limit 重试;仍零命中则如实报告,不要编造结果,也不要用其他平台或 DSL 的卡片替代。

## read_card

读取一张知识卡的全文证据。`path` 用 `search` 返回的 `path` 字段(带不带 `.md` 均可;前导 `/` 按 Bundle 根解析)。

### 参数

| 参数 | 类型 | 必填 | 默认 | 语义 |
|---|---|---|---|---|
| `path` | string | 是 | — | Bundle 相对卡路径,即 search 结果的 `path` |
| `offset` | int | 否 | `0` | 0 起行号分页;frontmatter 行计入。**续读永远传上次返回的 `next_offset`**——它是游标,不是行号 |
| `limit` | int | 否 | `200` | 本次最大返回行数;超过 500 截断为 500 |

### 返回(节选)

```json
{
  "path": "ops/triton/apis/ir/memory_management/memory_alignment",
  "title": "...", "type": "API", "status": "stable",
  "card_sha256": "b7573516...",
  "total_lines": 74, "offset": 0, "returned_lines": 74,
  "truncated": false, "next_offset": null,
  "content": "整卡原文(含 frontmatter,按行分页)",
  "frontmatter": { "type": "API", "title": "...", "platforms": ["950"], "...": "..." },
  "sources": [ "frontmatter 中的完整 sources 列表" ],
  "source_headers": [ "Ascend C 头文件证据(存在时)" ],
  "links": [ { "text": "...", "path": "已解析为 read_card-ready 路径" } ],
  "images": [ "正文图片引用" ],
  "index": { "...": "同 discover 的 index 块" }
}
```

- `truncated: true` 时用 `next_offset` 续读,读到 `truncated: false`;
- `sources` / `source_headers` **只报告不抓取**:需要声明原文或实现时另行获取;
- `links` 已解析为可直接作为 `path` 传入 `read_card` 的路径,可作下一跳;
- stdio 模式额外返回 `local_only`(本地卡片绝对路径、sources 根与头文件根;HTTP 模式不返回,保持 `response_sha256` 跨实例稳定)。

## 典型流程:查 950 平台 DataCopy 的对齐要求

一次完整的「确认平台 → 检索 → 读卡 → 续读/深读」:

```
1. discover                              # 健康检查 + 确认覆盖
2. search(query="DataCopy 对齐要求",
          platform=["950"],
          limit=5)                       # 定位候选卡
3. read_card(path=<第2步 rank=1 的 path>) # 读全文(默认 200 行)
4. truncated=true → read_card(path, offset=next_offset)
   或:沿 read_card 返回的 links 继续读相关卡
```

搜索技巧:

- 查**确切 API / 类名 / 宏**用 `match: literal`(整串原样匹配,不要把多个词当必然短语);
- 概念性、多约束问题用默认 `text`,把准确 API 名或首发错误信号放进 query;
- `stable` 之外的生命周期卡(draft/deprecated)需要有明确理由再查;
- 结果排序不能代替声明核对:同名 API 不同家族时按返回的完整声明区分。

## 错误分类(error_kind)

工具失败按 `error_kind` 结构化返回,完整症状→处置对照见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md):| error_kind | 含义 |
|---|---|
| `platform_missing` | search 缺平台参数且无缺省,报错指导补参(fail-closed) |
| `index_missing` / `index_stale` | 索引缺失/过期,拒绝服务,交由维护者重建 |
| `path_not_indexed` | read_card 的 path 不在索引中;用 search 获取有效路径 |
| `path_out_of_bundle` | 路径越界(Bundle 根之外) |
| `invalid_argument` / `offset_out_of_range` | 分页参数非法 |
| `subprocess_timeout` | CLI 子进程超时(默认 30 秒)被杀 |
| `cli_error` | 其他 CLI 失败 |
| `internal` | 服务器内部错误 |
