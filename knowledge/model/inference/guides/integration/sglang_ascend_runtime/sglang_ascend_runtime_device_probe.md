---
type: Guide
title: SGLang NPU探测、显存查询与设备模块选择
description: 区分torch_npu不可见时报错、ZBAL容量和可用显存口径、分布式最小值与GiB/MiB单位，以及避免CUDA初始化的设备模块解析。
tags:
- task.implementation
- topic.memory
- topic.architecture
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/utils/device.py
  role: primary
created_at: '2026-11-08T12:04:52Z'
updated_at: '2026-11-08T12:04:52Z'
platforms: []
aliases:
- get_available_gpu_memory
- get_npu_memory_capacity
---

# SGLang NPU探测、显存查询与设备模块选择

is_npu是进程内缓存：没有torch.npu返回False；存在但is_available为False则抛RuntimeError，不能理解成自动降级CPU。get_device先检查其他可用平台再NPU，NPU返回npu或npu:id；get_device_module通过平台探测选择torch.npu，源码特意避免无参torch.get_device_module隐式初始化CUDA破坏fork。

get_available_gpu_memory的NPU分支校验编号，当前设备不同仅告警，不主动切换；可选empty_cache只释放allocator未用块，不清KV/radix/request缓存，也不释放活Tensor。正的ZBAL_LOCAL_MEM_SIZE且非mix时用zbal mem_get_info；mix模式因GVA可能尚未初始化改用torch.npu。最终返回GiB，distributed=True还在cpu_group上对各rank字节值做MIN，不是总和或均值。

get_npu_memory_capacity返回MiB：正的SGLANG_ZBAL_LOCAL_MEM_SIZE直接作为容量，否则torch.npu.mem_get_info总量除1024²。因此默认32/64GiB分档可能基于配置预算，不能总叫物理显存容量。OOM分析应区分总量、当前可用、峰值、配置预算与跨rank最小值。

异步H2D/D2H helper使用平台pin-memory策略和non_blocking；async_d2h在CPU无需复制，不能pin时直接to(cpu)，可pin则记录源Tensor current_stream。方法返回不表示Host结果已可读，消费者还需正确同步。验证以真实worker可见设备、单位和stream完成为准，不靠函数名中的gpu/cuda判平台。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
