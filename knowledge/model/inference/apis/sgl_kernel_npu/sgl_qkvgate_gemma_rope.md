---
type: API
title: SGL Gemma Q/gate解交错与部分RoPE接口
description: 说明 split_qkvgate_gemma_rmsnorm_rope 的逐head交错布局、原始Gemma偏移和只读gate/V。
tags:
- task.implementation
- topic.attention
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkvgate_gemma_rmsnorm_rope.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/norm/split_qkv_rmsnorm_rope.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/norm/norm_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/split_qkv_rmsnorm_rope.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
- '950'
aliases:
- split_qkvgate_gemma_rmsnorm_rope
---

# SGL Gemma Q/gate解交错与部分RoPE接口

## 调用入口

```python
from sgl_kernel_npu.operators.norm import split_qkvgate_gemma_rmsnorm_rope

def split_qkvgate_gemma_rmsnorm_rope(
    input,
    sin,
    cos,
    q_hidden_size,
    kv_hidden_size,
    head_dim,
    rope_dim,
    eps,
    q_weight,
    k_weight,
    *,
    impl="auto",
):
    ...
```

## 布局和Gemma权重

输入连续浮点 `[N,2Q+2K]`，顺序是 `[q0,gate0,q1,gate1,...,K,V]`，不是全部Q后接全部gate。将每head的Q与gate解交错后，只对Q/K做RMSNorm，乘数为 `1+q_weight`、`1+k_weight`，其中输入weight是原始Gemma偏移；不得在调用前加1后又在算子内重复加1。

归一化使用FP32，eps为有限正实数；仅旋转每head前rope_dim个特征，NeoX前后半配对，尾部保留归一化值。V/gate都直接复制，不做激活、归一化或旋转。

## 参数和返回

Q为K整数倍，K可被head_dim整除；Triton 与 torch_native 的 head_dim 均须为2的幂。rope_dim是正偶数且不超过head_dim；sin/cos连续，shape为 `[N,R]` 或 `[N,1,1,R]`，R与rope_dim一致。NeoX旋转要求sin为重复半表[sin(theta),sin(theta)]，cos按同一前后半角度配对；形状一致不足以保证旋转语义，不能传入未重复的独立角度表。weight连续、至少head_dim个值，可与输入不同浮点dtype但同设备；浮点限FP16/BF16/FP32。

返回四个同设备、输入dtype的新连续Tensor：Q `[N,Q]`、K/V `[N,K]`、gate `[N,Q]`。N允许0，空输入不启动kernel，不修改任何输入。auto/triton无自动回退，启动前独立校验元信息。

## 验证边界

文档实现表声明arch22/arch35支持，同时标注实际硬件执行仍待验证。对照torch_native时覆盖D=256/R=64等部分RoPE、原始偏移为零、gate/V精确复制；Q/K使用dtype容差，不能据此宣称完整模型精度验收。

## 旧Gemma Q/gate入口的同body范围

旧 `sgl_kernel_npu.norm.split_qkv_rmsnorm_rope.split_qkvgate_gemma_rmsnorm_rope` 与新版同名函数的实际 `split_qkvgate_gemma_rmsnorm_rope_kernel`、JIT装饰器、参数/default、input/output地址与数学body相同。它们都以每head的[Q,gate]交错段解交错：gate/V只复制，Q/K为FP32 RMSNorm乘1+原weight并旋转前rope_dim，head尾保留归一化值。不要与外部torch_npu的add_gemma_rms_norm或MRoPE t/h/w三轴算法合并。

新版Host在旧的head二次幂/宽度关系检查之前，加入validate_split_qkvgate与NPU断言，以及N==0时直接返回四个空输出；旧Host没有这套完整dtype/device/连续、trig表、weight容量、eps等保护和空输入短路。函数body一致仅支持合法交集内复用，不扩大公开支持。两个模块各自重复定义的kernels={}在可达Host中没有用于lookup/缓存，不能因全局变量存在就宣称显式compiled-kernel缓存已还原。

两份get_device_properties helper具有相同实现，但分别是两个Python模块内的独立无参数functools.cache：首次成功查询当前NPU的num_aicore/num_vectorcore后缓存，key不含device。进程切换设备不保证重新读取核数，两个模块也不保证共享JIT/autotune/属性缓存；不是同一个函数对象的转发别名。

[Gemma Q/gate完整实现A2/A3](/model/inference/operators/direct/transformer/posembedding/sgl_split_qkvgate_gemma_rmsnorm_rope.md)及[950](/model/inference/operators/direct/transformer/posembedding/sgl_split_qkvgate_gemma_rmsnorm_rope_950.md)负责相同Device资源/精度；本段只补旧Host和缓存对象边界，未做编译或数值验证。

### 增量固定实现来源

- [python/sgl_kernel_npu/sgl_kernel_npu/norm/split_qkv_rmsnorm_rope.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/split_qkv_rmsnorm_rope.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py)。

## 固定来源与验证状态

- [norm/split_qkvgate_gemma_rmsnorm_rope.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkvgate_gemma_rmsnorm_rope.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
