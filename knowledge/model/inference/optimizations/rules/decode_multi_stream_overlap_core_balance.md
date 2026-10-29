---
type: Optimization
title: Decode 多流控核平衡：LongCat 双重路径拖尾的优化规则
description: Atlas A3、GE 图模式下，LongCat Decode 的 Attention/Dense 与 MoE 双流出现拖尾时，依据剖析调整两流核数；固定配比和收益边界只属于该实现，Indexer 前处理切流另见独立案例。
tags:
- task.optimization
- topic.attention
- topic.mixture_of_experts
- topic.graph_execution
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/docs/models/longcat-flash/longcat_flash_optimization.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/models/longcat-flash/models/modeling_longcat_flash.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/models/longcat-flash/README.md
  role: constraint
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/d739fecb4232cc1ef69b9acce8661c34c92945e5/.agent/skills/model-infer-multi-stream/examples/longcat-flash-multi-stream-limit-core.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/d739fecb4232cc1ef69b9acce8661c34c92945e5/.agent/skills/model-infer-multi-stream/examples/indexer-prolog-multi-stream.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/124
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/351
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-23T03:56:00Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      objective:
      - latency
      - tpot
      model_features:
        all_of:
        - moe
      execution_mode:
      - ge_graph
---

# Decode 多流控核平衡：LongCat 双重路径拖尾的优化规则

## 适用场景

已为 Decode 的 Attention/Dense 主路径与 MoE 旁路启用[多流并行](../../concepts/techniques/multi_stream.md)，两条路径都较重，但剖析仍显示明显拖尾、单步关键路径没有相应缩短。此时检查分核是否失衡，再考虑调整核数。

已核验实现为 Atlas A3 上的 LongCat-Flash GE 图模式实践。本卡 `platforms` 与 Scope 只覆盖该主结论；它们不替 Indexer Prolog 机制参考声明平台或执行模式。Scope 匹配仍须结合正文中的模型、版本和实现边界判断是否可以迁移。

## 问题信号

- 一条流长时间运行，另一条流已结束；虽然出现 overlap，双流汇合前仍有明显等待。
- 官方 LongCat 文档指出，多流时可能由一个流占用全部核，限制另一流的算子并行度。该解释是排查方向，不能只凭拖尾就排除工作量差异、通信或同步依赖。

## 优化规则

先确认两条路径的数据依赖允许重叠，再用 `limit_core_num` 为主流、副流分配 AI Core 与 Vector Core。依据双流时长和整体 Decode 时延迭代，避免一条重路径长期拖尾。

核数配置属于具体模型和负载下的调优参数。双流时长接近只是中间信号，最终应确认关键路径缩短、端到端指标改善且精度满足要求。

## 机制

固定模型源码在 `(enable_multi_stream > 0) and not is_prefill` 时进入 `multi_stream_forward`。`npu_stream_switch(True, "1")` 将 shortcut MoE 放到副流，Attention/Dense 主路径在另一套核数限制下执行，最后汇合两条路径结果。

同一函数还包含可开关的[权重预取](../../concepts/techniques/weight_prefetch.md)和 [SuperKernel](../../concepts/techniques/superkernel.md)。源码证明它们与分流、控核同时存在；来源没有逐项消融实验，不能据此认定每项都是收益的必要条件。

## 实施要点

固定模型提交 `0640521a817001f560fc30617acad41af585dfe1` 的核数配置如下；表中参数仅为该实现的参考值，不作为其他模型或负载的默认值。

| 配置 | 副流 MoE：AI Core / Vector Core | 主流 Attention/Dense：AI Core / Vector Core |
|---|---|---|
| `enable_multi_stream=1` | 8 / 16 | 16 / 32 |
| `enable_multi_stream=2` | 12 / 24 | 12 / 24 |

官方优化文档描述 Stage1 不控核、Stage2 采用主流 c16v32 与副流 c8v16。源码中的 `=2` 分支是另一套固定配置，不代表已经测得更优收益。

逐项核对数据依赖、分流位置、核数以及预取和 SuperKernel 开关。SuperKernel 的标定范围应与分流、分核范围一致，不能机械复制其他模型的 scope。

后续提交 `d739fecb4232cc1ef69b9acce8661c34c92945e5` 的 LongCat Skill 示例增加了 `not self.enable_afd` 条件。它与上述模型源码属于不同提交、不同证据形态，不把两段内容拼接成同一份已核验实现。AFD 部署需另外核对来源与拓扑。

## 收益

来源定性描述了让双流计算时间接近、减少拖尾的目标，没有给出“仅调整核数”或“仅打开多流”的受控前后对比。本次只做来源和代码静态核对，没有执行模型、真机测试或独立性能复现。

官方文档的整模型 benchmark 同时包含 MTP2、perfect EPLB 等配置，不能归因为本条规则；本卡不将该总收益作为控核收益。

## 代价和风险

- 控核使单条流只能使用部分核；副路径很轻时，分核可能限制主路径，整体反而变慢。
- 分流改变了调度与同步关系。隐藏依赖、输入尚未就绪或汇合点错误可能导致编译、执行或精度问题。
- 其他模型、负载、量化或部署拓扑需要重新剖析。固定常量不是通用配比；也不能将同卡分核规则直接用于 AFD。

## 回退方式

在该固定实现中，将 `enable_multi_stream` 设为 `0` 会绕过 `multi_stream_forward`、回到普通前向分支。这是源码可见的回退入口，未在本次操作中执行验证。回退后还应核对预取、SuperKernel 等开关组合、图编译状态和输出一致性。

## 验证方法

以下是迁移时应执行的验证方法，不是本次已完成的实验：

1. 固定模型、硬件、软件版本、量化、并行拓扑、batch、序列长度和并发，保留原始配置及剖析记录。
2. 在依赖与开关组合合法的前提下，对比原配置与调整核数后的配置，记录两流时间线、overlap、尾部等待和 Decode 关键路径；需要分析其他开关时单独设计对照。
3. 校验输出精度，同时比较预先约定口径的 Decode 单步时延或 TPOT；记录 warmup、重复次数与波动。只有 overlap 增加而端到端指标未改善，不能判为有效优化。
4. 出现编译失败、精度偏差或性能回退时，使用回退入口复核；保留失败配置与观察，不只记录成功结果。

## 适用边界

- 主结论证据限定 Atlas A3、LongCat-Flash、Decode 和 GE 图模式的固定实践；没有确认跨平台、其他模型或其他图后端的同等适用性。
- 固定来源文档当时声明不支持 `acl_graph`，不将此历史限制外推为当前所有版本的能力。
- 不为上下文、batch 或并发添加未经来源支持的定性 Scope 值，也不在本次补写版本字段或 `verified` 事件。

### 机制参考：Indexer Prolog 子链切流

保留该参考用于理解另一种切流粒度。固定 Skill 示例把 `q_b` 与 RoPE 放在 tagged stream `"22"`，把 `weights_proj` 放在 `"33"`，通过 `npu_wait_tensor` 及带条件的 tagged event 表达依赖；其开关包含 `not is_prefill`。流号与 API 组合属于示例细节，复用前应检查依赖、流编号和事件生命周期。

该历史 Skill 示例具名引用 DeepSeek-V3.2-Exp、GLM-5，但未声明硬件平台，单凭示例不能确认平台。后续按固定模型源码、README 与配置核对的 [A3 Indexer 前处理多流案例](../cases/indexer_prolog_streams_fixed_implementation.md)单独记录其平台依据、Decode 门控和两种后端的同步差异。消费这条实现时应读该案例，不能把 LongCat 的 GE 范围或双流核数转给它；本卡 Scope 仍只覆盖 LongCat 主结论，也没有新增 Indexer 性能复测证据。

## 相关经验

- [图模式多流跨流同步](graph_mode_multi_stream_cross_stream_sync_api.md)：核对所用图后端的同步表达方式。
- [Attention-FFN 解耦部署](afd_attn_ffn_disaggregation.md)：对比改变部署拓扑后解除同卡控核约束的场景，具体结论仍以该卡来源为准。
- [共享专家 Decode 双流重叠](moe_shared_expert_decode_dual_stream.md)：另一种双流骨架，不继承本卡固定核数。
- [Decode 权重预取调度](decode_weight_prefetch_ordering.md)：需要进一步分析预取时按其边界取证。
- [Indexer Prolog](../../concepts/kernels/indexer_prolog.md)：前处理机制入口；具体多流实现的平台依据见独立案例。

## Evidence

- S1：[LongCat 优化文档](https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/docs/models/longcat-flash/longcat_flash_optimization.md)，固定提交 `0640521a817001f560fc30617acad41af585dfe1`。核对全文中的 Atlas A3 范围、静态图限制、多流控核、预取、SuperKernel 及整模型 benchmark 限制；作为主结论的文档证据。
- S2：[LongCat 模型源码](https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/models/longcat-flash/models/modeling_longcat_flash.py)，同一提交，`LongcatFlashDecoderLayer.__init__`、`forward`、`multi_stream_forward`（约 L1048–L1238）。静态核对 Decode 门控、两组核数、分流/控核、预取与 SuperKernel；没有执行源码。
- S3：[LongCat README](https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/models/longcat-flash/README.md)，同一提交。核对 Atlas A3 产品声明和整模型测试环境，未据此产生独立复测结论。
- S4：[LongCat 多流控核 Skill 示例](https://gitcode.com/cann/cann-recipes-infer/blob/d739fecb4232cc1ef69b9acce8661c34c92945e5/.agent/skills/model-infer-multi-stream/examples/longcat-flash-multi-stream-limit-core.md)，提交 `d739fecb4232cc1ef69b9acce8661c34c92945e5`。仅作为 LongCat 拖尾、调参风险和带 AFD 条件写法的补充示例，未与 S2 混为同一实现。
- S5：[Indexer Prolog Skill 示例](https://gitcode.com/cann/cann-recipes-infer/blob/d739fecb4232cc1ef69b9acce8661c34c92945e5/.agent/skills/model-infer-multi-stream/examples/indexer-prolog-multi-stream.md)，同一后续提交。仅作为子链切流机制参考，示例自身没有平台声明；模型源码证据另由独立案例维护，不进入本卡主结论 Scope。
