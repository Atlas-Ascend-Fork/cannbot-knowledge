---
type: API
title: ReinterpretCast
description: 将当前GlobalTensor重解释为用户指定的新类型。转换后的Tensor与原Tensor地址及内容完全相同，Tensor的内存大小（比特数）保持不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/ReinterpretCast.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ReinterpretCast

将当前GlobalTensor重解释为用户指定的新类型。转换后的Tensor与原Tensor地址及内容完全相同，Tensor的内存大小（比特数）保持不变。

将当前GlobalTensor重解释为用户指定的新类型。转换后的Tensor与原Tensor地址及内容完全相同，Tensor的内存大小（比特数）保持不变。

本接口属于 GlobalTensor 数据结构操作接口，用于访问和修改 GM 上的 Tensor 属性。

返回值：重解释后的GlobalTensor。

约束：当数据类型发生转换后，元素个数可能无法取整，例如3个int4b_t类型转换为uint32_t，则转换后调用GetSize接口，只能获取向下取整的整数值，这种场景在CPU状态运行时，会有对应的提示告警信息。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

<!-- cannbot:related:start -->
## 相关

- [FreeTensor早释使队列别名被下一轮DMA覆盖](../../../../../runbooks/precision/reinterpret_tensor_alias_must_outlive_queue_release.md)（`exemplifies`）：“转换后的Tensor与原Tensor地址及内容完全相同，Tensor的内存大小（比特数）保持不变。”给出焦点端事实；“xT = xIO.ReinterpretCast<CT>()”给出候选端事实。API 的同地址重解释合同解释了 runbook 中 xT 仍别名 xIO 的事实，并直接支撑 FreeTensor 早释后别名被复用内存覆盖的根因判断。
<!-- cannbot:related:end -->
