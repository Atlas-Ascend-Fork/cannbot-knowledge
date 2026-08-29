---
type: API
title: SetDim
description: 设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetDim.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetDim

设置多核Matmul时，参与运算的核数。不同场景下的设置规则如下： - 纯Cube模式（只有矩阵计算） SetDim设置当前AI处理器可用的核数，通过Tiling计算得到执行Matmul计算实际使用的核数，实际使用的核数小于等于AI处理器可用的核数。SetSimdNumBlocks按照实际使用的核数由用户进行配置，SetSimdNumBlocks加载的核全部用于Matmul API的计算。

参数：
- dim（输入）：多核Matmul tiling计算时，可以使用的核数。注意，MIX模式下，该参数取值小于等于耦合模式下启动的AICore核数或者分离模式下启动的AIV核数。

返回值：-1表示设置失败； 0表示设置成功。
