# 使用知识库查询 API

## 目标

通过知识库检索替换 cannbot 基于 skills: ascendc-docs-search 逐文件翻目录的 API 查询方式，让 agent 更高效地找到需要的 API 信息。

## 适用场景

- 开发AscendC算子（如 foreach_addcdiv_scalar、rms_norm）时需要确认 API 签名、参数含义或平台支持情况
- 问题涉及具体开发硬件平台（910B/910B2/950 等）
- 需要同时查看签名、参数、约束、示例和使用方法

## 不适用场景

- 知识库索引不可用或对应 API 未收录

## 前置条件与输入

- 知识库索引可用且已编译（BM25F 倒排索引，4000+ 知识卡）
- 明确的 API 名称和关键约束（如 `Div count 对齐`）
- 目标平台标识（如 `a2`、`a3`、`950`）
- `knowledge-query` Skill 或 `knowledge_query.py` 可用
- Ascend C 专用流程使用与 Query 同装的 `ascendc-api-knowledge-query`；需要本机头文件证据时提供当前工程的 CANN 版本和包路径，详细定位流程以该 Skill 为准。

## 步骤

1. **构造查询。** 直接使用"实体 + 关键约束"，例如 `Div count 前n个元素`。不要在 query 里塞"帮我看看参数签名"这类填充词——去掉它们，召回立刻翻倍。
2. **执行查询。** `knowledge_query.py --knowledge-root <仓库> search --query "<实体> <约束>" --technology ascendc --type apis --platform <平台>`。
3. **选择候选卡。** 根据标题、摘要、路径和状态选择要阅读的卡片。优先选择平台匹配、状态为 `stable` 的卡片。
4. **打开卡片正文。** 阅读完整保留的官方文档正文，包括签名、参数含义、约束条件、示例和平台范围；再沿正文中的普通链接查看相关算子设计卡，并核对目标卡中的调用证据。不要直接使用搜索摘要作答。
5. **核对来源。** 确认来源确实支持准备采用的结论。如果多张卡片冲突，先比较它们的平台、版本和来源。
6. **补搜未定位卡。** 精确 API 名在目标平台的 stable 查询零命中时，单独执行 `knowledge_query.py --knowledge-root <仓库> search --query "<API 名>" --technology ascendc --type apis --match literal --include-unlocated --status draft`。该结果只能说明官方卡已入库但平台尚未定位，必须阅读正文或固定来源确认目标平台；不要和主查询使用同一 receipt。
7. **降级路径。** 未定位 draft 补搜仍未命中时，降级到官方来源核对原文。

## 预期产物

一个带结论、适用范围、依据和限制的回答，例如：

```text
结论：<API 签名和参数说明>
适用范围：<平台、版本和其他条件>
依据：<使用的知识卡和来源>
限制或冲突：<不适用情况或不同结论>
仍需验证：<源码、实验或性能分析>
```


## 效果对比

我们收集了一个 75 条的测试集（都是真实cannbot进行算子开发过程中查过的 API 需求），每个查询单独开一个会话（避免上下文干扰），让 agent 分别用 cannbot 原生 skill 和基于知识库的 knowledge-query skill 两种方式查询，记录：平均耗时、回合数、工具调用、token 用量。

### 第一轮：deepseek-v4-flash

| 指标 | docs-search（baseline） | knowledge-query（本仓库提供的 skill ） |
|---|---|---|
| 平均耗时 | 47.4s | **32.6s** |
| 回合数 | 7.8 | **6.3** |
| 工具调用 | 11.2 | **8.7** |
| token/条 | 33.5K | **27.6K** |

### 第二轮：glm-5.2

| 指标 | docs-search（baseline） | knowledge-query（本仓库提供的 skill ） |
|---|---|---|
| 平均耗时 | 58.3s | **44.9s** |
| 回合数 | 7.7 | **6.0** |
| 工具调用 | 11.2 | **8.1** |
| token/条 | 33.3K | **26.8K** |

### 第三轮：minimax-m2.7

| 指标 | docs-search（baseline） | knowledge-query（本仓库提供的 skill ） |
|---|---|---|
| 平均耗时 | 131.9s | **69.3s** |
| 回合数 | 9.2 | **5.8** |
| 工具调用 | 10.2 | **5.1** |
| token/条 | 56.1K | **46.8K** |

说明：以上结果不体现模型能力，耗时等差异主要体现在测试时段（峰谷模型调用耗时不同）。

### 重合度分析

同一批查询，两套方式查到的结果高度一致，内容重合率 **>96%**.
不一致的基本不是"谁查错了"，而是两套语料**组织粒度不同**：同一 API 在官方文档是独立文件、在知识库是经过知识编译后的聚合卡；或者 reg 版和 memory 版归属不同。整体上两套查法给出的是同一批正确文档——说明 knowledge-query 在更高效的同时没有牺牲准确性。

### 实验总结

基于上述实验结果，knowledge-query 可以在保证检索质量不下降的基础上提升 API 查询效率，减少反复查找与上下文切换：

- 速度更快：端到端查询耗时降低 15%以上 ，节省时间
- 更省轮次：少跑1～2轮工具调用，规避反复路径猜测；
- token消耗降低：平均单条查询节省 5K token。

## 验证方式

- 命中卡的路径 Profile 是 `apis`，平台包含目标平台，生命周期满足当前查询条件。
- 正文中的签名、参数、约束和版本边界能分别回到 `sources` 核验。
- 使用仓库的检索回归验证代表性 API 查询。

## 失败或停止条件

- 索引缺失、损坏或 stale：停止查询，请维护者重建索引。
- 目标平台 stable 查询和未定位 draft 补搜都零命中：报告知识缺口，不把它解释为 API 不存在。
- 候选平台、版本或来源互相冲突：停止给出确定性结论，先核对固定来源或目标环境。


## 相关规则和延伸阅读

- [知识库用户指南](../docs/user_guide.md)
- [`knowledge-query` Skill](../.agents/skills/knowledge-query/SKILL.md)
- [`ascendc-api-knowledge-query` Skill](../.agents/skills/ascendc-api-knowledge-query/SKILL.md)
