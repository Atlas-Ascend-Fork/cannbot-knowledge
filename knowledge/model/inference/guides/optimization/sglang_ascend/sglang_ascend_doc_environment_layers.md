---
type: Guide
title: SGLang Ascend 环境变量：框架、DeepEP与DSPARK路径的作用域
description: 区分MLAPO/FIA NZ、多流、权重格式、DeepEP分组缓冲、MemFabric和DSPARK目标/draft注意力开关，避免以同名变量推导跨层保证。
tags:
- task.implementation
- topic.architecture
- topic.attention
- topic.implementation.synchronization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/reference/environment_variables.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/references/environment_variables.mdx
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/mla_preprocess.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/memory_pool_npu.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_backend.py
  role: implementation
created_at: '2026-11-08T11:50:28Z'
updated_at: '2026-11-09T04:34:34Z'
platforms: []
---

# SGLang Ascend 环境变量：框架、DeepEP与DSPARK路径的作用域

## 消费层决定含义

本页保存当前Ascend reference给出的变量作用域，来源没有逐变量完整产品支持表，保持平台未定位草稿。设置变量不证明所选模型实际消费了该路径，也不等于相应外部Kernel已安装。

框架直接读取 SGLANG_NPU_USE_MLAPO 用于 MLA 预处理。文档要求 SGLANG_USE_FIA_NZ 与其同时开启，但固定实现两个 helper 各读各自变量，并无强制依赖；普通 MLA writer 也能写 NZ，适用范围仍限对应缓存布局与 FIA 注意力分支，不能据独立开关泛化所有布局/consumer。SGLANG_NPU_USE_MULTI_STREAM可覆盖共享/路由专家以及DSA索引器的不同双流路径，不能只看一个全局变量就声称所有层已重叠。SGLANG_NPU_DISABLE_ACL_FORMAT_WEIGHT关闭特定NPU权重格式转换，非通用关闭KV缓存。

## Kimi-K3 DSPARK的两个独立注意力路径

SGLANG_NPU_USE_FLASH_MLA只选择DSPARK target-model MLA验证路径，不应用于draft或普通非投机decode；ASCEND_USE_PAGED_MTP选择DSPARK draft MHA注意力，不改变主模型。二者都覆盖其对应eager和graph replay路径，可独立启用；需安装导出flash_mla、flash_mla_metadata、paged_mtp_attention_decode的sgl-kernel-npu。

减少CPU序列长度镜像还要同时开启两条Kernel路径并设置SGLANG_NPU_ATTN_BACKEND_NEEDS_CPU_SEQ_LENS=0，其默认是1。只开启两个Kernel不自动关闭CPU镜像；关闭任一开关应回到该worker已有路径，不能对所有AttentionBackend移除Host更新。

## DeepEP、Runtime与传输层

长序列normal dispatch由DEEPEP_NORMAL_LONG_SEQ_PER_ROUND_TOKENS（文档默认8192）和DEEPEP_NORMAL_LONG_SEQ_ROUND（默认1）控制，combine另有DEEPEP_NORMAL_COMBINE_ENABLE_LONG_SEQ。MOE_ENABLE_TOPK_NEG_ONE针对-1专家编号。DEEP_NORMAL_MODE_USE_INT8_QUANT已标弃用，其未来自动推导计划不证明本次实现已自动推断。

DEEPEP_HCCL_BUFFSIZE在SGLang文档中用于DeepEP通信组，未设置回退HCCL_BUFFSIZE再回退200；这与Kernel库自己的前置校验层不是同一资源创建职责。LL dispatch token容量、HCCL字节缓冲与KV池互不替代。

TASK_QUEUE_ENABLE、INF_NAN_MODE_ENABLE、STREAMS_PER_DEVICE、PYTORCH_NPU_ALLOC_CONF和ASCEND_LAUNCH_BLOCKING分别涉及任务队列、数值模式、流池、分配器和同步调试；默认/具体可接受值仍需匹配CANN与torch_npu。PD传输store和HCCL/GLOO网络接口各自配置，不能只改store就认为分布式通信完成。

## 验证和回退

各rank启动前记录有效变量、模型分支、版本与外部依赖。以来源允许的最小配置为基线，核对实际调用路径、CPU镜像是否更新、输出精度及任务/通信时间，再逐项回退开关；不以日志存在变量证明Kernel被执行。本次未运行源码、探测设备或采集性能。

## 通用环境变量页中的 NPU 小节

通用页还列关闭ACL格式权重转换、MLAPO/multistream、Skywork-Reward-Gemma-2-27B-v0.2专用native GELU-tanh/Gemma RMSNorm、QLoRA后才all-gather以及ZBAL内存/bootstrap。模型专用开关不应推广到全部Gemma或全部950。Mooncake物理ID默认-1可自动检测，与旧PD页要求手设并不等同每种容器映射都正确，应核对进程可见和物理设备。

该页“NPU”标题下还混有实验TRT-LLM LoRA和triton_v2双graph的说明，标题本身不是NPU实现支持证明；不能直接把这些GPU依赖开关当Ascend优化。以实际backend和目标模型路径为准。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/reference/environment_variables.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/reference/environment_variables.mdx)（primary）
- [sglang：docs/docs/references/environment_variables.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/references/environment_variables.mdx)（supporting）
