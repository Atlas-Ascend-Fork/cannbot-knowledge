---
name: model-knowledge-trace-ingest
description: 从一批 Agent 运行轨迹中提取模型训练/推理优化、框架适配及相关环境调试知识，归一化后跨轨迹归并为模型 Runbook。适用于 Codex、Claude Code、OpenCode 或其他 Agent 的本地导出、日志和事件流。
---

# Agent 轨迹中的模型知识摄入

由加载本 Skill 的 Agent 对一批轨迹执行 **normalize → mine → curate**。输入来源与 Agent 客户端无关；先转为统一事件，再按证据提取模型与框架知识，最终写入 `knowledge/model/<route>/runbooks/`。

本 Skill 的脚本只负责本地数据转换、批次准备和确定性校验。远端获取、全量初筛、客户端调用与并发由调用方管理；来源中的命令作为历史证据，不执行。

## 1. Normalize：统一轨迹

先读[归一化接口与事件格式](references/data-processing.md)。原始 JSON、JSONL、消息导出和文本记录都从此进入：

- 自动识别常见的消息、内容块和事件封装，不以某个项目、存储服务或会话路径判断格式。
- 其他 Agent 的结构化记录通过声明式字段映射接入；不能确认角色的转写、未知块和不完整记录保留原文并记为 unknown，不猜测工具观测或成功状态。
- 保留会话及显式父子关系、事件顺序、工具 call id、完整正文与来源锚点；按[脱敏流程](references/privacy.md)清理凭据、身份和私有路径，单独记账，不截短长输出。累积消息快照使用显式 snapshots 模式，只消除继承前缀，保留真实重复回合。
- 验证规范化文件、来源清单和事件覆盖；已有快照不可覆盖。工具生命周期 completed 不等于成功；读取 outcome、原始结果元数据与 limitations，非零退出码、截断或未知状态不能构成修复成功。父消息与父会话分别保留，不从 parentID 猜会话关系。归一化成功不代表语义已读或知识有效。

批量输入读取[批处理接口](references/batch-processing.md)：接收一组目录或清单，离线 normalize 后 prepare。已符合统一事件合同的输入可以先 verify 再 prepare；旧的其他格式须重新 normalize。单来源是一个元素的批次，不把多轨迹输入拆为逐轨迹 Agent 任务。

## 2. Mine：批量挖掘

按[范围边界](references/scope-policy.md)与[挖掘方法](references/mining.md)，在多轨迹窗口中先还原各自的目标、环境、尝试与客观结果，再按问题和机制聚类，形成跨来源候选。

1. 只采纳模型训练/推理优化、框架开发适配及服务于这些场景的环境调试调优知识。混合输入中的无关内容明确标 out_of_scope；未知或缺上下文内容保留 deferred。
2. 大批次优先用引用目录定位候选，再按[批处理接口](references/batch-processing.md)生成有界证据包，一次读取多事件和调用/返回上下文。完整阅读采用的机制与验证单元；其他区间如实记未读。小批次可用连续阅读视图，单事件 reader 仅作精确补证。
3. 按修复配方、诊断规则、失败边界或已验证模式组织候选；一个候选可引用多条轨迹。不同会话和实验不得拼成虚构闭环，同源副本不增加复现次数。
4. 采用的结论回原文核对完整机制单元与客观信号。性能改善须有可比基线；用户叙述、Agent 判断和工具观测分别标注。诊断和失败知识不以成功 after 为前提。
5. 输出一份批级候选 `manifest.json`、草稿和 `batch-report.json`，覆盖每条输入的 mined/no_knowledge/out_of_scope/deferred 去向。运行批级 check；它不代替真实语义阅读。

不先为每条轨迹生成完整报告再合并。窗口超出上下文时延续批级候选索引、证据锚点与未决项。调用方要求文件包时按[文件包协议](references/file-bundle.md)返回，由其离线展开并校验。

## 3. Curate：策展与落库

按[证据合同](references/runbooks-contract.md)和[策展流程](references/curation.md)，对问题簇查重，决定创建、更新、合并、拒绝或暂缓。用确定性策展入口保留 claim 类型、完整性能对比和来源编号；删减结论须显式说明去向并同步正文。准备重建、账本和最终待审字节，不靠缩短引文修复证据缺口。

需要发布的卡由实际独立审查者按[审查要点](references/reviewer.md)复核标题、摘要、正文及完整机制，审查绑定冻结内容；语义问题不能降为 minor 后通过。没有独立审查能力就交付待审产物。修改正文、实质账本或重建后重新审查，脚本不能产生语义批准。

冻结与写入前按[公开检查](references/privacy.md)对整批卡和受影响导航复查；检查失败不能冻结、批准或发布。自动检查不证明脱敏完备，独立审查仍须检查上下文中的身份和敏感信息。

真实审查通过后由执行 Agent 按仓库合同写入已核对的卡片，创建不覆盖、更新核对旧内容 hash；统一补齐导航、日志、Lint、索引与目标查询验证。原始轨迹和取证账本留在调用方工作目录，不进入公开知识正文。运行与复现方式见[离线验证](references/validation.md)，固定样本、实际产物与独立审查记录见[语义对照实验](references/semantic-evaluation.md)。
