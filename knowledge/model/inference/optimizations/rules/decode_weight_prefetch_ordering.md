---
type: Optimization
title: 权重预取决策：按带宽窗口、缓存空间和消费依赖安排预取
description: 在已核验的 A3 LongCat Decode 路径中，依据带宽窗口、相邻算子搬运压力和依赖选择预取位置与范围；具体实现分别进入 LongCat 案例及平台待核验的 vLLM MoE 草稿。
tags:
- task.optimization
- topic.attention
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:24:40Z'
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
      execution_mode:
      - ge_graph
---

# 权重预取决策：按带宽窗口、缓存空间和消费依赖安排预取

## 适用场景

后续 matmul 类算子暴露权重搬运等待，而前一段计算存在可利用的带宽窗口时，考虑[权重预取](../../concepts/techniques/weight_prefetch.md)。本卡来源覆盖 Atlas A3 LongCat-Flash Decode；当前实现另有 npugraph_ex 专用预取流；Scope 和平台声明覆盖该主结论。

## 问题信号

结合时间线检查后续权重消费算子是否受搬运限制、前序计算是否留下带宽窗口。不能仅因模型权重大就判定应开启预取，也不能把两条路径的机制类比当作收益证据。

## 优化规则

- 选择发起预取到消费权重之间存在有效计算窗口的位置，核对依赖及数据生命周期。
- 同时考虑相邻算子的搬运压力和缓存空间，不为每个权重无差别预取；固定来源中的 LongCat 策略优先为搬运压力更大的 MLA_Prolog 留出空间，提前预取其前置 QBMM 权重。
- 预取范围、门控和比例属于实现与负载条件；具体参数由案例记录，不能将某实现的常量升级为通用阈值。

## 机制

预取利用前序计算期间的带宽搬运后续要消费的权重，目标是减少后续等待。LongCat 与 vLLM 的发起点、依赖表达、权重定位和开关不同；本卡集中维护选择预取窗口与缓存预算的判断，案例维护各自的实施细节。

## 实施要点

先读适用平台与实现对应的案例，再核对权重来源、发起/消费点、预取字节范围和开关。LongCat 的 `enable_prefetch` 与 vLLM 的 `weight_prefetch_config` 是不同接口，不能互换；vLLM 的单次 forward token 数也不能直接等同于 batch 或某个推理阶段。

## 收益

来源只给出减少搬运等待的定性目标，没有对本规则的独立受控前后对比。LongCat 整模型 benchmark 含其他优化，vLLM PR 的性能描述也没有独立量化数据；本卡不据此给出加速比或保证。

## 代价和风险

过多预取可能争用带宽、挤占缓存；窗口不足、依赖或权重定位错误也可能使预取无效或改变执行行为。调整后同时检查精度、时间线及端到端时延，不能只依据是否调用预取接口判断成功。

## 回退方式

按案例中的配置入口关闭对应预取能力，恢复原始配置和依赖关系后验证输出与时延。回退入口来自固定来源，本次没有执行模型或验证回退效果。

## 验证方法

固定模型、硬件、软件、量化、batch、序列长度、并发与并行拓扑，再对比原配置和仅改变预取的合法配置。记录预取发起/消费点、关键路径、目标时延指标、精度、warmup、重复次数与波动；目标指标未改善时，不把局部 overlap 作为成功结论。

## 适用边界

当前源码与来源报告限定上述 A3 LongCat 实现；平台待核验的 vLLM 案例不因引用本规则而获得 A3 或跨平台适用性。规则的 Scope 不代替案例的具体前提，不声明 Prefill 或所有 batch 均适用，也不把缺失条件写成 `any`。

## 相关经验

- [LongCat A3 Decode 权重预取案例](../cases/longcat_a3_decode_weight_prefetch.md)：记录固定模型的相邻算子排布与开关。
- [vLLM MoE 权重预取案例草稿](../cases/vllm_moe_weight_prefetch_token_gate.md)：记录 token 门控、比例和权重定位，平台仍待核验。
- [Decode 多流控核规则](decode_multi_stream_overlap_core_balance.md)：需要联合分析多流窗口时，分别核对两项优化的条件。

## Evidence

- [longcat_flash_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md)（primary）
- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（implementation）
