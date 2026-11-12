---
type: API
title: SGL变长缓存片段复制与布尔返回值
description: 说明 assign_cache_op 的位模式复制、32字节访问边界和True不保证发生复制的状态语义。
tags:
- task.implementation
- topic.data_movement
- topic.alignment
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/assign_cache_op.md
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
- assign_cache_op
---

# SGL变长缓存片段复制与布尔返回值

## 调用入口

```python
from sgl_kernel_npu.operators.mem_cache import assign_cache_op

def assign_cache_op(
    dst, src, dst_start, dst_end, src_start, src_end, *, impl="auto",
): ...
```

## 参数与分段布局

dst为稠密 `[B,W]`，src为稠密 `[N]`；dst_start/dst_end/src_start/src_end是同设备int64向量，长度至少B。第i行把src的半开区间复制到dst行对应半开列区间，调用方须提供对应的有效正长度片段。

按1、2、4、8字节元素宽度复制，保留位模式而非进行数值dtype转换；源/目标应使用相同元素宽度。这既可更新请求token映射表，也适用于同类稠密分段缓冲。接口原地改dst，src只读。

## 返回状态和原生边界

输入缺失、标量或索引向量长度不足B时返回False。其他路径正常返回True，其中也包括元素宽度不支持导致跳过复制，因此True不能独立证明数据已更新。

AscendC访问需给每段末尾保留向上取整到32字节后的可用存储；仅逻辑区间在shape内不一定满足物理访问约束。所有张量同一NPU，auto选择ascendc，参考实现须显式torch_native。

验证需在目标区间填哨兵，比较被写区间的原始位模式以及区间外值。分别覆盖支持元素宽度、状态False及不支持宽度的True/未写行为，不能只检查布尔返回值。

## 固定来源与验证状态

- [mem_cache/assign_cache_op.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/assign_cache_op.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
