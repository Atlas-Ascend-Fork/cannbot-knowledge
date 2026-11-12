---
type: Optimization
title: SGLang CMO权重预取的流顺序与消费位置
description: 从CMO helper和Qwen3/layer-boundary调用解释预取字节上限、主流先行依赖、prefill piecewise触发和收益验收边界。
tags:
- task.optimization
- topic.memory
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/cmo.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/layer_boundary/prepare.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/qwen3.py
  role: example
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/layer_boundary/stage.py
  role: supporting
created_at: '2026-11-08T11:53:39Z'
updated_at: '2026-11-08T12:27:46Z'
platforms: []
---

# SGLang CMO权重预取的流顺序与消费位置

## 适用信号和规则

矩阵乘前存在AIV/通信窗口且权重访存成为瓶颈时，当前SGLang有CMO辅助流发起npu_prefetch的实现。收益只能通过同负载profile归因；源码注释的字节/带宽估时不是实测时延或吞吐保证。通用决策已有[权重预取规则](/model/inference/optimizations/rules/decode_weight_prefetch_ordering.md)，本卡只承载SGLang实现差异。

prepare_weight_cache(handle,cache,PREFETCH_MAX_SIZE=1000000000)惰性建CMO流，先wait主流，再在CMO流对一个权重或列表逐个调用torch_npu.npu_prefetch。上限单位为字节，是单次调用上限，不是全模型或整层总预算。wait_cmo_stream由当前流等待CMO；不调用它不能由helper自动推导依赖闭合。

## 实际可达分支

layer_boundary._reduce_update_read在需要的all-reduce完成后，且NPU/cache非None时调用预取，再进入norm/read。Qwen3在NPU且Prefill后端TC_PIECEWISE、MLP两个线性层有weight时，把gate_up_proj/down_proj列表传给ffn边界；MLP后再wait_cmo_stream。不能把这个触发描述成所有Decode或所有模型默认预取，也不能擅改成“MLP前全等待”而抹去当前调度窗口。

## 代价、回退和验证

预取占用带宽和缓存，过大范围可能驱逐其他工作集；cache helper不产生新的模型数学输出。CMO模块的share_stream与npu.utils中的share/routed流是不同全局状态，不能按同名变量认定同一条流。

比较启用/不传cache的同模型、同shape、同量化版本，记录CMO预取区间、矩阵乘、通信和总前向时间；分开TTFT、TPOT与单task指标，并核对精度与尾部流完成。回退到原边界调用/不传cache，保留权重和并行配置；本文不建议用未声明env臆造开关。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
