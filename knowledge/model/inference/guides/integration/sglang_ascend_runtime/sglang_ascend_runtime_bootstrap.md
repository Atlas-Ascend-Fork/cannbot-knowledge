---
type: Guide
title: SGLang NPU分布式初始化顺序与KV显存基线
description: 说明NPU补丁、设备选择、进程组、通信预热和模型加载前显存测量的先后关系，以及draft不能参与WORLD测量的原因。
tags:
- task.implementation
- topic.parallelism
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/distributed/bootstrap.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/platforms/device_mixin.py
  role: supporting
created_at: '2026-11-08T12:07:25Z'
updated_at: '2026-11-08T12:07:25Z'
platforms: []
aliases:
- init_parallel_runtime
- measure_pre_model_load_memory
---

# SGLang NPU分布式初始化顺序与KV显存基线

init_parallel_runtime要求每进程执行一次，draft复用target组不可重复调用。先init_npu_backend安装兼容补丁，再解析平台通信backend、rendezvous与归约标志，选择本地设备，然后初始化共享传输引擎与WORLD/模型并行组。重复初始化guard在工作开始前设定，异常后不是可自由重试的事务；新进程更利于排除残留组与补丁。

rendezvous优先SGLANG_DISTRIBUTED_INIT_METHOD_OVERRIDE，再dist_init_addr，最后服务host/端口。NPU组建立后register_sgl_tp_rank实际传gpu_id，供IPC设备索引重建使用；不能把它简单等同全局TP rank。

pre_warm_nccl名称在这里也覆盖HCCL：配置开启且TP/PP/EP任一>1时，对TP设备组做一次all_reduce再平台同步。warmup源码仍写torch.cuda接口，依赖前置NPU兼容补丁；它没有逐一演练所有PP点对点、EP大消息或每个通信算法。TP LM-head A2A和EPLB P2P的额外预热有明确device==cuda守卫，不能作为NPU已预热证据。

模型加载前测量应在通信初始化后，调用分布式可用显存MIN以计入常驻通信资源，再加载权重和分配KV。draft可能只存在某PP阶段，不参与WORLD归约，避免缺席peer死锁；TP主worker还检查显存不平衡。各rank应记录同一时刻、同一单位的基线，不能拿刚启动未建组显存估算稳态KV容量。

验证先看设备映射、rendezvous、组与预热日志，再检查加载前后基线与首请求额外分配；回退预热或通信配置后重新测量KV预算，不沿用旧进程统计。

## ZBAL通信后端选择

DeviceMixin的设备到分布式后端映射在模块初始化时根据SGLANG_ZBAL_LOCAL_MEM_SIZE选择NPU的hccl或zbal。环境必须在相关模块导入前一致设置，不能把正预算模式仍一律称HCCL；KV基线与GVA初始化也应采用相同allocator模式。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
