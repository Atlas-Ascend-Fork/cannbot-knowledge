# 组件搜索接入（Component Search Integration）

knowledge-query 提供独立、显式调用的通用组件机器检索入口。组件在官方归档中提供自己的机器
skill，知识仓负责资源准备与调用，当前注册组件为 Ascend C C API 的 `asc-search`。
该入口不改变普通知识卡 Query、审计或安装器的行为，也不新增治理或可安装 Skill。
操作接口由 [Query Skill](../.agents/skills/knowledge-query/SKILL.md) 及其参考资料维护。

## 分层与职责

| 层 | 职责 | 边界 |
|---|---|---|
| 组件机器 skill | 索引构建、上下文探测、检索和原生 JSON 契约 | 随官方归档提供，不随知识仓提交 |
| 通用 provisioner | 注册表加载、归档下载与 SHA-256 校验、白名单解压、缓存、索引准备、调用及结果校验 | 不复制组件检索语义，不自动执行知识卡 Query |
| 调用方 | 选择组件、整理查询条件、处理上下文缺口、阅读证据、决定是否转入普通 Query | 外部结果不伪装为 Concept，不写入原卡片审计链 |

完整 checkout 提供规范源、相邻依赖与注册表。普通安装器仍只安装原有项目 Skill、准备原有来源和
Query 索引；不会准备组件归档。独立复制 Skill 目录不属于支持的安装方式。

## 组件注册表

[component_search.yaml](../governance/schemas/component_search.yaml) 是组件接入的唯一机器事实源。
注册表加载阶段先校验结构；格式错误在下载前停止，错误包含组件名及字段位置。

- `status: pending` 的组件不下载；只有 `active` 可准备。注册状态不等于资源已下载、覆盖已确认或索引已就绪。
- `archive` 定义官方归档目录和共享下载缓存。校验清单固定为 `checksums.txt`；
  `archive.checksums` 只能省略或采用该值，不支持全局 `archive.env`。
- `archive_prefix` 与 `extraction.paths` 决定白名单。paths 是 `{archive, kind}` 映射列表；
  `required_kinds` 指定必须获得的资源类型。
- `machine` 声明必须存在的文件及探测、建索引、搜索入口。当前 DevKit 必需文件还包括
  `scripts/ensure_index.py`、`config/product-map.yaml` 和 `config/tag-taxonomy.json`，以注册表完整集合为准。
- `cache_dir`、组件级 `cache_env` 和 `archive_env` 定义缓存位置及覆盖来源；写入仍限于知识根的 `artifacts/`。
- `index.build_command` 和 `search.command` 是带占位符的非空字符串列表；`search.schema` 指定返回协议。
  筛选维度由通用 CLI 定义，不支持 `search.filters` 配置。
- 可选的 `index.required_files` 是索引目录内安全相对 JSON 文件路径的列表；
  `index.validation_command` 是带占位符的非空字符串列表，声明组件索引验证入口。
  DevKit 要求 `index.json`、`build-meta.json`、`gaps.json`，验证入口使用归档内的
  `ensure_index.py`。这两个字段均计入已有索引缓存契约摘要，不增加 CLI 参数。
- `coverage.doc_count`、`coverage.pending_no_okf` 是非空字符串路径列表，默认还要求产品标记路径。
  只有 `require_products=false` 时可省略产品标记；不接受 pending/products 别名。

## 准备与搜索

```text
显式请求
  → 读取并校验注册表、确认组件 active
  → 解析 checksums.txt 与唯一 tar.gz，下载并校验 SHA-256
  → 按组件白名单解压，验证机器入口和必需资源
  → 探测上下文，保留显式目标优先级
  → 构建或复用目标版本、架构的索引，校验实际文件、JSON、元数据、新鲜度与覆盖
  → prepare 返回 ready；search 调用机器入口并校验原生 JSON
```

缺少目标平台、版本或架构时保留上下文缺口，不以默认架构代替。缺少机器 skill、可用知识头或
必要产品标记时报告不支持；网络、校验、解压、构建或机器 JSON 错误报告失败。
未注册或 pending 组件不会触发下载。

首次构建、普通缓存复用和同会话 ready 复用采用相同的索引有效性要求。通用检查读取实际文件，
解析 JSON，并核对注册表 `index.meta` 声明的目标元数据（包括架构和来源）。DevKit 的验证入口复用
归档内 `ensure_index.gate_reasons`、`light_fresh` 与 `query.load`，核对 `surface`、`cann_version`、
`arch_label`、`source_commit`，避免把文件缺失、JSON 损坏或索引过期当作 ready。
已有索引无效时重建一次；新构建仍无效则清理失败索引、返回 error 且不记录 ready。
覆盖不足保持 unsupported，不因完整性校验改成 ready。

搜索先运行同一准备流程，因此可能联网和写缓存。成功时直接返回组件原生 JSON，包括合法的零命中。
失败时返回结构化状态和 `fallback=knowledge-query` 提示；提示本身不执行原 Query。
调用方需要澄清上下文，或自行选择普通 Query 并遵守其 discover、索引与证据规则。
组件结果不进入原 SQLite 索引，也不参与 Concept 的 receipt/state/outcome 链。

## 缓存与隔离

- 共享下载按 SHA-256 存入 `artifacts/component-search/downloads`，组件缓存保留硬链接副本。
  组件按白名单解压到各自快照；索引按组件、归档 SHA、CANN 版本、架构和检索面隔离。
- 快照完成标记、索引旁的 `.component-contract.json` 与会话键绑定缓存契约摘要。
  摘要包含归档前缀、extraction、machine、index 与 coverage 规则，契约变化会使旧快照和索引失效；
  缺少摘要的旧缓存同样失效。
- 同一组件缓存的准备过程使用跨进程锁，支持 Unix 与 Windows。仅保留当前归档的组件下载、快照和索引。
- 稳定会话仅复用有效 ready，命中时再次核对快照、索引实际内容和新鲜度，通过后无需联网；
  失败或损坏的会话重新准备。
  会话元数据最多保留 7 天、128 个文件，在准备锁内回收。临时进程会话不持久化 ready，资源缓存仍可复用。
- 显式刷新重新准备；不会把组件资源放入共享 raw 来源根，不修改 tracked 文件、知识卡或 SDK。

## 安全与验证

归档 URL 只接受 http(s)，拒绝凭据、查询串和片段；校验清单限制大小且只接受单个 tar.gz。
解压拒绝绝对路径、路径穿越、符号链接与其他非常规成员，并限制解压体积；目录成员跳过。
机器 skill 仅调用注册表声明的入口（包括索引验证入口），其文档、include、示例不进入本仓提交。
索引校验保证本地内容完整及其与当前归档、目标条件相符，不证明上游真实性；下载摘要来自同目录的
`checksums.txt`，并非仓内固定的可信摘要。这些检查不提供归档代码的执行沙箱或环境隔离。

定向回归应覆盖注册表接受/拒绝案例、归档及解压边界、缓存复用和失效、上下文与覆盖不足、
机器 JSON 校验及多组件隔离；普通 Query 与安装器应保持原行为。测试实现与统一门禁由仓库维护。
