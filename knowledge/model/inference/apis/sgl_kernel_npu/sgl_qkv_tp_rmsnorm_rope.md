---
type: API
title: SGL张量并行QKV RMSNorm与NeoX RoPE接口
description: 说明 split_qkv_tp_rmsnorm_rope 的全局QK统计、完整head分片、归一化后dtype舍入和组内一致调用。
tags:
- task.implementation
- topic.parallelism
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkv_tp_rmsnorm_rope.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/split_qkv_tp_rmsnorm_rope.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_tp_rmsnorm_rope.py
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
- split_qkv_tp_rmsnorm_rope
---

# SGL张量并行QKV RMSNorm与NeoX RoPE接口

## 调用入口

```python
from sgl_kernel_npu.operators.norm import split_qkv_tp_rmsnorm_rope

def split_qkv_tp_rmsnorm_rope(
    input, cos, sin, q_hidden_size, kv_hidden_size, head_dim, eps, q_weight,
    k_weight, rotary_dim, tp_world, tp_group, *, impl="auto",
): ...
```

## 计算顺序

连续本地投影 `[B,Q+2K]` 拆成Q/K/V；每token计算Q、K均方统计。tp_world>1时在给定TP组内合并统计，再做带逐本地通道权重的RMSNorm。归一化结果先舍入input.dtype，随后只对前rotary_dim通道做NeoX RoPE；尾部不转动，V直接复制。

输入FP16/BF16/FP32，同一NPU；Q是K整数倍，分片包含完整head，head_dim为2的幂。cos/sin为稠密 `[B,R]`，每行前R/2值提供频率；R=rotary_dim为不超过head_dim的正偶数。q_weight为 `[Q]`、k_weight为 `[K]`，与独立按head共享权重的非TP接口不同。

## 组与输出契约

单卡传tp_world=1、tp_group=None。多卡时所有rank须共同调用，批量大小和分片宽度一致，不能只在部分rank进入函数。返回同设备同dtype的新Q `[B,Q]`、K/V `[B,K]`，输入不变。

auto选择triton；torch_native使用相同TP组与输出布局作为参考。先做单卡数学和布局对照，再验证组内统计与collective参与一致性。低精度参考需保留归一化到RoPE之间的dtype舍入，不能用全FP32融合表达式代替。

## 旧TP入口映射与collective边界

旧 `sgl_kernel_npu.norm.split_qkv_tp_rmsnorm_rope.split_qkv_tp_rmsnorm_rope` 与新版 `implementation.triton.norm.split_qkv_tp_rmsnorm_rope` 的Host执行语句/default、两个实际JIT、装饰器和globals一致；新版只移除旧长docstring并改设备属性helper导入。两个JIT为 `_split_qkv_and_compute_local_qk_var_kernel`、`_apply_global_rmsnorm_kernel`，不是三个自有Device kernel：第一步拆Q/K/V并生成FP32[B,2]局部QK均方，tp_world>1时Host调用 `torch.distributed.all_reduce(qk_var,group=tp_group)` 默认SUM，第二kernel以1/tp_world折算全局统计、RMS仿射、先舍入input dtype，再做NeoX RoPE，V只复制。tp_world==1完全不调用collective；B==0两版都在属性查询/launch前返回空输出。

两份get_device_properties helper具有相同实现，但分别是两个Python模块内的独立无参数functools.cache：首次成功查询当前NPU的num_aicore/num_vectorcore后缓存，key不含device。进程切换设备不保证重新读取核数，两个模块也不保证共享JIT/autotune/属性缓存；不是同一个函数对象的转发别名。

[TP=1完整实现A2/A3](/model/inference/operators/direct/transformer/posembedding/sgl_split_qkv_tp_rmsnorm_rope_tp1.md)和[950](/model/inference/operators/direct/transformer/posembedding/sgl_split_qkv_tp_rmsnorm_rope_tp1_950.md)对应可闭合的本地两个kernel。tp_world>1的核心all_reduce并非普通view/copy前处理：这里保留可见数学顺序、GM统计4*B*2字节与集体参与合同，通信库的Device算法/workspace/ordering实现未在此固定集合展开，不冒充多卡完整Operator/source_closed。该边界与单卡数学同body判断分开，未做多卡、真机或编译验证。

### 增量固定实现来源

- [python/sgl_kernel_npu/sgl_kernel_npu/norm/split_qkv_tp_rmsnorm_rope.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/split_qkv_tp_rmsnorm_rope.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_tp_rmsnorm_rope.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_tp_rmsnorm_rope.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py)。

## 固定来源与验证状态

- [norm/split_qkv_tp_rmsnorm_rope.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkv_tp_rmsnorm_rope.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
