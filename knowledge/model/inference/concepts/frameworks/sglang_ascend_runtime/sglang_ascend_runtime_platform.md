---
type: Concept
title: SGLang NPU平台能力声明与设备统计口径
description: 说明NPUSRTPlatform的Ascend默认后端、Triton/图能力声明、固定零设备capability和峰值显存口径，区分软件接口与硬件验收。
tags:
- task.implementation
- topic.architecture
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/platforms/npu.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/configs/device_config.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/utils/torch_npu_patch_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/platforms/__init__.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/platforms/device_mixin.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/runner/eager_runner.py
  role: supporting
created_at: '2026-11-08T11:53:38Z'
updated_at: '2026-11-08T11:53:38Z'
platforms: []
aliases:
- NPUSRTPlatform
- NPUDeviceMixin
---

# SGLang NPU平台能力声明与设备统计口径

## 平台接口

`NPUSRTPlatform`继承NPUDeviceMixin与SRTPlatform，设备名/类型/dispatch key均为npu，默认Attention为ascend。`PlatformCapabilities(supports_triton=True,graph_capture=True)`是该平台对象的软件能力声明，不是每种芯片、模型或Kernel组合均已通过图捕获/精度的报告。

DeviceConfig接受npu和其他注册设备，构造torch.device并记录gpu_id；参数名gpu_id不能用来判断CUDA。设备设置、同步、清缓存、总容量和free/total查询委托torch.npu。

## 统计与兼容占位

`get_device_capability()`固定返回DeviceCapability(0,0)，源码说明TorchNPU能力值可由TORCH_NPU_DEVICE_CAPABILITY控制，只为PyTorch兼容而不代表实际NPU能力。不得用0,0推断无Cube/无Triton，也不得把环境值当NVIDIA SM或产品代际。

`get_current_memory_usage`调用max_memory_allocated，口径是分配峰值，不是当前存活、系统已用或剩余显存；剩余空间用mem_get_info。设备properties中的total_memory、uuid和name分别保留各自语义。pin-memory可用性函数仅在传入对象字符串恰为cpu时返回False，否则True，它不是逐硬件实测探针。

## 补丁兼容与复核

`apply_torch_npu_patches`优先调用旧API `_apply_patches(patches)`，没有时调用 `_apply_all_patches()`，两者皆无才抛AttributeError；新入口不接收原patch列表，不能声称两版本逐条补丁完全等价。该helper也不负责自动import或执行安装。

排查时先核对实际current_platform、device类型和后端选择，再看是否为对应算子支持的硬件/软件组合；日志中峰值/剩余指标要分开。验证应覆盖NPU平台选择、旧/新patch API、未知后端及统计口径，不能以平台类可构造代替模型验收。

## 平台选择与执行模式

平台插件由显式配置/激活结果优先决定；无插件时CPU显式opt-in先于硬件探测，CUDA在NPU前，多个插件激活需显式选择。_is_npu_available仅布尔判断，不等同utils.is_npu的不可见抛错合同。EagerRunner保留NPU MIXED模式供专门kernel消费，其他无CP平台可将MIXED改EXTEND，移植时不能统一重写。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
