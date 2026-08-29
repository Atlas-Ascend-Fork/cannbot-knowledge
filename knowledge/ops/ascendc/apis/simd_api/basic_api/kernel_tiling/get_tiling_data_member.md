---
type: API
title: GET_TILING_DATA_MEMBER
description: 用于获取tiling结构体的成员变量。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/GET_TILING_DATA_MEMBER.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GET_TILING_DATA_MEMBER

用于获取tiling结构体的成员变量。

用于获取tiling结构体的成员变量。

本接口属于 Kernel 侧 Tiling 接口，用于 Host 侧向 Kernel 侧传递 Tiling 参数。

约束：本函数需在算子kernel代码处使用，并且传入的tiling_data参数不需要声明类型。；暂不支持Kernel直调工程。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [手动 tiling 头遮蔽自动生成类致 no member 判别](../../../../runbooks/compilation/tiling_no_member.md)（`exemplifies`）：用于获取tiling结构体的成员变量。；在 `JOIN_OP_DEF True` 工程里，kernel 侧不要手动 `#include "<op>_tiling.h"`、不要 `REGISTER_TILING_DEFAULT`；tiling 数据经自动生成的 `kernel_tiling/kernel_tiling.h` + `GET_TILING_DATA` 获取本地拷贝。。运行手册解释成员访问报错并非字段不存在，而是手写 tiling 类遮蔽生成类，最终应回到受支持的宏获取路径。
<!-- cannbot:related:end -->
