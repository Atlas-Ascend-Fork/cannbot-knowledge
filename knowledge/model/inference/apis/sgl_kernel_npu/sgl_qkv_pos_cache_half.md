---
type: API
title: SGL位置缓存QKV融合接口的两次BF16舍入
description: 明确 pos_cache_half 变体的int32索引截断、packed频率表、最终QK强制BF16和wide-grid条件。
tags:
- task.implementation
- topic.attention
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-08T11:03:33Z'
platforms:
- a2
- a3
- '950'
aliases:
- split_qkv_rmsnorm_rope_pos_cache_half_npu
---

# SGL位置缓存QKV融合接口的两次BF16舍入

## 调用入口

```python
from sgl_kernel_npu.operators.norm import split_qkv_rmsnorm_rope_pos_cache_half_npu

def split_qkv_rmsnorm_rope_pos_cache_half_npu(
    input_tensor,
    positions,
    cos_sin_cache,
    q_hidden_size,
    kv_hidden_size,
    head_dim,
    eps=None,
    q_weight=None,
    k_weight=None,
    q_bias=None,
    k_bias=None,
    rope_dim=None,
    cast_norm_to_bf16=True,
    wide_grid_min_tokens=1024,
    *,
    impl="auto",
):
    ...
```

## 输入与索引

输入为连续浮点 `[N,Q+2K]`；Q须为K整数倍，K含完整head，Triton head_dim须为2的幂。positions为同设备N个int32/int64值；先转int32，再在设备端clamp到 `[0,M-1]`，并非直接使用int64索引。cos_sin_cache为同设备 `[M,R]`，M>0，每行先cos_half后sin_half；rope_dim默认head_dim，须为不超过head_dim的正偶数。

eps=None跳过归一化，否则按head对Q/K做FP32 RMSNorm，并使用连续同设备至少head_dim值的q/k_weight；bias须成对。浮点类型为FP16/BF16/FP32，归一化向量可与输入dtype不同。

## 不可省略的舍入

cast_norm_to_bf16默认True，在RoPE前将Q/K舍入为BF16，跳过归一化时也生效。无论该开关如何，RoPE后Q/K全部特征（含未旋转尾部）都先舍入BF16，再转input.dtype。V原值复制。权重已是调用方准备的实际乘数，不再加1。

输出为同设备新连续Q `[N,Q]`、K/V `[N,K]`；不改输入，N=0不启动kernel。positions/cache可非连续，wrapper会连续化；不把索引回读主机，保留图捕获路径。

## 网格和验证边界

wide_grid_min_tokens默认1024，须为正整数；N达到阈值且Q<=8192才使用wide grid，否则按KV head分列。它只改变Triton执行分解，不改变数学。

auto/triton不自动回退，元信息非法在启动前AssertionError。上游arch22/arch35声明支持但硬件执行仍待验证。参考对拍即便输入存FP16/FP32，也应考虑Q/K的BF16精度；独立检查两次舍入、索引转型/截断、V原值和输入不变。

## 固定来源与验证状态

- [norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
