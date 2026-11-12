---
type: API
title: SGLang Markov采样的Philox、词表分片与噪声所有权
description: 解释markov_sample_step_triton的舍入、温度、Philox计数协议、全局词表索引、gather回调和外部噪声重放条件。
tags:
- task.implementation
- topic.compute.random_sampling
- topic.parallelism
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/sample/markov_sample_step_triton.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/sample/markov_sample.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/sample/markov_sample.py
  role: implementation
created_at: '2026-11-08T11:03:54Z'
updated_at: '2026-11-09T04:38:09Z'
platforms:
- a2
- a3
- '950'
---

# SGLang Markov采样的Philox、词表分片与噪声所有权

## 签名与范围

```python
from sgl_kernel_npu.operators.sample import markov_sample_step_triton
markov_sample_step_triton(
    *, base_logits, bias, temperatures, key, offset, step, step_dtype,
    vocab_start=0, gather=None, gather_logits=None, logits_out=None,
    has_sampled_rows=None, exp_noise=None, impl="auto")
```

Triton与Torch reference声明支持arch22/arch35（A2/A3、950）；auto选Triton。这里只记录固定版本接口，未执行全平台验收。

## 数值和有效列

只对bias覆盖的有效列把bias加到base logits，并舍入到`step_dtype`（FP32/FP16/BF16）。温度0取最大logit；非零时取 `logit/temperature - log(noise)` 最大值，noise为正指数分布样本。本地/候选选择按 bias 宽度屏蔽 padding；保留汇聚 logits 分支会先写完整 `[B,P]` 本地缓冲，再将 gather_logits 返回的全部保留列视为有效列，不能自动沿用该屏蔽。输出为同设备新建 `[B]` int64 **全局**token ID，空有效分片贡献哨兵2147483647。

| 参数 | 合同 |
| --- | --- |
| base_logits / bias | 同NPU浮点 `[B,P]` / `[B,V]`，B>0、P>0、0<=V<=P，列stride=1。 |
| temperatures | 同设备连续FP32 `[B]`；建议非负有限值，0为贪心。 |
| offset | 同设备单元素int64；即使提供外部noise仍须传入。 |
| vocab_start | 分片全局起点，须4整除。 |
| logits_out | 可选同设备、step_dtype缓冲；本地 `[B,P]`，汇聚 `[B,V_global]`，列stride=1，原地写舍入logits。 |
| exp_noise | 可选同设备FP32正噪声，与本地logits或汇聚后的logits_out同shape，列stride=1。 |

## 随机流和回调合同

内部Philox流由key、offset、step、行号与全局词表索引共同确定。提供 `exp_noise` 后跳过内部生成、忽略key/step；调用方负责更新外部噪声，尤其图重放不能把固定噪声误当新采样。`has_sampled_rows=False` 仅可用于所有行均贪心的情况。

不保留logits的分布式选择由`gather`交换候选并沿batch堆叠，候选布局依后端；不能把一个后端的候选回调直接套另一个后端。若同时用gather与logits_out，必须提供 `gather_logits`，返回按全局词表顺序排列的有效列，或保证 padding 仅处于最终末尾并被 logits_out 宽度截去；直接拼接各分片完整 `[B,P]` 会把中间 padding 纳入选择并改变全局索引；外部noise也须匹配汇聚结果形状。公开层直接转发，回调、分片、随机数生命周期由调用方保证。

## 复核入口

上游 `tests/python/operators/sample/test_markov_sample_step_triton.py` 是精度入口；先用同一外部noise隔离随机差异，再核对step_dtype舍入、0温度、padding、空分片、vocab_start和两个gather模式。Triton/Torch均声明同一计数协议不代表任意回调或随机序列自动兼容。本次未执行数值、图重放或性能测试。
