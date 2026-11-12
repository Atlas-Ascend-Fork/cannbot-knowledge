---
type: Guide
title: SGLang Diffusion NPU平台：设备映射、探测与后端选择
description: 说明平台插件优先级、可见设备、no_grad语义、内存查询及NPU通信类与注意力路由的实际边界。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/platforms/npu.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/platforms/__init__.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/platforms/interface.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/distributed/device_communicators/cpu_communicator.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/distributed/device_communicators/cuda_communicator.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/distributed/device_communicators/pynccl.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/distributed/parallel_state.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/distributed/group_coordinator.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/distributed/device_communicators/base_device_communicator.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/distributed/device_communicators/ipc_a2a.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/test/unit/test_single_rank_device_group.py
  role: implementation
created_at: '2026-11-08T12:26:52Z'
updated_at: '2026-11-08T12:37:01Z'
platforms: []
---

# SGLang Diffusion NPU平台：设备映射、探测与后端选择

## 场景与选择流程

部署同包中的Diffusion时先确认current_platform。显式SGLANG_DIFFUSION_PLATFORM_OVERRIDE选择builtin或安装插件；自动探测优先外部插件，再按内置顺序探测，NPU依靠torch.npu.is_available。覆盖平台不会安装缺少的运行时。ASCEND_RT_VISIBLE_DEVICES将逻辑序号映射到物理设备，空字符串意味着无可用设备并报错；容器、local_rank与可见列表需共同核对。

NPU平台的inference_mode实际返回torch.no_grad，保留tensor version counter供缓存失效检查；不要替换成torch.inference_mode。平台不支持float64，默认不启用DiT layerwise offload，也不宣称full NVLink连接。

## 运算与通信

显式FA选择AscendFA；LASER、BLOCK_SPARSE_ATTN、RAIN_FUSION_ATTN要求attentions包，否则报安装错误；未命中选择SDPA。get_device_communicator_cls返回名为CudaCommunicator的通用类，all-to-all选择CpuCommunicator；名称不能证明NPU走CUDA/NCCL或一定D2H。前者在PyNccl不可用时回退torch.distributed，后者的张量集合通信也使用device_group，需以实际backend核对HCCL。

## 内存与验收

free memory查询可先empty_cache，再读mem_get_info；分布式返回各rank的最小值，使用NPU FP32标量归约。get_current_memory_usage会先reset_peak_memory_stats，不能把该值解释为进程全生命周期峰值。启动时记录最终平台类、设备ID、实际attention类和通信backend，再测试一个小请求以及可见设备重排。这里只核对固定源码，没有启动服务；各子功能缺少统一产品矩阵，平台范围保持未知。

## HCCL、单rank与SP通信依赖

Platform接口为NPU返回hccl，init_distributed_environment未显式backend时消费该值；device_group承载加速器tensor，cpu_group另用gloo协调。new_device_group对单rank一律选择gloo，集合通信在world_size=1时短路；不能据单rank测试证明NPU多rank HCCL已运行。CUDA custom allreduce只对cuda_alike打开。

AllToAll4D以连续4D张量做head与sequence轴交换：scatter head要求head数整除组大小，逆向要求sequence整除组大小，经过transpose/reshape和dist.all_to_all_single恢复目标布局。两rank IPC快路在ipc_a2a_ready显式要求current_platform.is_cuda且TP1，NPU返回False，进入device group的常规集合通信；日志里的NCCL字样不是NPU实际backend证据。纯Ulysses可用over_group复用已有communicator和单rank Ring组，该view不拥有process group，不能独立destroy造成双重释放。验收需核对TP/SP组成员、整除关系与销毁所有者，本次未初始化进程组。
