---
type: Optimization
title: SGLang稀疏KV卸载的模型准入与预算分离
description: 说明SGLANG_NPU_ENABLE_SPARSE_KV_OFFLOAD的Ascend双阶段DSA/MLA门槛、显式并发上界、indexer-only设备cell预算和Host容量代价。
tags:
- task.optimization
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/sparsity_driven_kv_offload/config.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/sparsity_driven_kv_offload/manager.py
  role: implementation
created_at: '2026-11-08T11:53:41Z'
updated_at: '2026-11-08T11:53:41Z'
platforms: []
---

# SGLang稀疏KV卸载的模型准入与预算分离

## 触发条件与规则

SGLANG_NPU_ENABLE_SPARSE_KV_OFFLOAD未开时准入函数直接False；开后必须NPU、Prefill与Decode后端均ascend、使用MLA并且配置为DSA家族（例DeepSeekV3.2、GLM5.x），否则抛ValueError而非静默回退。max_running_requests必须显式非None，为每进程Host KV容量提供上界；这不是任意模型都可用的通用CPU卸载开关。

每请求device sparse window来自模型index_topk且必须>0；index_head_dim优先ModelConfig字段，否则从HF配置读取，也必须>0。关闭native KV并不关闭所有device占用：cell_size返回index_head_dim×实际indexer层数×element_size，若elide无需TopK层则按对应模型层跳过；它只计算该部分设备cell，不包含完整Host池、selected buffer、slot map或工作区。

## 容量代价

SparseKVCacheManager仍按请求池实际行数（含padding）分配每层Host完整上下文KV、device TopK窗口和int32槽位映射；Host容量随max_requests×max_context×层数×KV宽度增长。减设备常驻KV不等于总内存变小或可无限并发；Host分配失败错误提示应缩小max-running-requests。

## 实施、回退与验证

先确认HF模型属于DSA、两个阶段后端、MLA和显式并发上界，再比较native与offload的真实device/Host分配、TTFT/TPOT、命中率与拷贝区间；带长prefix和多请求重用槽位验证精度。回退须关闭env并重建native KV池/进程，不能对已分配None的K/V直接改开关继续调用getter。量化、PD、CP、投机等组合另由实际分支验证，不能从env准入成功推导全部支持。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
