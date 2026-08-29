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

- [Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa](../../../../runbooks/compilation/arch_variant_lookup_chain_soc_ini_npuarch_dispatcher.md)（`exemplifies`）：- `AIC_version` 与 `NpuArch` 互为印证：`NpuArch=3510` → dispatcher 的 `__NPU_ARCH__==3510` 分支；`AIC_version=AIC-C-310` → `dav_c310/` 目录名。任一即可定位变体，且都来自 ini 硬证据。；当前硬件平台架构号的枚举类。该枚举类和AI处理器型号的对应关系请通过CANN软件安装后文件存储路径下include/platform/soc_spec.h头文件获取。 - Ascend 950PR/Ascend 950DT：DAV_3510 - Atlas A3 训练系列产品/Atlas A3 推理系列产品：DAV_2201 - Atlas A2 训练系列产品/Atlas A2 推理系列产品：DAV_2201；焦点按 NpuArch 选择编译期 dispatcher 变体，目标提供产品到 DAV 架构枚举的权威映射入口。
- [NPU架构版本2002](../../../../guides/programming_guide/advanced_programming/hardware_implementation/hardware_constraints/npu_arch_2002.md)（`explains`）：NPU架构版本2002不支持Generic Addressing通用寻址（针对UB、stack、GM等地址空间），因此语言层面地址空间必须匹配。；Atlas 推理系列产品AI Core：DAV_2002；GetCurNpuArch 的返回映射可在运行或 Host 选择阶段识别 DAV_2002，随后应用焦点卡的地址空间约束。
- [NPU架构版本3002](../../../../guides/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_3002.md)（`explains`）：对应的产品型号为；获取当前硬件平台芯片架构版本号；连接静态架构映射与平台查询 API。
<!-- cannbot:related:end -->
