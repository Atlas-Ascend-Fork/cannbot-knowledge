---
type: API
title: GetCurNpuArch
description: 获取当前硬件平台芯片架构版本号。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCurNpuArch.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetCurNpuArch

## 功能说明
获取当前硬件平台芯片架构版本号。
## 函数原型
## 参数说明
无
## 返回值
当前硬件平台架构号的枚举类。该枚举类和AI处理器型号的对应关系请通过CANN软件安装后文件存储路径下include/platform/soc_spec.h头文件获取。
- Ascend 950PR/Ascend 950DT：DAV_3510
- Atlas A3 训练系列产品/Atlas A3 推理系列产品：DAV_2201
- Atlas A2 训练系列产品/Atlas A2 推理系列产品：DAV_2201
- Atlas 200I/500 A2 推理产品：DAV_3002
- Atlas 推理系列产品AI Core：DAV_2002
- Atlas 推理系列产品Vector Core：DAV_2002
- Atlas 训练系列产品：DAV_1001
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav](../../../../runbooks/compilation/bisheng_npu_arch_requires_lowercase_dav_2201.md)（`exemplifies`）：bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav 与《GetCurNpuArch》的实质衔接是：故障根因是把 DAV_2201 内部名误写成 bisheng 参数；架构查证链、GetCurNpuArch、dav-3510 同类 CMake 隔离、编译器/迁移文档和 CMake 参考共同确认 token 映射与全量重配。
- [NPU架构版本2002](../../../../guides/programming_guide/advanced_programming/hardware_implementation/hardware_constraints/npu_arch_2002.md)（`explains`）：NPU架构版本2002 与《GetCurNpuArch》的实质衔接是：2002 architecture spec给出硬件组成，constraints给出 Generic Addressing/全局变量限制；GetCurNpuArch和 SoC 查证链用于确认当前目标确实落在2002。
- [NPU架构版本2201](../../../../guides/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_2201.md)（`explains`）：GetCurNpuArch说明获取当前硬件平台芯片架构版本号。
- [NPU架构版本3002](../../../../guides/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_3002.md)（`explains`）：NPU架构版本3002 与《GetCurNpuArch》的衔接是：arch3002 卡给出该架构的核结构与存储约束；基础架构说明、运行时架构查询和 SoC→ini→NpuArch 查证链用于确认实际编译/运行落到该变体。
<!-- cannbot:related:end -->
