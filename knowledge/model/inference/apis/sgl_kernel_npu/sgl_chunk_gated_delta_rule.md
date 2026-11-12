---
type: API
title: SGLang chunk_gated_delta_rule 的状态与长度契约
description: 区分各序列实际长度、V×K 状态布局、可选块进入状态缓冲，以及 arch22/arch35 的状态精度差异。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/chunk_gated_delta_rule.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-08T11:04:14Z'
platforms:
- a2
- a3
- '950'
---

# SGLang chunk_gated_delta_rule 的状态与长度契约

## 接口原型

```python
from sgl_kernel_npu.operators.attention import chunk_gated_delta_rule

def chunk_gated_delta_rule(
    query,
    key,
    value,
    *,
    beta=None,
    initial_state=None,
    actual_seq_lengths=None,
    scale=None,
    g=None,
    chunk_state=None,
    impl="auto",
):
    ...
```

## 状态递推

该融合入口按序列执行 Gated Delta Rule：先用 `exp(g_t)` 衰减旧状态，再令 `u_t=beta_t*(v_t-D_t@k_t)`、`S_t=D_t+outer(u_t,k_t)`，输出 `scale*(S_t@q_t)`。`g=None` 表示不衰减；`scale=None` 表示 1.0，显式 0.0 仍有效。

Q/K 为 BF16 `[T,Nk,Dk]`，V 为 BF16 `[T,Nv,Dv]`，beta 为 BF16 `[T,Nv]`，可选 g 为 FP32 `[T,Nv]`。各维为正，`Nk,Nv<=64`、`Dk,Dv<=128`、`Nv%Nk==0`。状态是 `[B,Nv,Dv,Dk]`，最后两维为 V、K；不能直接复用 K、V 顺序的 Triton chunk 状态。

`beta`、`initial_state`、`actual_seq_lengths` 即使签名默认为 None，实际也必须提供。int32 `[B]` 长度是每序列长度，不是累计边界。Ascend C 要求各项为正、和为 T，内容由调用方保证；参考接受零长度序列并保留该序列初始状态。

## 输出、缓冲与后端差异

函数返回 `(out,final_state)`，分别为 BF16 `[T,Nv,Dv]` 与同初始状态 dtype 的 `[B,Nv,Dv,Dk]`，初始状态不原地修改。原生 arch22 仅支持 BF16 状态；arch35 支持 BF16/FP32 状态。`torch_native` 用 FP32 内部计算。

可选 `chunk_state[sum(ceil(length/64)),Nv,Dv,Dk]` 保存各块进入状态，按序列再按块排列。连续缓冲原地写入；非连续缓冲使用临时副本且不回写，函数也不返回它。调用方负责容量和长度值，不能只靠元数据检查。

`auto` 固定选 Ascend C，不自动回退。所有原生张量须同 NPU；输入可在内部连续化。验证应覆盖多序列独立状态、64-token 尾块、状态精度限制，以及连续/非连续 chunk_state 的不同写回行为。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。
