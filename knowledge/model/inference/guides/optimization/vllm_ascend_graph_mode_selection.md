---
type: Guide
title: vLLM Ascend 图优化流程：ACLGraph、Npugraph_ex 与有效配置验收
description: 结合图模式与Npugraph_ex中文设计核对有效配置、硬件门控和FX融合guard，分开验收运行时捕获、static/Super Kernel及Xlite路径。
tags:
- task.optimization
- topic.compilation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/graph_mode.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/compilation/compiler_interface.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/npugraph_ex.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/ACL_Graph.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/graph_mode.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/xlite/xlite.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/xlite/xlite_model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/npugraph_ex.po
  role: supporting
created_at: '2026-10-29T08:40:49Z'
updated_at: '2026-10-30T05:23:56Z'
platforms:
- a2
- a3
- 310p
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 图优化流程：ACLGraph、Npugraph_ex 与有效配置验收

## 适用范围与目标

本文限 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 与其 vLLM `v0.32.0` 兼容目标的图配置。目标是在正确性不退化的条件下，证明请求的图模式确实生效，并测量启动成本、稳态时延和显存。不能套用其他 executor 的 `exe_mode` 配方。

## 分清两层机制

默认图路径中，ACLGraph 使用 `torch.npu.NPUGraph` 做运行时 capture/replay；Npugraph_ex 优化 FX 图，再由 ACLGraph 捕获。`force_eager=True` 在该编译后端表示 FX 优化阶段不自行捕获，不意味着最终服务不使用 ACLGraph。另有 Xlite 可选路径，需要独立核对模型适配和配置。

固定文档描述的模式如下，最终值仍需经过平台和 Attention 检查：

| `cudagraph_mode` | 编译与运行路径 | Npugraph_ex |
| --- | --- | --- |
| `FULL_AND_PIECEWISE` | 按 piecewise 编译，运行时区分混合批与 uniform decode | 关闭 |
| `PIECEWISE` | 基本 FX 融合后由 ACLGraph 捕获/重放 | 关闭 |
| `FULL` / `FULL_DECODE_ONLY` | FX 优化后由 ACLGraph 捕获/重放 | 支持硬件上默认启用 |
| `NONE` | eager | 关闭 |

这是来源版本的默认策略，不是每个模型的有效最终模式。`_setup_compile_backend()` 回写 `additional_config`，piecewise/NONE 会同时关闭 Npugraph_ex、static 与 Super Kernel；encoder-decoder 还可能降为 PIECEWISE/NONE。显式传入 true 不足以证明生效。

## 实施步骤

1. 保存同一模型与输入下的 eager 正确性和预热后基线，确认实际[Runner](../../optimizations/rules/vllm_ascend_model_runner_selection.md)。
2. 核对 Attention 的图支持声明与 batch 条件。文档中普通 attention 支持混合批，MLA/SFA 等声明 uniform batch；不能将这些声明外推到所有 Attention 实现。
3. 检查[硬件能力](../../concepts/frameworks/vllm_ascend_hardware_profiles.md)。310P 缺少 `NPUGRAPH_EX`，配置校验会关闭对应三层优化；这不等于所有图执行方式均由该能力位决定。CP 场景的 FULL 支持与其他组合限制单独核对。
4. 选择目标图模式，保存最终 `cudagraph_mode`、编译模式、Ascend 扩展参数、capture sizes 和实际日志。SP/shared-expert-DP/DSA-CP 等路径还可能要求 capture sizes 对齐 TP；被过滤后没有合法档位会报错。
5. 在真实目标 workload 下对齐输出，再测稳态性能、捕获开销、显存与档位覆盖，不用一次启动成功替代动态输入验收。

## Static 与 Super Kernel 的增量验收

依赖为 `Super Kernel → static kernel → Npugraph_ex`。static 默认关闭；显式提供 static=true 且省略 Super 开关时，配置 validator 让后者继承 static。要只测 static，应显式关闭 Super，避免一次实验混入两项变化。

以 `additional_config.ascend_compilation_config` 配置这三项，参数名与默认/继承行为分别如下。不能只写“开启Super”而忽略所依赖的前两层。

| 配置字段 | 默认与显式控制 | 生效边界 |
| --- | --- | --- |
| enable_npugraph_ex | 支持硬件的FULL/FULL_DECODE_ONLY默认开启；其余所述模式自动关闭 | 核对平台/backend回写后的有效值 |
| enable_static_kernel | 默认关闭；显式true才请求static编译 | 依赖Npugraph_ex，不能仅由模型shape静态推断开启 |
| enable_super_kernel | 省略时跟随static；显式false可只测static | 依赖static和Npugraph_ex；显式true不绕过依赖门禁 |

只比较static时可在该配置对象中设置enable_npugraph_ex=true、enable_static_kernel=true、enable_super_kernel=false，并选择允许Npugraph_ex的有效图模式。它是固定指南配置意图，仍需核对硬件/backend与运行日志，不是本环境已执行的配方。

检查启动编译日志和 profiler：static 可看 `op_statistic.csv` 的实际条目，Super 则比较 `kernel_details.csv` 的任务数量、融合覆盖和耗时。日志只证明优化步骤被调用，不能证明所有算子融合或有端到端收益；缓存重建也应计入启动成本。

## Xlite 的独立边界

Xlite 使用单独的模型 adapter 与 token 预算。固定文档自 v0.28 起按跨 DP rank 的最大 token 数选路；所谓 decode-only 的预算并不排除能装入的小 prefill/mixed batch。full 模式预算和 ACLGraph 协同另有配置，不应把 `enforce_eager=True` 简单解释为 Xlite 运行时也被关闭。新模型须核对 adapter 支持，不能只启用开关。

## 回退与停止条件

输出不一致、重复捕获、档位不足或收益不明确时，分别撤回 static/Super 等增量项；要定位 ACLGraph 相关问题，可临时 `--enforce-eager` 并确认 Xlite 等独立路径状态。资源耗尽须结合完整错误判断，可减少 capture sizes、缩小最大档位或在允许的 uniform decode 场景选择 full 路径，不能绕过功能不兼容限制。

## Evidence

图指南给出模式与运行边界；`platform.py` 给出配置回写和组合检查；`AscendCompilationConfig` 给出依赖与硬件降级；`compiler_interface.py` 给出 FX 后端选项。本次完成静态核对，未执行图捕获或基准，不声明提速。


## Fusion pass 和运行时重放分别验收

Npugraph_ex设计把FX优化分为中间节点reinplace、输入functionalization的in-place+copy恢复，以及pattern fusion。register_replacement的example_inputs用于追踪；实际match还会重追踪，不能把示例shape当作自动硬约束。需要在extra_check中检查实际match.meta的shape/device/dtype/stream，缺信息时拒绝该match；具体旧版算子布局/scale约束见[已有融合守则](../../optimizations/rules/graph_fusion_register_replacement_guardrails.md)，不能把其v0.13数值阈值自动推广到当前所有pass。

TORCH_COMPILE_DEBUG=1可输出FX各阶段图，用于确认匹配与替换。随后仍须验证ACLGraph的桶、地址和动态参数更新；捕获成功不证明跨步重放正确，见[重放生命周期](../../concepts/frameworks/vllm_ascend_aclgraph_replay_lifecycle.md)。设计还明确Atlas300I DUO与Atlas200I Pro不支持enable_npugraph_ex，不从某个算子可运行反推图后端支持。


## 中文图模式资料与Xlite实现细化

graph_mode.po的109条有效译文已完整对照固定英文，全部非空、0fuzzy/obsolete且msgid精确匹配；源码PO对照不等于线上zh-cn/latest HTML版本映射已证明。中文TP4示例叙述出现“每节点”，英文和CLI只明确tensor_parallel_size=4及4卡示例，不据此推广成多节点每节点拓扑配方。

Xlite文档列11个architecture字符串，适配只查architectures[0]；完整身份、量化权重/RoPE/MHA/MLA/DSA缓存与缺字段warning见[新模型适配合同](../integration/vllm_ascend_xlite_model_adapter.md)。这些是上游声明与Host映射，不能补写成所有同系列新模型已验证。

所读实现把decode预算再与max_num_batched_tokens取min并向TP倍数ceil，full预算同样TP对齐；路由优先_EXTRA_CTX跨DP最大token，其次DP metadata，再本地actual。V1/V2均有Xlite runner，profile/capture旁路与DP dummy参与的区别见[运行接线](../integration/vllm_ascend_xlite_runner_dispatch.md)。C8/metadata error日志、真正raise和超预算原生回退要分别判断。

FULL等请求模式仍须按平台与backend回写后验收；原生NONE/enforce_eager和Xlite开关不能互相代替。静态/Super启动warning或调用日志只证明触发步骤，cache命中时没有warning也不能单独反证未启用；实际覆盖与收益仍以profiler、输出及对照结果为准。本次仅增加中文和Host源码解释，保留已有平台/生命周期，不新增verified或任何真机结论。


## Npugraph_ex中文API与示例限制

npugraph_ex.po的27条有效译文均匹配当前英文，包括300I DUO/200I Pro不支持enable_npugraph_ex；这一限制不能扩大成这两类产品完全不能执行任何ACLGraph。外部torchair与默认fusion列表是未在本批读取的外部入口，不当所有版本已冻结的pass/ABI清单。

固定设计的register_replacement要求search_fn、replace_fn、example_inputs，默认trace_fn=fwd_only、extra_check=_return_true。提供search_fn_pattern时，它替代search_fn作为匹配规则；不能继续假定search_fn承担同一形状约束。默认前向追踪适用于推理，不证明自动包含反向或训练正确性。

示例用FakeTensorMode建立初始图，初始(1,1,2)/float16不是实际融合的通用shape/dtype门槛；extra_check读取Match.kwargs中的x1、meta.val并在缺项时False，示例只允许最后一维7168。7168属于这个示例的guard，不是所有RMSNorm或所有新模型的全局限制。要适配其他形状、layout、stream、device和dtype，分别建立相应匹配条件与输出/别名正确性验收，不以fake trace成功代替真机融合证明。

reinplace、恢复functionalization产生的in-place+copy模式与pattern fusion是不同步骤。TORCH_COMPILE_DEBUG=1可帮助观察FX改变，但graph dump不证明替换已被真实负载执行、所有算子均融合或端到端提速；随后仍按本卡核对运行时捕获、参数更新与有效配置。本批未导入npugraph_ex/torch_npu或执行示例。
