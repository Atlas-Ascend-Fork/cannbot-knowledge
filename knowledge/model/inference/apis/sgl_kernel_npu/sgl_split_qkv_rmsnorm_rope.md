---
type: API
title: SGL QKV拆分、可选RMSNorm与两种RoPE配对
description: 说明 split_qkv_rmsnorm_rope 的重复半表、成对bias、可选归一化和V原值复制。
tags:
- task.implementation
- topic.attention
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkv_rmsnorm_rope.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/split_qkv_rmsnorm_rope.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/norm/norm_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/split_qkv_rmsnorm_rope.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T15:27:12Z'
platforms:
- a2
- a3
- '950'
aliases:
- split_qkv_rmsnorm_rope
---

# SGL QKV拆分、可选RMSNorm与两种RoPE配对

## 调用入口

```python
from sgl_kernel_npu.operators.norm import split_qkv_rmsnorm_rope

def split_qkv_rmsnorm_rope(
    input,
    sin,
    cos,
    q_hidden_size,
    kv_hidden_size,
    head_dim,
    eps=None,
    q_weight=None,
    k_weight=None,
    q_bias=None,
    k_bias=None,
    is_neox_style=True,
    *,
    impl="auto",
):
    ...
```

## 入口布局

连续输入 `[N,Q+2K]` 依次是Q、K、V，Q是K的整数倍、K能被head_dim整除。浮点类型为FP16/BF16/FP32，各运算Tensor同设备；N允许0。sin/cos是连续 `[N,R]` 或 `[N,1,1,R]` 重复半表，各含N*R个值；R须为不超过 head_dim 的正偶数，Triton/torch_native 均在计算前检查。

eps=None时跳过归一化；否则eps须有限正数，并传连续至少head_dim个值的q_weight/k_weight。可选q_bias/k_bias必须成对提供且只在归一化时生效。按head做FP32 RMSNorm、仿射后，旋转前R个特征；尾部保留归一化值。is_neox_style=True配前后两半，False按相邻通道配对并使用前半频率。V始终直接复制。

返回新连续Q `[N,Q]`、K/V各 `[N,K]`，均为输入dtype和设备，输入和权重不变。这里FP32归一化与RoPE之间不额外降低激活dtype，不能替换成显式低精度分步路径。

## 分发、边界与验证

auto选择triton，不自动回退。独立后端检查元信息，Triton需NPU；错误在启动前AssertionError，空N不启动kernel。文档支持表列arch22/arch35，但实际硬件执行仍待验证。

显式torch_native对拍时同时覆盖eps=None、成对bias、部分旋转及两种配对；V复制可精确比较，Q/K按dtype容差比较。普通包导入依赖torch_npu与原生库；CPU参考的数学可用性不保证常规导入能在CPU独立完成。

## 旧普通入口与position-cache入口分别映射

旧 `sgl_kernel_npu.norm.split_qkv_rmsnorm_rope.split_qkv_rmsnorm_rope` 与新版实现同名函数的 `split_qkv_rmsnorm_rope_kernel`、装饰器、参数/default和完整body相同；新版Host额外先执行validate_split_qkv/NPU断言，N==0返回三空Tensor，旧Host没有完整检查和该短路。普通入口的sin/cos逐行重复半表、eps=None、成对bias和两种RoPE配对仍以本卡原合同为准，不能用旧raw入口弱检查放宽。

另一个旧模块 `norm.split_qkv_rmsnorm_rope_pos_cache_half_npu` 并非上面原型：它接positions与全局cos_sin_cache，并提供rope_dim、cast_norm_to_bf16、wide_grid_min_tokens。其 `fp32_to_bf16_rne` helper、`split_qkv_rmsnorm_rope_half_pos_cache_kernel`（含装饰器/完整body）、_WIDE_GRID_MAX_Q_HIDDEN=8192及Host后半执行逻辑，与新版 `implementation.triton.norm.split_qkv_rmsnorm_rope_pos_cache_half_npu` 相同。新版只在原逻辑前添加validate_pos_cache/NPU断言和空N短路；旧版原有的输入宽度、positions/cache整理、weight/bias至少head_dim容量检查仍存在，不能笼统写成旧版完全无guard。position-cache按positions选频率与可选BF16 RNE中间舍入是独立接口合同，不可塞进本页普通sin/cos参数列表。

普通与Gemma旧/新模块的kernels={}没有在可达Host中lookup。两份get_device_properties helper具有相同实现，但分别是两个Python模块内的独立无参数functools.cache：首次成功查询当前NPU的num_aicore/num_vectorcore后缓存，key不含device。进程切换设备不保证重新读取核数，两个模块也不保证共享JIT/autotune/属性缓存；不是同一个函数对象的转发别名。

[普通QKV完整实现A2/A3](/model/inference/operators/direct/transformer/posembedding/sgl_split_qkv_rmsnorm_rope.md)、[950](/model/inference/operators/direct/transformer/posembedding/sgl_split_qkv_rmsnorm_rope_950.md)，以及[position-cache完整实现A2/A3](/model/inference/operators/direct/transformer/posembedding/sgl_split_qkv_rmsnorm_rope_pos_cache_half_npu.md)、[950](/model/inference/operators/direct/transformer/posembedding/sgl_split_qkv_rmsnorm_rope_pos_cache_half_npu_950.md)分别保存实际Device资源、精度和尾块；旧路径只映射到各自相同body，不新增重复Operator、不扩大平台，未做编译/真机/数值验证。

### 增量固定实现来源

- [python/sgl_kernel_npu/sgl_kernel_npu/norm/split_qkv_rmsnorm_rope.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/split_qkv_rmsnorm_rope.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py)。

## 固定来源与验证状态

- [norm/split_qkv_rmsnorm_rope.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkv_rmsnorm_rope.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
