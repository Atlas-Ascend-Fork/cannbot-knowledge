---
type: Guide
title: vLLM Ascend 功能组合裁决：成熟度、两两矩阵与专用约束
description: 裁决通用成熟度、350个两两兼容声明与PP/细粒度TP/EPLB/量化条件；核对 KVPP 中文译文的 eager/PIECEWISE、Ascend STAIR 与旧PO边界，按英文、专用指南和启动校验约束Agent配置。 核对PCP的FULL_DECODE_ONLY与FULL_AND_PIECEWISE图模式，区别于被禁止的FULL。
tags:
- task.design
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/feature_matrix.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_features.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/pipeline_parallel.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/Fine_grained_TP.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/context_parallel.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/expert_parallelism_load_balancer.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/support_matrix/feature_matrix.po
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/support_matrix/supported_features.po
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/generate_zh_docs.py
  role: implementation
created_at: '2026-10-29T12:30:02Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T21:17:47Z'
aliases:
- PCP 图模式 FULL_DECODE_ONLY 与 FULL_AND_PIECEWISE
---

# vLLM Ascend 功能组合裁决：成熟度、两两矩阵与专用约束

## 先区分三个支持维度

固定Ascend提交的通用功能成熟度、功能两两兼容表、模型×硬件单项表分别回答不同问题。Functional是上游成熟度声明，不是任意模型/平台/组合都验证；两两✅不能合成为三项以上全开。Agent的结果必须包含版本、硬件、模型、Runner、P/D角色、量化布局和实际图模式，未知项不得填成支持。

本卡涵盖通用表23项及两两表350个有值单元的裁决。整项功能的硬件产品范围未在此矩阵细分，platforms保持未知；查询具体硬件时用[模型支持裁决](../models/vllm_ascend_model_support_resolution.md)及对应专用指南，不能将“Ascend”一词扩为全部产品。

## 通用功能成熟度及下一步含义

| 上游成熟度 | 功能 | 消费限制 |
| --- | --- | --- |
| Functional（17项） | Chunked Prefill、APC、投机、多模态、LogProbs、Prompt LogProbs、Async output、Guided Decoding、TP、PP、EP、DP、PD、量化、Graph Mode、Sleep Mode、CP | 需继续核对模型、布局、拓扑及专门限制 |
| Experimental（5项） | LoRA、Pooling、Beam search、Runtime Guard、KVPP | 接口/功能可能变化；不能提升为生产稳定承诺 |
| Planned（1项） | Enc-dec | 通用成熟度尚未承诺；不否认具体Cohere实验ASR的存在 |

来源还定义WIP和NO plan/Deprecated，但这23项中没有对应行。Pooling的V1能力依赖vLLM，并需更多模型CI；LogProbs、Prompt LogProbs、Async output和Beam也留有CI待补说明，不能把通用Functional写成本仓已跑过CI。TP下一步仍提图模式TP>4，DP文字特别提Qwen3 MoE，量化文字仍提W4A8待扩展：这些说明不能替代已更新的具体模型/量化实现，也不构造所有TP>4必然失败的硬规则。

EP的通用行区分MRv1 legacy EPLB与MRv2异步EPLB（Ascend STAIR默认策略）；PD称支持xPyD，但不解除具体模型的PD❌。Runtime Guard的detect/report/dump_kv与KVPP的non-hybrid MLA/SFA、eager/PIECEWISE限制仍需按专门指南取证。Async output与两两矩阵的异步调度是不同条目，不互换名称后推论。

## 两两表的完整比较范围

为避免把上三角空白误读为支持或不支持，下表明确每行的有限比较域。序列按下列顺序编号；某行“序列前N项”只比较这N个功能（含对角线）。该有限集合中，除后三列列出的例外外，其余单元才是来源的✅。这是一种对固定表的无损归并，不是对未来功能、其他硬件或多项组合的默认许可。PP是额外一行，比较全部25项，原表没有PP列。

1. FULL_DECODE_ONLY

2. Piecewise

3. 异步调度

4. APC

5. Chunked

6. PCP

7. DCP

8. CPU绑定

9. DP

10. PD

11. Eagle3

12. EPLB

13. EP

14. KV Cache Pool

15. LM-head TP

16. MLAPO

17. 多模态

18. Multistream MoE

19. Shared Expert DP

20. W4A4

21. W4A8

22. W8A8

23. TP

24. Weight NZ

25. KVPP

| 本行功能 | 本行比较范围 | ❌不兼容 | 🟠部分兼容 | ❔未知/TBD |
| --- | --- | --- | --- | --- |
| FULL_DECODE_ONLY | 序列前1项 | 无 | 无 | 无 |
| Piecewise | 序列前2项 | FULL_DECODE_ONLY | 无 | 无 |
| 异步调度 | 序列前3项 | 无 | 无 | 无 |
| APC | 序列前4项 | 无 | 无 | 无 |
| Chunked | 序列前5项 | 无 | 无 | 无 |
| PCP | 序列前6项 | 无 | 无 | 无 |
| DCP | 序列前7项 | 无 | PCP | 无 |
| CPU绑定 | 序列前8项 | 无 | 无 | 无 |
| DP | 序列前9项 | 无 | 无 | 无 |
| PD | 序列前10项 | 无 | 无 | 无 |
| Eagle3 | 序列前11项 | 无 | 无 | 无 |
| EPLB | 序列前12项 | 无 | 无 | 无 |
| EP | 序列前13项 | 无 | 无 | 无 |
| KV Cache Pool | 序列前14项 | 无 | 无 | 无 |
| LM-head TP | 序列前15项 | 无 | DP（注1） | PCP、DCP、KV Cache Pool |
| MLAPO | 序列前16项 | 无 | PD（注2） | KV Cache Pool |
| 多模态 | 序列前17项 | KV Cache Pool | PCP、DCP | 无 |
| Multistream MoE | 序列前18项 | 无 | 无 | 无 |
| Shared Expert DP | 序列前19项 | 无 | 无 | LM-head TP、Multistream MoE |
| W4A4 | 序列前20项 | EPLB、多模态 | 无 | EP、MLAPO、Multistream MoE、Shared Expert DP |
| W4A8 | 序列前21项 | EPLB、多模态 | 无 | MLAPO、W4A4 |
| W8A8 | 序列前22项 | 无 | 无 | W4A4 |
| TP | 序列前23项 | 无 | 无 | 无 |
| Weight NZ | 序列前24项 | W4A4 | W4A8 | DCP |
| KVPP | 序列前25项 | FULL_DECODE_ONLY、DCP | PD、KV Cache Pool | CPU绑定、DP、EPLB、LM-head TP、MLAPO、多模态、Multistream MoE、Shared Expert DP、W4A4、W4A8、W8A8、Weight NZ |
| PP | 序列前25项 | 无 | PD（注3）、Eagle3（注4） | 无 |

来源350个单元中305个✅、9个❌、10个🟠、26个❔；上三角未填单元不参与这个统计。未知/TBD不能自动启用，部分兼容若没有更具体条件也保持待验证。

- 注1：LM-head TP只在pure DP场景开启；不据“LM-head TP+DP🟠”推导任意TP/DP混合计划。
- 注2：MLAPO只在Decode阶段；PD双端不是都开启。
- 注3：PD时PP在Prefill端，Decode必须PP1。
- 注4：Eagle3+PP只支持MiniMax-M3 sparse，不能泛化到所有Eagle3模型。

## 需要继续裁决的差异与强约束

| 触发条件 | 固定来源差异 / 更具体条件 | Agent动作 |
| --- | --- | --- |
| PCP配图 | PCP指南禁止FULL，但允许eager、PIECEWISE、FULL_AND_PIECEWISE及FULL_DECODE_ONLY；本表FULL_DECODE_ONLY✅与此一致 | 保留完整枚举名；不能截成“Full”后制造冲突，也不能把Fullgraph模型列直接当FULL |
| Piecewise与FULL_DECODE_ONLY | 表将两个模式标为互斥 | 不解释为禁止显式FULL_AND_PIECEWISE模式；以实际调度模式核对 |
| PP与LM-head TP | PP表✅，专门Fine_grained_TP指南排斥PP>1；已读FinegrainedTPConfig本体未查到PP guard | 保留冲突，按[细粒度TP契约](../optimization/vllm_ascend_finegrained_tp_contracts.md)补目标调用链与验证；不凭表生成可用配置 |
| PP与Sparse KV Offload | PP指南称layerwise支持，SparseKVOffloadConfig启用时明确拒绝PP>1 | 先确认具体实现、角色与校验；不能用connector名称绕过启动拒绝 |
| EPLB与W4A4/W4A8 | 通用表为❌；MRv2专门指南却列普通W4A8 enabled、950的W4A4 MXFP enabled；W4A8 MXFP/W4A16/W4A16 MXFP rejected | 按Runner、精确权重格式、布局与硬件裁决；不把所有4bit并成一种能力，也不将enabled等同已做模型回归 |
| KVPP配图/并行/PD | 矩阵FULL_DECODE_ONLY、DCP为❌，PD及KV池为部分兼容 | 按专门KVPP门控核对eager/PIECEWISE、non-hybrid MLA、producer角色与connector；模型/CP/decoder路径不能因某个✅越过硬校验 |
| PCP配PD/多模态 | 表为✅或部分兼容，专门指南只许P端PCP；encoder-decoder、LoRA不支持PCP，V1/Hybrid connector不支持PP+PCP，Hybrid不支持DCP | 逐模型与connector取交集；PP+PCP须用受支持模型的V2 connector，PCP池化只支持AscendStore且use_layerwise=false |

EPLB指南只将W8A8的MRv2模型级NPU回归列为该级验证，其他enabled格式仍需目标配置验收；A2不支持冗余专家，两Runner的num_redundant_experts必须0。通用兼容表不能推翻这些范围。具体任务分别进入[EPLB与权重迁移](../optimization/vllm_ascend_eplb_runner_and_movement.md)、[PCP/DCP拓扑](vllm_ascend_context_parallel_topology.md)、[KVPP容量与门控](../optimization/vllm_ascend_kvpp_capacity_tradeoff.md)和[PP分区](vllm_ascend_pipeline_partitioning.md)。

## 从候选配置到可执行计划

先按任务/硬件/维护状态排除明确不合适的模型行，再记录所需功能集合，检查每对的有值声明和注释。对具体条件仍有效的❌停止该候选；粗表与专门指南不一致时先做冲突裁决。❔或无具体条件的🟠保留未知，转专门指南与实际startup门控。出现不同层级冲突时保留两份证据，不能删assert或挑一个较宽松的表解决。

完成静态交集后仍按[新模型接入验收](../bringup/vllm_ascend_new_model_onboarding.md)验证真实权重、eager精度、状态推进、图/并行和目标SLO，每加一项保存有效配置与回退。检测到强约束时回到最近验证组合。本次仅静态蒸馏，没有运行组合测试或下游Agent A/B。


## 中文翻译条目不能覆盖当前英文支持边界

固定ceac提交的feature_matrix.po与supported_features.po提供中英条目，但不能脱离当前英文源直接消费msgstr。已核对的旧条目中：EP写“upstream default policy”，当前英文行已明确Ascend STAIR；KVPP旧条目只有eager，当前英文为eager或PIECEWISE；PP旧注释块多一条仅FULL_DECODE_ONLY并保留旧脚注编号，而当前表已删该行并重新编号。Agent不得据旧翻译缩窄KVPP或错接PP注释。

generate_zh_docs.py只在英文可匹配文本上应用翻译；表格、列表等结构性换行不能套普通段落重排匹配，因此PO存在不证明旧条目进入当前页面。匹配不到的原文保留英文，fenced代码段不参与翻译。中英混排不自动意味着功能缺失；应连同固定英文、有效翻译、具体实现和专门指南裁决。此处核对的是两份PO及生成器，不声称全站翻译或页面映射全部完成。
