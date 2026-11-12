---
type: Guide
title: SGLang NPU默认参数解析与容量分档边界
description: 从platform_hook与NPU默认解析说明ascend后端强制选择、page128、32/64GiB档的prefill和图batch默认，以及HiCache和对称内存限制。
tags:
- task.implementation
- topic.model_serving
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/utils/device.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/platform_hook.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/utils.py
  role: implementation
created_at: '2026-11-08T11:53:39Z'
updated_at: '2026-11-09T04:33:52Z'
platforms: []
aliases:
- set_default_server_args
- handle_npu_backends
---

# SGLang NPU默认参数解析与容量分档边界

## 解析路径

当解析视图device为npu时，handle_npu_backends调用set_default_server_args，通过declare_resolution写入解析结果，而不是直接把命令行字段看成最终值。Attention、Prefill Attention、Decode Attention均被该规则声明为ascend；page_size仅在未给值时默认128。

## 显存档位不是产品识别

get_npu_memory_capacity返回MiB：正的SGLANG_ZBAL_LOCAL_MEM_SIZE直接作为容量，否则取NPU总量。因此这里可能使用配置预算而非物理容量；默认规则按容量而非设备型号分档：不超过32×1024时，未指定chunked-prefill默认4096，decode图max_bs在TP<4时16、否则64；不超过64×1024时分别8192和64/256。超过64GiB的设备没有在这段代码里得到另一组默认值，后续解析可能继续处理。

容量注释列出历史910型号，但不能反向以容量识别A2/A3或据默认值认定任意长序列可运行。用户显式给出的chunked-prefill和decode max_bs不会在这些“is None”分支被替换；Attention三入口与disable_custom_all_reduce则是该规则声明的决议。最终还应查看解析冲突/锁定机制和打印结果。

## 通信与缓存约束

NPU默认禁用CustomAllReduce。enable_symm_mem仅CUDA/HIP支持，NPU会在平台规则中告警并关闭，因为该分配器编译CUDA/NCCL插件；这与其他NPU共享内存/MemFabric能力不是同一开关。

启用层次缓存、Decode offload，或disaggregation_mode=="decode"且retraction backup为None/host_pool时，默认HiCache IO为kernel_ascend。MLA选择page_first_kv_split，其他路径page_first_direct；在PD Decode模式仅设置host_pool备份也可能创建Host池；未启用层次缓存/offload的混部服务不因备份默认为None进入此分支，不能以未启用enable_hierarchical_cache断言无Host内存分配。

名字为pre_warm_nccl的配置在源码中也允许NPU；不能按名称将其排除，也不能据此说实际通信变为NCCL。

## 实施、回退和验证

保留启动参数与最终解析快照，对比page、图batch、chunk token和Host池后端，再逐项调节并测量峰值、TTFT/TPOT。缩小batch/token或关闭相关缓存/备份需同步验证功能；不要把容量档位默认当性能最优解。具体组件与平台版本见[安装版本组](/model/inference/guides/deployment/sglang_ascend/sglang_ascend_doc_installation_version_sets.md)。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
