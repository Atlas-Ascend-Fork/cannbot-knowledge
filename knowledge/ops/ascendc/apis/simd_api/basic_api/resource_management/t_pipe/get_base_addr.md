---
type: API
title: GetBaseAddr
description: 根据传入的logicPos（逻辑抽象位置）获取该位置的基础地址，只在CPU调试场景下生效。通常用于计算Tensor在logicPos的偏移地址。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/GetBaseAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetBaseAddr

头文件路径为："basic_api/kernel_tpipe.h"。

根据传入的logicPos（逻辑抽象位置），获取该位置的基础地址，只在CPU调试场景下此接口生效。通常用于计算Tensor在logicPos的偏移地址即Tensor地址减去GetBaseAddr返回值。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [Gather 双加 LocalTensor 基址导致交错旋转乱码](../../../../../runbooks/precision/localtensor_gather_base_address_not_double_counted.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《GetBaseAddr》明确提供“根据传入的logicPos（逻辑抽象位置）获取该位置的基础地址，只在CPU调试场景下生效。通常用于计算Tensor在logicPos的偏移地址。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [GetCurAddr](../local_mem_allocator/get_cur_addr.md)（`related`）：GetBaseAddr说明根据传入的logicPos（逻辑抽象位置）获取该位置的基础地址，只在CPU调试场景下生效。通常用于计算Tensor在logicPos的偏移地址。
- [Init](init.md)（`related`）：GetBaseAddr 只能在初始化后的逻辑内存池上查询。
- [InitBufPool](init_buf_pool.md)（`related`）：BufPool 绑定各 logicPos 的基址，是查询值来源。
- [LocalMemAllocator简介](../local_mem_allocator/local_mem_allocator_intro.md)（`same_topic`）：LocalMemAllocator 介绍解释逻辑位置、基础地址和偏移模型。
<!-- cannbot:related:end -->
