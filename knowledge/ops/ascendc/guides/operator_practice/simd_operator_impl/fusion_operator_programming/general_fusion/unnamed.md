---
type: Guide
title: 通用融合特性场景
description: 为避免执行通信任务的环境中硬件闪断导致发生通信中断，通算融合算子可通过配置编译宏与环境变量，开启重执行能力。通算融合算子开启重执行后，AI
  CPU在检测到环境异常时，通过下图示意的机制，通知AI Core重新下发通信任务，避免由于硬件闪断造成的通信中断，提升通信稳定性。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/fusion_operator_programming/general_fusion/特性场景.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 特性场景

## 重执行
为避免执行通信任务的环境中硬件闪断导致发生通信中断，通算融合算子可通过配置编译宏与环境变量，开启重执行能力。通算融合算子开启重执行后，AI CPU在检测到环境异常时，通过下图示意的机制，通知AI Core重新下发通信任务，避免由于硬件闪断造成的通信中断，提升通信稳定性。
当前，该能力的支持情况如下：
Ascend 950PR/Ascend 950DT不支持通算融合算子的重执行。
Atlas A3 训练系列产品/Atlas A3 推理系列产品支持通算融合算子的重执行。
Atlas A2 训练系列产品/Atlas A2 推理系列产品不支持通算融合算子的重执行。
开启重执行的条件如下：
-   通算融合算子的输出内存地址和输入内存地址不相同。
-   通算融合算子仅存在Server间通信（Server为计算节点，通常是8卡或16卡的昇腾NPU设备组成的服务器形态的统称）。
-   算子编译时，配置编译宏AICORE_EXCEPTION_RESTART，如下所示。具体的编译宏配置阶段和方式请参考支持自定义编译选项。
-   配置HCCL重执行环境变量HCCL_OP_RETRY_ENABLE，开启重执行的检测和上报能力，该环境变量的说明请参考HCCL_OP_RETRY_ENABLE。请在算子执行前设置该环境变量，具体配置如下：
注意，开启重执行后，若AI Core第一次下发通信任务后通信中断，默认只重执行一次。若需修改重执行次数或重传间隔时间，请参考HCCL_OP_RETRY_PARAMS。

<!-- cannbot:related:start -->
## 相关

- [通用融合算子实现](operator_impl.md)（`related`）：“当前通算融合算子暂不支持Kernel直调和入图（GE图）开发，仅支持单算子API调用。”限定通算融合的开发入口；“算子编译时，配置编译宏AICORE_EXCEPTION_RESTART”补充同类算子在支持平台启用通信重执行的构建条件。
<!-- cannbot:related:end -->
