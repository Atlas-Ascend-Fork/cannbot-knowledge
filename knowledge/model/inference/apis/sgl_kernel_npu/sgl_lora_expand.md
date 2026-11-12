---
type: API
title: SGL LoRA expand 的原地累加、切片边界与rank差别
description: 说明SGEMMV/SGEMMC expand的低秩类型、切片和原地累加，并区分有效rank数学域与SGEMMV按32字节块搬运的容量边界。
tags:
- task.implementation
- topic.model_adaptation
- topic.memory
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/lora/sgemmv_expand.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/lora/sgemmc_expand.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/lora/sgemmc_expand/torch_adapter.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/lora/sgemmv_expand/op_kernel/sgemmv_expand.cpp
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
- '950'
aliases:
- sgemmv_expand
- sgemmc_expand
---

# SGL LoRA expand 的原地累加、切片边界与rank差别

## 调用入口

```python
from sgl_kernel_npu.operators.lora import sgemmv_expand

def sgemmv_expand(x, weight, lora_indices, seq_len, lora_ranks, slice_offsets, y, *, impl="auto"): ...

from sgl_kernel_npu.operators.lora import sgemmc_expand

def sgemmc_expand(x, weight, lora_indices, seq_len, lora_ranks, slice_offsets, y,
                  *, impl="auto"): ...
```

## 低秩第二阶段

输入h已经由shrink包含alpha/r，expand计算每slice的 `h[s*r:(s+1)*r]@B_i[o_s:o_next,:r].T`，并加到已有基础GEMM输出y。slice_offsets定义输出列区间；只有有效rank列参与数学结果，不能由此推导DMA不会读取rank之后的存储。负适配器ID或rank0的block不累加；切片外列保留旧值。

weight为连续FP16/BF16 `[num_loras,hidden_out,max_rank]` 或加单例维，dtype与y一致。y `[tokens,hidden_out]` 原地累加；输入h `[tokens,S*max_rank]`，S为slice_offsets长度减1，tokens>0。全部Tensor同NPU连续，索引/seq_len/rank/slice_offsets均int32。

| 路线 | h类型/精度 | 实现约束 |
| --- | --- | --- |
| sgemmv_expand | h为FP32，点积及与y累加用FP32，写回一次舍入 | rank为0/8/16/32/64；FP16/BF16输出的每个offset须为16元素倍数。 |
| sgemmc_expand | h与y同FP16/BF16，Cube点积及累加用FP32，写回一次舍入 | ascendc后端要求非零实际lora_ranks>=16，rank0仍跳过；上游用例覆盖16/32/64，无rank8补齐。实际rank下限与下述max_rank容量对齐是两项独立条件。新框架 ascendc 入口强制 max_rank（每切片输入宽度）为16倍数，在 ACLNN 调用前 TORCH_CHECK 拒绝未对齐值；slice宽度建议16倍数，切片宽还须为2的幂或Matmul所选baseN整数倍，防止末步越界。 |

slice_offsets递增且不超hidden_out，末项可小于y宽度；max_rank由h宽度/S确定。各block的适配器元数据在设备读取，调用方保证合法。


原生SGEMMV的搬运单位还受32字节块限制。固定`KernelSgemmvExpand::CopyInW`把每行读取块数设为`ceil(rank*sizeof(W_T)/32)`：FP16/BF16的rank8会请求整32字节，即16个元素。max_rank不为8时，内部rank扩为16，计算通过零填充和`MASK_FILTER`屏蔽补齐列；屏蔽数学贡献不等于未搬运这些列。max_rank=8时内部rank仍为8，完整tile的DMA请求跨度与单个权重队列槽容量不一致，不能只以公开支持rank8或depth2总容量作为单槽安全证明。上述为固定源码推导，未在NPU复现；本API数学合同不能替代具体原生分支的容量及调度验证。

## 副作用和验证

auto选ascendc，没有自动切参考；torch_native须显式选择。返回与y共享存储的Tensor，h/权重/元数据只读。验证使用非零初始y以检查累加而非覆盖，用独立y副本对拍，核对切片外哨兵和跳过block。不能重复应用shrink已折叠的scale，也不能把Cube的低精度h当Vector FP32输入契约。

## 固定来源与验证状态

- [lora/sgemmv_expand.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/lora/sgemmv_expand.md)
- [lora/sgemmc_expand.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/lora/sgemmc_expand.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
