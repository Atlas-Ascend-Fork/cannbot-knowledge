# 显式组件机器检索

通用入口直接调用注册组件的机器 skill，当前为 `ascendc-devkit` 的 `asc-search`。
调用方显式选择该路径并整理机器查询维度；普通 Query CLI 不自动调用它。
该组件的首期检索面是 Ascend C C API，不代表全部 AscendC C++/SIMT API。

## 完整 checkout 与入口

从完整知识仓 checkout 使用 Python 环境与 `requirements.txt` 中的依赖。下例中的 `<repo>` 为知识仓根，
`<query-skill>` 为该 checkout 中的 `.agents/skills/knowledge-query`，不是业务项目的数据目录。
三个子命令均支持 `--knowledge-root`、`--registry` 和 `--component`；默认根来自脚本所属 checkout，
默认注册表为根内 `governance/schemas/component_search.yaml`，默认组件为 `ascendc-devkit`。

```bash
python3 <query-skill>/scripts/component_search.py capabilities --knowledge-root <repo> --component ascendc-devkit
```

capabilities 只读取注册表，不联网、不下载、不检查机器资源或索引是否已准备。读取成功时输出
`available`、`status`、`machine_skill`、`components`、`archive` 等字段；当前未配置人类扩展，
`human_extension` 为空。读取失败返回 `available=false` 及错误；命令本身仍退出 0，必须读取 JSON。
`available=true` 只代表组件已注册且 active，不保证归档可用或文档有覆盖。

```bash
python3 <query-skill>/scripts/component_search.py prepare --knowledge-root <repo> \
  --component ascendc-devkit --platform 950 --cann-version 9.2.0 \
  --session-id <stable-agent-process-id>

python3 <query-skill>/scripts/component_search.py search --knowledge-root <repo> \
  --component ascendc-devkit --platform 950 --cann-version 9.2.0 \
  --session-id <stable-agent-process-id> --api asc_abs --dtype float --limit 5
```

prepare 下载并校验官方归档，按白名单准备机器 skill、文档、include、示例和索引。
search 按需执行同一 prepare，再调用机器检索；首次调用或缓存失效时可能联网并写入缓存。
它不要求知识卡 SQLite 索引，也不要求先运行 discover。进入普通 Query 时仍遵守原 discover 与索引规则。

prepare 和 search 的公共目标/准备参数为 `--archive-url`、`--platform`、`--cann-version`、
`--session-id`、`--refresh`。prepare 另支持 `--arch` 和 `--cache`；缓存必须位于知识根的 `artifacts/` 内。
显式目标优先，本机探测只补未指定条件；平台、版本或架构无法确认时保留 needs_context。
prepare 的显式架构若与目标平台探测结果冲突则报错。

search 的筛选参数为：

- 字符串：`--stage`、`--operation`、`--category`、`--api-class`、`--dtype`、`--kw`、
  `--feature`、`--changed-in`、`--api`、`--deps-of`、`--kind`、`--param`、`--enum`、`--gap`；
- `--convert SRC DST`、`--reverse`、`--keywords <一个或多个词>`、`--limit <整数>`。

各维度的检索语义由组件机器 skill 决定；该入口不接受自然语言问题或 JSON 过滤文件参数。
当前注册的搜索子进程设置 `ASC_SEARCH_NO_LLM=0`，固定消费机器 JSON，不改变调用方环境。

## 返回结果与调用方处理

| 命令 | 返回 | 退出码 |
|---|---|---|
| capabilities | 注册状态 JSON，含 available 或错误 | 0；参数语法错误除外 |
| prepare | status=ready，含数据根、索引目录、机器入口、目标条件、归档 SHA-256 和 coverage | 0 |
| prepare | unsupported、unavailable 或 needs_context | 1 |
| prepare | status=error | 2 |
| search | 注册 schema 的原生机器 JSON，当前为 asc-search-results/1 | 0，含合法 count=0 |
| search | 结构化失败或不可用状态，含 fallback=knowledge-query | 2 |

机器结果必须退出成功、schema 正确、results 为合法列表且整数 count 等于结果数；每条结果须包含
非空 path 或 gap_id。CLI 参数语法错误由参数解析器处理，不保证返回 JSON。

needs_context 由调用方澄清。unsupported 表示缺少机器入口、可用知识头或产品支持标记；
unavailable 表示组件未激活等；error 表示配置、网络、校验、解压、构建或机器输出失败。
`fallback=knowledge-query` 是提示，不执行原 Query，也不包含原 Query 结果。
需要回退时由调用方单独调用原查询，并保留原有平台、领域及其他明确过滤条件；组件结果与
原知识卡结果不能混成同一排序或审计链。合法零命中仍是成功结果，应按其证据边界处理。

## 缓存、来源和权限

组件注册与安全边界见[组件搜索接入](../../../../docs/component_search_integration.md)。
DevKit 默认组件缓存为 `<repo>/artifacts/ascendc-devkit`，共享归档下载位于
`<repo>/artifacts/component-search/downloads`。环境配置使用组件登记的
`CANNBOT_ASC_DEVKIT_ARCHIVE_URL` 和 `CANNBOT_ASC_DEVKIT_CACHE`；CLI 显式值优先。
归档 URL 必须是无凭据、查询串或片段的 http(s) URL，可指定目录或直接 tar.gz；
所在目录需提供 checksums.txt，清单只接受唯一 tar.gz。

快照按 SHA-256、索引按目标版本/架构复用，并绑定注册契约摘要；`--refresh` 强制刷新。
首次构建、普通缓存复用和同会话 ready 复用均检查实际索引文件、JSON、目标元数据及覆盖，
不能仅凭完成标记判定 ready。DevKit 要求 `index.json`、`build-meta.json` 和 `gaps.json`，
通过归档中的 `ensure_index.py` 的 `gate_reasons`、`light_fresh` 及 `query.load` 校验索引，
核对 `surface`、`cann_version`、`arch_label` 和 `source_commit`。
已有索引失效时只重建一次；新构建仍无效则清理失败索引并返回 error，不记录 ready。
覆盖不足仍返回 unsupported。

用同一稳定 `--session-id` 可复用 ready 元数据；也可用 `CANNBOT_AGENT_SESSION_ID`。
命中时仍执行本地完整性与新鲜度检查，通过后无需检查远端。非 ready 或损坏会话不复用，
失败不写入会话缓存。
会话文件只保留 7 天、最多 128 个，自动退化的 invocation 会话不持久化，但仍可复用资源缓存。

准备与按需准备只写 ignored 的 artifacts，不修改 tracked 文件、知识卡或 SDK；只调用注册表声明的
机器入口（包括索引验证入口）。这些检查确认本地索引完整性及其与当前归档、目标的匹配，
不证明归档真实性；下载时的 SHA-256 来自同目录 `checksums.txt`，不是仓内固定的可信摘要。
归档及索引不是 knowledge/ 的 Concept，不进入原 SQLite 索引。
原生结果必须保留其来源，阅读候选证据后再形成答案，不能据此创建原 card_sha256、receipt、ready 或 outcome。
