---
type: Guide
title: 原生设备与流迁移：NPU名称、查询和产品差异
description: 区分设备和流方法的产品范围，并记录950DT已列启动环境、读取时机及能力查询的兼容含义。
tags:
- task.implementation
- topic.compilation
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-cuda.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-accelerator.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-cpu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-cpu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-cpu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-cpu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-cpu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-cpu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-cpu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-cpu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-cpu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-cpu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-cpu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-cpu.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-cpu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-cpu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/device_management/ACL_DEVICE_SYNC_TIMEOUT.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/device_management/ACL_DEVICE_SYNC_TIMEOUT.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/device_management/PYTORCH_HAL_BASED_NPU_CHECK.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/device_management/PYTORCH_HAL_BASED_NPU_CHECK.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/device_management/STREAMS_PER_DEVICE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/device_management/STREAMS_PER_DEVICE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/device_management/TORCH_DEVICE_BACKEND_AUTOLOAD.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/device_management/TORCH_DEVICE_BACKEND_AUTOLOAD.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/device_management/TORCH_NPU_DEVICE_CAPABILITY.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/device_management/TORCH_NPU_DEVICE_CAPABILITY.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/device_management/TORCH_TRANSFER_TO_NPU.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/device_management/TORCH_TRANSFER_TO_NPU.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/ASCEND_LAUNCH_BLOCKING.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/ASCEND_LAUNCH_BLOCKING.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TASK_QUEUE_ENABLE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/TASK_QUEUE_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/PER_STREAM_QUEUE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/PER_STREAM_QUEUE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/FORCE_OVERFLOW_CHECK.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/FORCE_OVERFLOW_CHECK.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/INF_NAN_MODE_ENABLE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/INF_NAN_MODE_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/INF_NAN_MODE_FORCE_DISABLE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/INF_NAN_MODE_FORCE_DISABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/performance_tuning/CPU_AFFINITY_CONF.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/performance_tuning/CPU_AFFINITY_CONF.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/pytorch_comparison.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/pytorch_comparison.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/NPU-Device.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/NPU-Device.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/NPU-Device.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/streams.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/streams.py
  role: implementation
created_at: '2026-11-09T13:09:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生设备与流迁移：NPU名称、查询和产品差异

## 固定版本与范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 中PyTorch2.7.1、2.9至2.14的中英文原生支持页及所指实现；收录/缺项、类/方法与产品标记分别保留，不将文档版本差异直接视为实际发行历史。产品为各条目明列的A2/A3训练系列与950DT，不扩展950PR，也不推导主线与26.0/PyTorch2.8或其他主线已配套。支持表不替代完整参数、底层能力和设备验证，未执行上游或NPU实验。

## CUDA名称的迁移边界

CUDA页要求对所列支持接口使用NPU形式：torch.cuda前缀换为torch_npu.npu或torch.npu，页面称这两种NPU调用方式功能一致。它不是任意CUDA生态、第三方库、所有同名属性或其他命名空间的自动迁移保证；例如Storage.cuda不是同一条前缀替换规则，torch.backends.cuda的具体设置也应单独核对。

StreamContext、can_device_access_peer、current_blas_handle/current_device、current_stream/default_stream、device/device_count/device_of、get_device_name/properties/capability、get/set_sync_debug_mode、init/is_available、set_device/set_stream/stream/synchronize、utilization在相应页列三类产品。中文还列get_stream_from_external、ExternalStream、device_memory_used、memory_usage、is_tf32_supported等，未给完整参数/返回规格的项目不能仅按名字补齐。is_bf16_supported中文2.10..2.14才收录，不据旧页缺项推定设备不支持BF16。

current_stream/default_stream未指定device时会隐式初始化当前设备，默认0卡。初始化/可用性、当前设备、同步和返回句柄是不同操作；查询调用成功不证明模型或跨设备访问已经可用。环境与ACL配置时机见[初始化指南](torch_npu_initialization_and_device_detection.md)，其A2/A3整体范围不由本API清单扩到950。

## 设备探测不能按CUDA属性猜硬件

get_device_capability由TORCH_NPU_DEVICE_CAPABILITY提供兼容值，不代表NPU硬件能力；所读Python实现还注明device参数无实际意义。get_device_properties只列name、total_memory、L2_cache_size、cube_core_num、vector_core_num，其余CUDA属性为空，不由空字段认定相关硬件物理不存在。

is_initialized中文仅列A2/A3，英文明确950DT不支持；固定实现只是返回_initialized且不在bad fork，没有这个函数内的SoC分支。保留文档产品表与静态函数层次，不由Python函数存在覆盖产品表或宣称950调用已验证。

temperature/power_draw/clock_rate中文列三类产品支持，英文均列三类产品不支持，两侧都提示可用npu-smi info -t common -i <id>分别看Temperature(C)、NPU Real-time Power(W)、Aicore curFreq(MHZ)。这组材料有支持标记分歧，不能据中文表构造已验证的API采样器；本文未运行CLI或监控设备。

## Stream和Event的子方法

Stream类列三类产品；query/record_event/synchronize/wait_event在中文有三类产品表，英文只重复部分方法。wait_stream中文仅列A2/A3、英文明确950DT不支持。Event的elapsed_time/from_ipc_handle/query/wait列三类产品，record/synchronize在中文另列；ipc_handle明确950DT不支持。from_ipc_handle支持不能反过来证明同产品能导出句柄或跨进程全流程成立。

_sanitizer.enable_npu_sanitizer的对应CUDA条目中文仅列A2/A3，英文明确950DT不支持；不将它与所有调试/安全工具混成同一开关。工具名、方法注册和真正跨流依赖分别核对，图内同步另见[多流依赖](../torchair/graph_multistream_dependencies.md)。

## Accelerator与CPU命名空间

accelerator的device_count/is_available/current_accelerator/current_device_index/set_stream/current_stream/synchronize列三类产品，device_index从2.11..2.14收录。set_device_index/set_device_idx/current_device_idx在2.7.1及2.9..2.12中文只列A2/A3、英文明确950不支持，2.13/2.14列三类产品；current_device_index不与_idx取统一版本矩阵。

英文2.9/2.10/2.14提示set_device_idx/current_device_idx弃用，迁移到_index形式；get_device_capability只在英文2.12..2.14收录，三类产品均不支持，不能用前述npu.get_device_capability替它补表。

cpu.stream、StreamContext、Stream列三类产品；cpu.current_stream/is_available/synchronize/device_count中文只列A2/A3、英文明确950不支持。该清单口径不等于950机器没有CPU或Host预处理能力，也不等于CPU Stream就是NPU Stream。

## 其他兼容入口的有限信息

中文CUDA页还对comm.broadcast/broadcast_coalesced/reduce_add、nvtx.range_push/range_pop/range、jiterator._create_multi_output_jit_fn、tunable的is_enabled/tuning_is_enabled/record_untuned_enable/record_untuned_is_enabled/get_max_tuning_duration/get_max_tuning_iterations/set_filename/get_filename/get_validators/tune_gemm_in_file/get_rotating_buffer_size，以及gds.gds_deregister_buffer、GdsFile的register_handle/deregister_handle/save_storage列三类产品；tunable.write_file_on_exit仅2.7.1/2.9收录。英文未列大部分这些项，comm.scatter/gather则明确三类产品均不支持。

这些条目没有完整NPU实现、Kernel编译、文件/句柄、通信或实际调优协议，不能据通用前缀规则宣称Jiterator/TunableOp/GPUDirect Storage整套能力已可用。NVTX范围条目与[autograd.emit_nvtx/emit_itt的独立不支持表](../../../../training/guides/torch_npu_native_autograd_profiler.md)也不是同一接口。

## 验收

固定真实包、NPU形式、设备/线程/流、方法及消费者，检查实际初始化、属性、事件/依赖和错误，再比较同步、拷贝与稳态开销。支持清单和兼容返回值不能代替真实执行证据，本文未访问活跃设备、流或句柄。

## torch根Stream和Event类的支持粒度

同提交七份中文torch页对torch.Stream/torch.Event类列三产品，英文torch页未收录；2.7.1/2.9放在Generators章节，2.10至2.14改为Accelerators章节，目录位置变化不证明实现迁移。类级表没有给所有方法、默认设备、流优先级和事件时间测量规格，不覆盖前文torch.npu方法与子项的产品例外。

## 950DT已列的启动环境与读取阶段

固定主线中英文环境页对下列六项均明确列A2/A3及950DT；与ACL初始化JSON页未列950的范围分开，不由某个设备查询成功推导全部初始化配置已支持。

| 变量 | 值和默认 | 读取/使用条件 |
| --- | --- | --- |
| TORCH_DEVICE_BACKEND_AUTOLOAD | 未配或严格1开启，其他值关闭 | PyTorch≥2.5及pip entry point；首次import torch前设置，源码PYTHONPATH无安装元数据不生效；导入注册与设备懒初始化不同 |
| TORCH_TRANSFER_TO_NPU | 默认0；仅0/1，其他值ValueError | import torch前设置；1替换CUDA相关入口，不证明全部CUDA语义或算子已等价迁移 |
| PYTORCH_HAL_BASED_NPU_CHECK | 严格1使用HAL，其他/未配用Runtime | 首次is_available前设置；HAL动态库与可见设备解析失败则回Runtime，Runtime首次非零设备数缓存 |
| TORCH_NPU_DEVICE_CAPABILITY | 默认未配返回None；配置major.minor | 仅兼容CUDA返回值，不代表硬件实际指令或类型能力 |
| STREAMS_PER_DEVICE | 默认32；只接受8/32，其他值告警回32 | 流池Round Robin，不是任意流数调优合同 |
| ACL_DEVICE_SYNC_TIMEOUT | 秒，1..2147483，未配用设备默认 | 控制设备同步等待，不替代HCCL连接/执行超时，也不修复依赖死锁 |

本表仅摄取这些环境页的限定合同，未导入包、加载HAL库、修改环境或初始化设备。完整A2/A3初始化流程见[初始化指南](torch_npu_initialization_and_device_detection.md)。

## 950DT执行、队列与Host绑核环境

按中英文详情页区分环境支持和整套运行模式，不能由流API列支持推导所有优化组合可用：

| 配置 | 明确的产品/执行条件 |
| --- | --- |
| ASCEND_LAUNCH_BLOCKING | A2/A3/950DT，默认0异步；1同步给正确栈但降速并关闭TaskQueue，0可能增加内存及OOM风险 |
| TASK_QUEUE_ENABLE | A2/A3/950DT，默认1；0主线程全部下发，1将主要aclnn调用放二级流水，2再移workspace且仅二进制场景生效，可能增加显存峰值。默认每设备一队列，跨流依赖倒序入队可死锁 |
| PER_STREAM_QUEUE | A2/A3/950DT，实验功能，默认0、1每流一队列，必须TASK_QUEUE为1/2；不据此保证多流一定并发或解除依赖 |
| CPU_AFFINITY_CONF | 通用绑核页列A2/A3/950DT，0/未配关闭、1粗粒度、2细粒度；CPU核按卡均分，可定制闭区间，force1仅跳过软件冲突检测，不能突破OS/Cgroup；npu_affine1子模式**仅A2**。完整每流队列与细粒度组合仍独立核对 |
| FORCE_OVERFLOW_CHECK | 页列A2/A3/950DT，默认0、1在Inf/NaN模式检测而不改变计算模式，其他值视作未配；要求CANN≥9.1，旧版告警忽略；启动前设置且有性能开销。950DT不能通过get_npu_overflow_flag等接口查询状态，需ASCEND_GLOBAL_LOG_LEVEL=1的plog中aclrtSetStreamOverflowSwitch记录 |
| INF_NAN_MODE_ENABLE / FORCE_DISABLE | 950DT只支持Inf/NaN模式，这两个切换变量对它无效；A2/A3的饱和模式教程不适用950。无效不等于可通过设置变量强制启用950饱和模式 |

COMBINED_ENABLE与ACL Op编译缓存详情页未列950，Eager DVM融合页只列A2/A3，不能从上述队列支持补齐它们的范围；缺项与明示不支持仍分别记录。[CPU fallback与一致性实现](torch_npu_cpu_fallback_and_compatible_impl.md)是另一组已列950DT的路径选择，不代表禁用全部Host工作。

## PyTorch变量对照的含义

同提交对照页将TORCH_DEVICE_BACKEND_AUTOLOAD列为同名配置；PYTORCH_HAL_BASED_NPU_CHECK参考PYTORCH_NVML_BASED_CUDA_CHECK的取值和探测模式，但HAL与NVML不是同一个动态库，也不是变量自动互为别名。ASCEND_LAUNCH_BLOCKING对应CUDA同步调试功能仍按NPU变量配置。对照依配套PyTorch版本核验，名字接近不证明硬件能力或全部执行行为一致。

## OpPlugin设备目录与主线ExternalStream补充

两固定OpPlugin Device页把get_device_capability标为预留、默认None；这与固定TorchNPU兼容变量可返回major.minor是不同证据层，均不能用于推定真实CUDA指令能力。设备目录没有补齐其他11个名字的完整签名或健康诊断合同。

独立TorchNPU主线streams.py新增ExternalStream(stream_ptr,device=None)，不管理外部流寿命；priority/is_sync_launch须保留0。其docstring明确拒绝同步/查询、事件record/wait、Tensor.record_stream、图捕获/任务组、SuperKernel、Host callback及report订阅等路径，调用者需外部追踪完成并保持流活着。原因是外部流不在内部AsyncTaskQueue管理范围；不能由它继承Stream或CUDA列表列支持就推定具备完整内部流能力，发布streams.py没有此类。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-cuda.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-cuda.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-cuda.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-cuda.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-cuda.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-cuda.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-cuda.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-cuda.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-cuda.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-cuda.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-cuda.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-cuda.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-cuda.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-cuda.md)（constraint）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-accelerator.md)（constraint）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-accelerator.md)（constraint）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-accelerator.md)（constraint）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-accelerator.md)（constraint）
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-accelerator.md)（constraint）
- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-accelerator.md)（constraint）
- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-accelerator.md)（constraint）
- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-accelerator.md)（constraint）
- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-accelerator.md)（constraint）
- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-accelerator.md)（constraint）
- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-accelerator.md)（constraint）
- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-accelerator.md)（primary）
- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-accelerator.md)（constraint）
- [固定来源 28](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-accelerator.md)（constraint）
- [固定来源 29](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-cpu.md)（constraint）
- [固定来源 30](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-cpu.md)（constraint）
- [固定来源 31](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-cpu.md)（constraint）
- [固定来源 32](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-cpu.md)（constraint）
- [固定来源 33](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-cpu.md)（constraint）
- [固定来源 34](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-cpu.md)（constraint）
- [固定来源 35](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-cpu.md)（constraint）
- [固定来源 36](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-cpu.md)（constraint）
- [固定来源 37](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-cpu.md)（constraint）
- [固定来源 38](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-cpu.md)（constraint）
- [固定来源 39](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-cpu.md)（constraint）
- [固定来源 40](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-cpu.md)（primary）
- [固定来源 41](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-cpu.md)（constraint）
- [固定来源 42](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-cpu.md)（constraint）
- [固定来源 43](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py)（implementation）

- [固定来源 44](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md)（constraint）

- [固定来源 45](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md)（constraint）

- [固定来源 46](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md)（constraint）

- [固定来源 47](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md)（constraint）

- [固定来源 48](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md)（constraint）

- [固定来源 49](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md)（constraint）

- [固定来源 50](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md)（constraint）

- [固定来源 51](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md)（constraint）

- [固定来源 52](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md)（constraint）

- [固定来源 53](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md)（constraint）

- [固定来源 54](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md)（constraint）

- [固定来源 55](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md)（primary）

- [固定来源 56](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md)（constraint）

- [固定来源 57](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md)（constraint）

- [固定来源 58](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/device_management/ACL_DEVICE_SYNC_TIMEOUT.md)（primary）

- [固定来源 59](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/device_management/ACL_DEVICE_SYNC_TIMEOUT.md)（constraint）

- [固定来源 60](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/device_management/PYTORCH_HAL_BASED_NPU_CHECK.md)（primary）

- [固定来源 61](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/device_management/PYTORCH_HAL_BASED_NPU_CHECK.md)（constraint）

- [固定来源 62](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/device_management/STREAMS_PER_DEVICE.md)（primary）

- [固定来源 63](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/device_management/STREAMS_PER_DEVICE.md)（constraint）

- [固定来源 64](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/device_management/TORCH_DEVICE_BACKEND_AUTOLOAD.md)（primary）

- [固定来源 65](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/device_management/TORCH_DEVICE_BACKEND_AUTOLOAD.md)（constraint）

- [固定来源 66](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/device_management/TORCH_NPU_DEVICE_CAPABILITY.md)（primary）

- [固定来源 67](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/device_management/TORCH_NPU_DEVICE_CAPABILITY.md)（constraint）

- [固定来源 68](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/device_management/TORCH_TRANSFER_TO_NPU.md)（primary）

- [固定来源 69](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/device_management/TORCH_TRANSFER_TO_NPU.md)（constraint）

- [固定来源 70](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/ASCEND_LAUNCH_BLOCKING.md)（primary）

- [固定来源 71](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/ASCEND_LAUNCH_BLOCKING.md)（constraint）

- [固定来源 72](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TASK_QUEUE_ENABLE.md)（primary）

- [固定来源 73](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/TASK_QUEUE_ENABLE.md)（constraint）

- [固定来源 74](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/PER_STREAM_QUEUE.md)（primary）

- [固定来源 75](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/PER_STREAM_QUEUE.md)（constraint）

- [固定来源 76](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/FORCE_OVERFLOW_CHECK.md)（primary）

- [固定来源 77](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/FORCE_OVERFLOW_CHECK.md)（constraint）

- [固定来源 78](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/INF_NAN_MODE_ENABLE.md)（primary）

- [固定来源 79](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/INF_NAN_MODE_ENABLE.md)（constraint）

- [固定来源 80](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/INF_NAN_MODE_FORCE_DISABLE.md)（primary）

- [固定来源 81](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/INF_NAN_MODE_FORCE_DISABLE.md)（constraint）

- [固定来源 82](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/performance_tuning/CPU_AFFINITY_CONF.md)（primary）

- [固定来源 83](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/performance_tuning/CPU_AFFINITY_CONF.md)（constraint）

- [固定来源 84](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/pytorch_comparison.md)（constraint）

- [固定来源 85](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/pytorch_comparison.md)（constraint）

- [固定来源 86](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/NPU-Device.md)（constraint）

- [固定来源 87](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/NPU-Device.md)（primary）

- [固定来源 88](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/NPU-Device.md)（constraint）

- [固定来源 89](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/streams.py)（implementation）

- [固定来源 90](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/streams.py)（implementation）
