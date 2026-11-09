---
type: Guide
title: vLLM Ascend 设备 ABI 版本变化：量化 KeyPool 与 RoPE0 SparseAttention
description: 记录3164新增POOL_KEY_INDEXER_FP8/INT8硬件能力、A5二维NZ输入约束及q_pe=None/RoPE0/LSE的自定义SparseAttention派发，供模型后端选择与接口迁移。
aliases:
- POOL_KEY_INDEXER_FP8 POOL_KEY_INDEXER_INT8
- requires_2d_nz_linear_input
- q_pe None RoPE0 LSE custom operator
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/device/hardware_profile.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/device/device_op.py
  role: implementation
created_at: '2026-11-03T06:39:58Z'
updated_at: '2026-11-03T06:39:58Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 设备 ABI 版本变化：量化 KeyPool 与 RoPE0 SparseAttention

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`；完整变化与必要上下文静态读取，不标目标全文FULL，未执行upstream/JIT/NPU/图/通信/性能测试。

hardware_profile新增精确能力：POOL_KEY_INDEXER_FP8为CANN quant_mode0、E4M3 query/key和FP32 descales；INT8为quant_mode2及FP16 descales。当前映射A5添加FP8、A3添加INT8；不能由此认定A2或任意FP8算子都支持。同版本A5.requires_2d_nz_linear_input=True，默认False，是mm/addmm可用但batch matmul拒NZ的具体约束，GLM视觉调用据此flatten，不推广到量化Linear全体。

DeviceAdaptor SparseAttention允许q_pe=None，此时query取ql_nope.contiguous、rope dim缺省0，否则拼接两部。RoPE0或需要LSE走本仓npu_kv_quant_sparse_flash_attention_vllm，RoPE64且不需要LSE保留TorchNPU builtin。A5分支同样先计算安全rope dim，不能对None访问shape；builtin没有RoPE0合同且不返回DCP max/sum，不能换掉custom入口只凭输出shape通过。

这些是代码派发和具体ABI声明，没有本次CANN安装、算子调用或多硬件验收。升级时保存profile能力、actual q_pe、rope_dim、packed cache dtype与LSE consumer；错误fallback不能用能力标签绕过。
