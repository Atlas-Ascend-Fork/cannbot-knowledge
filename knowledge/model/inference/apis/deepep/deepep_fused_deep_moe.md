---
type: API
title: DeepEP fused_deep_moe：融合模式、激活与返回计数差异
description: 说明 FUSED_DEEP_MOE、DISPATCH_FFN_COMBINE、MEGA_MOE 的公开分发边界，限定 A3 与950的激活、权重契约和第二返回值语义。
tags:
- task.implementation
- topic.mixture_of_experts
- topic.compute.composite
- topic.compute.quantization
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/FUSED_DEEP_MOE.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/buffer.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/strategies/fused_strategy.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/deepep/ops/op_host/fused_deep_moe_a5/fused_deep_moe_tiling.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/deepep/deep_ep.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/deepep/test_fused_deep_moe_a5.py
  role: evidence
created_at: '2026-11-08T11:02:02Z'
updated_at: '2026-11-09T04:38:56Z'
platforms:
- a3
- '950'
aliases:
- fused_deep_moe
- FuseMode
---

# DeepEP fused_deep_moe：融合模式、激活与返回计数差异

## 一个入口不代表相同后端契约

`Buffer.fused_deep_moe(x, topk_idx, topk_weights, gmm1_permuted_weight, gmm1_permuted_weight_scale, gmm2_weight, gmm2_weight_scale, num_max_dispatch_tokens_per_rank, num_experts, quant_mode=1, fuse_mode=..., activation="swiglu", beta=4.0, linear_beta=25.0, ...)` 将 MoE 分发、两阶段专家 FFN 和聚合交给选中融合后端。

`FuseMode` 应从 `deep_ep.buffer` 导入，不在包顶层导出。固定源码在进入策略前拒绝非 MegaMoe 的字符串 `quant_mode`，并将 top-k 索引转为 int32。

| 模式 | 值 | 入口与边界 |
| --- | --- | --- |
| `FUSED_DEEP_MOE` | 1 | `aclnnFusedDeepMoe`；保留对应 fused 权重约定 |
| `DISPATCH_FFN_COMBINE` | 2 | `aclnnDispatchFFNCombine`；独立的权重/scale 契约，不支持 shared expert；Python 策略拒绝 SiTU |
| `MEGA_MOE` | 3 | 惰性加载 `cann_ops_transformer.ops.mega_moe`，容量、布局、软件版本另见[MegaMoe](deepep_mega_moe.md) |

不能将 mode 1 的 permuted GMM1 权重原样传给 mode 2/3。Buffer 注释说明 mode 2 的 scale 需要由调用方准备 float32 位表示对应的 int64，不能用普通数值 cast 代替；当前 mode 2 只实现 INT8 权重路径；BF16 权重在公开 C++ 分支被拒绝。

## A3 与 950 的差异

来源文档的 mode 1 范围为 `bs∈[1,256]`、`hidden∈[512,7168]`、`gmm1_hidden∈[1024,6144]`、top-k 为 1–12、专家数不超过 512。950 fused 路径另要求中间维度能被 1024 整除、专家数能被 EP ranks 整除，并要求 `bs≤capacity≤256`：输入会先 padding 到 capacity，Host 的 batch 上限约束该扩展后的长度。MXFP4 时 hidden 和中间维度为偶数。固定 Host 实现包含 FP4-NZ TensorList 与 stacked 权重分支：逻辑 hidden 和 GMM1 输出维须128对齐且满足非单位维检查，两组权重的 NZ 描述符均须合法；stacked 路径不接受 shared-expert 权重。测试定义了先对 packed bytes 做 NZ 转换、再 view FP4 的输入构造，并检查实际格式及存储字节数；环境若无法构造该输入会在调用融合 kernel 前失败。静态分支存在不等于当前环境可构造或已完成真机验证。

mode 1 在 A3 使用原有 permuted-weight 路径，950 host op 的 dtype/format 支持有所不同，不能因都叫 `gmm1_permuted_weight` 就认为相同布局。公开 950 fused Python 路径没有真正透传 shared-expert tensors；底层 host 定义了可选输入不等于公开路径已可用。

| 模式/平台 | 第二返回值 |
| --- | --- |
| mode 1，A3 | `ep_recv_count [E_local×R]`，按 EP rank 展开 |
| mode 1，950 | `expert_token_nums [E_local]`，当前 rank 各本地专家计数 |
| mode 2 / mode 3 | 本地 `expert_token_nums [E_local]` |

所有模式的第一返回值是本地 `[bs,hidden]` 输出；不能将第二返回值跨模式按同样的 reshape 使用。

## 激活函数

SwiGLU 为 `gate*sigmoid(gate)*up`。SiTU 的 gate 为 `beta*tanh(gate/beta)*sigmoid(gate)`，可选地再将 up 替换为 `linear_beta*tanh(up/linear_beta)`；`linear_beta=None` 保持 up 不变。选择 SiTU 时 beta 以及提供的 linear_beta 需为正。

950 mode 1 支持 SwiGLU/SiTU；A3 的 SiTU 走 MegaMoe；mode 2 只支持 SwiGLU。`profile_enable` 只控制已启动 profiling 内的当前调用，不会自行开始 profiling。

## 验证与失效边界

切换 fuse mode 前重新准备布局、scale、capacity 和专家 ID 合法性，分别核对第二返回值含义；MegaMoe 对专家 ID 的要求比 DeepEP 中 `-1` 的语义更窄。应覆盖 `bs<capacity` 的 padding/裁切以及不同激活分支。本卡是公开 API 与固定源码 reference 的蒸馏，未分析完整 Device 启动闭包，未执行编译、真机、数值或性能测试。

## Evidence

- [python/deep_ep/doc/FUSED_DEEP_MOE.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/FUSED_DEEP_MOE.md)（primary）
- [python/deep_ep/deep_ep/buffer.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/buffer.py)（implementation）
- [python/deep_ep/deep_ep/strategies/fused_strategy.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/strategies/fused_strategy.py)（implementation）
