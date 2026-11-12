---
type: Guide
title: SGLang HCCL进程组、量化归约与通信缓冲区分配
description: 说明NPU独立MoE EP组、HCCL缓冲区参数优先级、自定义组的全局参与约束和INT8 all-gather后归约的代价。
tags:
- task.implementation
- topic.parallelism
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/distributed/parallel_state.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/validation_hook.py
  role: supporting
created_at: '2026-11-08T12:07:25Z'
updated_at: '2026-11-08T12:07:25Z'
platforms: []
aliases:
- DEEPEP_HCCL_BUFFSIZE
- quant_all_reduce
---

# SGLang HCCL进程组、量化归约与通信缓冲区分配

## 组的构造

NPU coordinator设备取npu:local_rank；模型并行组默认不用PyNCCL。NPU即使moe_ep_size等于TP也单独创建MoE EP组，不复用TP组。world_size要求等于TP×PP；DCP允许NPU且要求TP可被DCP整除，但此处只证明组构造，不能替代attention后端、KV布局和PD路径约束。

get_torch_distributed_pg_options仅为默认组或名称含moe的组创建HCCL Options，hccl_buffer_size优先取非空DEEPEP_HCCL_BUFFSIZE，再HCCL_BUFFSIZE，再200，并直接int转换。它影响SGLang进程组申请，与sgl-kernel-npu自身的DeepEP前置检查是不同消费者，不能把两处默认/检查范围混成一个参数合同；也不能假定所有TP/CP组都接收该Options。

create_custom_parallel_group要求WORLD所有rank一致参与构组顺序。NPU在连续、对齐且等长分区时本地推导组，避免默认HCCL组的all_gather_object另分配缓冲；其他情况先WORLD收集配置再按排序逐组new_group。仅部分rank传局部子集可能导致不同分支或死锁，快路径不等于允许局部调用。

## 量化通信

enable_quant_communications校验仅NPU且TP>1。quant_all_reduce在单rank原样返回；npu_dynamic_quant不能导入则普通inplace归约，否则逐行INT8量化，all-gather量化Tensor及scale，还原到原dtype后按rank求和。它是低精度传输加全精度还原归约，不是HCCL原生INT8 SUM；需额外world_size倍gather缓冲和量化/反量化开销。

输入输出shape、scale广播、极值/小幅值误差及完整模型精度应独立验证；吞吐收益随消息大小、TP和网络而变。回退关闭量化通信并重启，记录组数、缓冲配置和启动空闲显存，避免把更多HCCL组的常驻内存误算为KV泄漏。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
