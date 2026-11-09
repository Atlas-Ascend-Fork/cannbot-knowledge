# 脱敏与公开自包含检查

先保护原始输入，再归一化，再审查公开卡。所有 Agent 和来源使用相同流程；不依赖存储服务、项目目录或特定账号。归一化不是匿名化证明，公开前仍需语义复核。

## Normalize：正文与元数据一起处理

原始文件只读，原始 hash 留在私有工作目录。默认 `agent.trace-redaction.v2` 对正文、JSON 工具参数、嵌套 JSON 字符串及结果元数据递归处理：

- 凭据：密码、AK/SK、API key、访问/刷新 token、Authorization、Cookie、URL userinfo 和敏感 query 参数、expect/send 密码。
- 身份与网络：结构化账号/用户信息、邮箱、SSH 登录身份、内网 IPv4/IPv6、内网域名及主机字段。
- 目录：个人 home（含字面 `~/`）、私有 work/workspace、数据/临时工作根和 Windows 用户目录。默认整条私有路径变成不含原文的占位符；不靠只换用户名保留可定位的项目树。

同一次归一化中同值用相同占位符，不同值保持可区分。输出只记版本、分类次数及是否使用调用方策略，不导出原值映射。公共 Git 固定提交链接、仓库相对源码路径、系统 `/usr`、`/opt`、`/dev` 路径、模型 token/shape/精度/指标等技术证据不因敏感字段同名而全部删除。

需要保留复现所需的相对路径时，由调用方在私有目录提供可选策略：

```json
{
  "path_aliases": [
    {"prefix": "/home/example/private_checkout", "replacement": "${PROJECT_ROOT}"},
    {"prefix": "/data/private_weights", "replacement": "${MODEL_DIR}"}
  ],
  "private_terms": ["example-private-account"]
}
```

```bash
python3 <SKILL_DIR>/scripts/trace_batch.py normalize <raw-input.json> --output <new-normalized> --redaction-policy <private-policy.json>
# 单来源也支持 normalize_trace.py ... --redaction-policy <private-policy.json>
```

前缀须为本地绝对路径或显式 `~/` 路径、替换项为变量（不执行命令或展开远端 home）；最长前缀优先，保留后缀。策略不能放入公开产物。默认规则无法推断组织内的全部敏感标识，调用方须补充 private_terms/目录映射并人工复核。真实账号/模型位置未确认可以省略，不能编造版本或工作负载来填空。

退出码、截断、错误状态及其限制须保留，脱敏不能删除这些观测，也不能让不同实验因占位符相同而合成一次运行。脱敏改变实际工件文本后，重新生成来源绑定、证据工件和审查主题；不复用旧 hash 或旧 PASS。

## Curate：公开内容不依赖私有账本

公开卡检查标题、摘要、正文、命令、日志和链接。把私有前缀改为 `${PROJECT_ROOT}`、`${MODEL_DIR}`、`${DATASET_DIR}`、`${PYTHON_ENV_ROOT}` 等有含义的变量，并在卡片中解释从何处取值，保留文件间相对关系与工作目录条件。无法确认路径角色时保持未知，不猜目录结构。

“见候选 c1”“同簇 s5-…”等内部指代不能代替参数、消融或验证。已有公开卡使用真正存在的相对 Markdown 链接；没有公开卡则把已有证据支持的必要内容写进本卡，或撤回依赖该缺失内容的结论并明确缺口。不把内部账本发布来绕过脱敏。

## 冻结和写入前：整批检查

```bash
python3 <SKILL_DIR>/scripts/audit_publication.py <repo-root> --files <changed-markdown-paths.json> --report <new-private-report.json>
```

文件清单为相对 root 的 Markdown 路径数组，包含待审卡及受影响导航；省略清单则扫描 root 下 Markdown。拒绝符号链接和路径越界，只读审计，不自动重写知识。报告只含路径、行号、类别和数量，不回显匹配值。可使用同一私有策略补充环境特有项。

`validate_model_evidence.py` 和 `review_cards.py` 的冻结及发布清单入口也检查默认规则。自动发现任一未处理敏感项或内部候选指代即失败；人工检查仍须覆盖未被规则识别的身份、连接信息和上下文重识别风险。审查发现问题后修改原产物，重跑全批校验并重新审查，不编辑 receipt 或降低 finding 严重性。
