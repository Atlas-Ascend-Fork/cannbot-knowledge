---
type: API
title: SGLang Batch Invariant FIA：OpOverloadPacket、v2参数与图捕获缓冲
description: 区分返回OpOverloadPacket的FIA入口和直接执行的FIA v2，列出字段改名、TND长度语义及workspace/output辅助接口。
tags:
- task.implementation
- topic.attention
- topic.graph_execution
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/fused_infer_attention_score.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/fused_infer_attention_score_v2.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/fused_infer_attention_score.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/fused_infer_attention_score_v2.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/installation.md
  role: constraint
created_at: '2026-11-08T11:02:02Z'
updated_at: '2026-11-09T11:15:03Z'
platforms:
- a2
- a3
- '950'
aliases:
- fused_infer_attention_score_batch_invariant
- fused_infer_attention_score_batch_invariant_v2
---

# SGLang Batch Invariant FIA：OpOverloadPacket、v2参数与图捕获缓冲

## v1 返回算子对象，v2 直接计算

`fused_infer_attention_score_batch_invariant(*,impl="auto")` 没有 query/key/value 位置参数：先调用它取得外部 `OpOverloadPacket`，然后调用该 packet 的默认或 `.out` 重载。保留 packet 是为了保留图捕获所需 schema 和 `.out`，不能把入口当作普通 forwarding function 传入 Q/K/V。

`fused_infer_attention_score_batch_invariant_v2(query,key,value,*,...,impl="auto")` 则立即转发执行并返回 `(attention_out,softmax_lse)`。两种接口均属于 `sgl_kernel_npu.operators.batch_invariant`。

| 语义 | v1 字段 | v2 字段 |
| --- | --- | --- |
| Q heads | `num_heads` | `num_query_heads` |
| QK scale | `scale` | `softmax_scale` |
| Q lengths | `actual_seq_lengths` | `actual_seq_qlen` |
| KV lengths | `actual_seq_lengths_kv` | `actual_seq_kvlen` |
| 返回 LSE | `softmax_lse_flag` | `return_softmax_lse` |

`num_key_value_heads=0` 表示与 Q heads 一致，默认布局 BSH；也可按外部 schema 选择 BNSD/TND。TND 的 Q 长度按累加和表达；分页 KV 需配套 `block_table` 与 `block_size`。字段改名后不能把同一 kwargs dict 不经转换用于两版。

## workspace、输出与图捕获

v1 提供 `_get_max_workspace`、`_infer_output` 和 `_out` 三类公开 helper（完整前缀为 `fused_infer_attention_score_batch_invariant`）。先用与实际计算相同的参数取得 workspace 需求，再按布局/head 数分配 output/LSE，最后调用 packet `.out(...,workspace=...,out=[attention_out,softmax_lse],...)` 或对应显式 out helper。不要把 workspace 大小与实际缓冲对象混淆。

v2 的公开辅助入口是 `fused_infer_attention_score_batch_invariant_v2_get_max_workspace` 与 `_infer_output`；本次快照没有同名公开 v2 `_out` forwarding helper。量化 scale、RoPE、dtype 覆盖等继续按 v2 schema 传递，不能由 v1 helper 的签名推导。

未启用 LSE flag 时第二结果可为未定义 tensor，不应按有效 LSE读取。普通调用输出按所选布局排布；out 路径则写入调用方提供的缓冲。

## Python转发的默认值与外部边界

两个模块都首次导入batch_invariant_ops后缓存torch.ops命名空间；封装没有自己的Q/K/V连续化、shape检查、量化转换、workspace分配或Device算法。主调用、max_workspace和infer_output是不同的外部符号，任一符号存在不能证明另外几个已注册。源内没有自动eager预热或捕获成功保证。

v1的显式out helper转发到 `torch.ops.batch_invariant_ops.npu_fused_infer_attention_score_batch_invariant_out`，分别传workspace、attention_out和softmax_lse；packet `.out` 则按实际外部schema调用，不能把两个入口的调用形式混写。包装只返回外部结果，没有替调用方验证缓冲容量、复用地址或跨流生命周期。max_workspace返回外部需求，infer_output将query/value及布局、head/量化/LSE/RoPE等分配相关字段传给外部helper；这些准备入口不执行完整注意力，也不证明计算时所有长度、mask、分页参数均已有效。

默认Q heads=1、KV heads=0、scale=1.0、pre_tokens=next_tokens=2147483647、input_layout="BSH"、各mode=0、LSE关闭。scale不会由Python自动替换成1/sqrt(head_dim)，heads也不由Tensor shape自动推导。v2以softmax_scale/num_query_heads等新字段直接透传，query/key/value_quant_mode及显式dtype字段同样交给外部库解释；默认值存在不代表所有dtype/模式组合可用。

v1显式接受key_shared_prefix、value_shared_prefix和actual_shared_prefix_len；本快照v2的函数签名没有这三个Tensor/长度参数，虽然含key_shared_prefix_dtype/value_shared_prefix_dtype字段，也不能据此把v1前缀缓存kwargs原样迁入v2。v2还可透传learnable_sink和query/key RoPE等独立字段，支持约束继续以匹配外部版本schema为准。

固定Git树只提供上述适配与安装地址，不能用同名普通CANN FIA源码替代外部BatchInvariant Device实现，也不能由“批不变”文档契约反推其Cube分块或归约调度。这里保留已读Python调用合同，不声称完整算子源码闭包。

## 验收对象

上游把不变量定义为同一 request 单独计算与在大 batch 中计算时的结果逐位一致。拆 request 时必须同步调整长度列表、分页映射与布局，不仅仅切 Q 的 batch 维。图捕获还应验证 workspace、输出地址与 packet schema，不能以 eager 成功代替。

## 来源与验证边界

本接口文档的支持表列出 `batch_invariant_ops` 在 arch22/arch35 可用，安装说明列出 910B/A3/950 的对应设备包。调用前须按[安装指南](/model/inference/guides/integration/sgl_kernel_npu/sgl_batch_invariant_installation.md)安装外部 CANN 算子包与 torch extension；`auto` 与 `batch_invariant_ops` 为同一入口，不提供缺依赖回退。逐位一致性为上游接口契约，本次未执行外部 kernel 的编译、真机、数值、图捕获或性能测试，未声称完成其 Device 实现分析。

## Evidence

- [docs/api/zh/operators/batch_invariant/fused_infer_attention_score.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/fused_infer_attention_score.md)（primary）
- [docs/api/zh/operators/batch_invariant/fused_infer_attention_score_v2.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/fused_infer_attention_score_v2.md)（supporting）
- [python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/fused_infer_attention_score.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/fused_infer_attention_score.py)（implementation）
- [python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/fused_infer_attention_score_v2.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/fused_infer_attention_score_v2.py)（implementation）
- [docs/api/zh/operators/batch_invariant/installation.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/installation.md)（constraint）
