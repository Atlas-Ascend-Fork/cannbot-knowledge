---
type: Guide
title: SGLang ACL Host回调辅助线程的订阅与退出边界
description: 解释按NPU设备缓存report线程、stream指针提取、process_report驱动和显式注册前置条件，不把helper存在当默认启用。
tags:
- task.implementation
- topic.implementation.callback
- topic.implementation.resource_lifecycle
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/sparsity_driven_kv_offload/host_callback.py
  role: primary
created_at: '2026-11-08T11:53:42Z'
updated_at: '2026-11-08T11:53:42Z'
platforms: []
aliases:
- register_npu_host_callback_stream
---

# SGLang ACL Host回调辅助线程的订阅与退出边界

register_npu_host_callback_stream为指定设备惰性建立reporter并订阅stream；device.index缺失时取当前NPU。辅助线程先torch.npu.set_device，再尝试acl.rt.set_device，保存Python thread ident、发ready事件，再循环process_report(100)。这是一条显式helper，不是import模块就自动开线程或所有稀疏KV路径都已调用它的证明。

原始stream指针依次尝试npu_stream、stream_ptr、cuda_stream属性，可为方法或数值；全部缺失报错。命名cuda_stream在此仅兼容属性名，不代表stream是CUDA。subscribe_report返回非0会报错，成功指针记入集合避免重复订阅。

每设备reporter缓存在进程字典，atexit执行close；退出对已订阅流逐个unsubscribe（异常忽略），清集合、发stop并join最多1秒。daemon/超时join不是已证明所有Host callback执行完或所有Device任务排空，资源释放顺序仍需调用方验证。全局reporter创建和订阅集合未显式加锁，不应推导任意并发Host调用安全。

验证应覆盖属性兼容、重复订阅、返回错误、不同设备、退出时仍有回调与资源所有权；只有确需Host callback的调用路径才启用该服务。不能因有report线程把Device拷贝完成等同CPU对象生命周期已安全。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
