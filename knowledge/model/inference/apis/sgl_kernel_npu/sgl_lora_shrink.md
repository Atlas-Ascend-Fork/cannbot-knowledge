---
type: API
title: SGL LoRA shrink 的分块适配器与Vector/Cube精度
description: 区分 sgemmv_shrink 的FP32中间输出与 sgemmc_shrink 的低精度写回，保留切片布局和rank约束。
tags:
- task.implementation
- topic.model_adaptation
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/lora/sgemmv_shrink.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/lora/sgemmc_shrink.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/lora/sgemmc_shrink/torch_adapter.cpp
  role: constraint
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T04:38:44Z'
platforms:
- a2
- a3
- '950'
aliases:
- sgemmv_shrink
- sgemmc_shrink
---

# SGL LoRA shrink 的分块适配器与Vector/Cube精度

## 调用入口

```python
from sgl_kernel_npu.operators.lora import sgemmv_shrink

def sgemmv_shrink(x, weight, lora_indices, seq_len, lora_ranks, lora_scales, y,
                  slice_count=1, *, impl="auto"): ...

from sgl_kernel_npu.operators.lora import sgemmc_shrink

def sgemmc_shrink(x, weight, lora_indices, seq_len, lora_ranks, lora_scales, y,
                  slice_count, *, impl="auto"): ...
```

## 低秩第一阶段

对一个sequence block的token，lora_indices选择适配器i，seq_len给该block的连续token数；每个slice s计算 `lambda_i*x@A_i[s*r:(s+1)*r].T`。lambda已折叠alpha/r，不在expand再乘一次。负适配器ID或rank=0跳过该block，未覆盖输出列保留原值。

所有Tensor同NPU且连续。x `[tokens,hidden_in]` 为FP16/BF16，tokens>0，hidden_in大于输出宽度；weight `[num_loras,S*max_rank,hidden_in]` 或加单例维。每适配器权重的slice按其实际rank紧密相接，不按max_rank间隔。

| 路线 | 输出y | rank/对齐 |
| --- | --- | --- |
| sgemmv_shrink | `[tokens,S*max_rank]` FP32；点积和缩放FP32 | 支持0/8/16/32/64；hidden_in应为64倍数，以同时满足搬运和归约对齐。 |
| sgemmc_shrink | 同x类型；Cube点积与缩放FP32，写回一次舍入 | 已验证16/32/64，rank0跳过；没有rank8补齐，不支持低于16的非零rank。auto/ascendc入口强制要求 slice_count>0、hidden_in%16==0、y.size(1)可被slice_count整除，且每片输出容量 max_rank=y.size(1)/slice_count 为16倍数；这是输出容量约束，不能与适配器实际rank混淆。 |

索引、seq_len、rank均int32向量，lora_scales为每适配器FP16。Vector的slice_count默认1，Cube版本必填；max_rank由y宽度/slice_count取得。

## 副作用与验证

两路线auto均选择ascendc；显式torch_native做同语义参考。返回与原地写入y共享存储的Tensor，输入/权重/索引不变；设备端元数据取值由调用方保证。

验证同时检查正确block路由、rank0/-1跳过、切片有效列与尾部哨兵、data_ptr别名。Vector与Cube中间输出dtype不同，后续expand须配对，不能只因数学都是LoRA就替换。没有运行证据时不声称某条路线更快。

## 固定来源与验证状态

- [lora/sgemmv_shrink.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/lora/sgemmv_shrink.md)
- [lora/sgemmc_shrink.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/lora/sgemmc_shrink.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
