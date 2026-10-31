---
type: Optimization
title: Decode 多流控核平衡：LongCat 双重路径拖尾的优化规则
description: 当前 LongCat Decode 的 GE/npugraph_ex 多流、两套核数、事件汇合与 AFD 边界；修正旧单数开关及版本拼接。
tags:
- task.optimization
- topic.attention
- topic.mixture_of_experts
- topic.graph_execution
- topic.implementation.synchronization
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T13:44:43Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      objective:
      - latency
      - tpot
      model_features:
        all_of:
        - moe
      execution_mode:
      - ge_graph
---

# Decode 多流控核平衡

## 适用与信号

在 LongCat-Flash A3 Decode 的 Attention/Dense 主路径与 shortcut MoE 可以重叠、但时间线出现单路拖尾时，按工作量和带宽调整两路核数。当前支持 ge_graph 与 npugraph_ex 多流，eager 配置直接拒绝；该实现不证明其他模型可继承相同配比。

## 当前配置与调度

配置位于 model_config.custom_params.enable_multi_streams：0关闭，1采用 MoE c8v16、主路c16v32，2采用两路均c12v24。源码在非 Prefill 且值>0时进入 multi_stream_forward；核数是固定候选，不能视为实测最优。

GE 分支用 npu_stream_switch_gegraph 的流1；npugraph_ex 使用独立 torch.npu.Stream，切流前 record_stream/record_event，MoE 等待输入事件、完成后记录事件，主流在相加前 wait_event。limit_core_num 按 exe_mode 选择对应后端的控核实现。

AFD 仍可进入多流前向，但不运行本地 shortcut MoE，且通过 limit_core_num(not enable_afd, ...) 取消同卡控核；不能把非 AFD 的核数配置直接套到远端 FFN。SuperKernel 仅 ge_graph 支持；预取依赖多流开关。

## 验证与回退

固定权重、并行、路由、MTP、batch/序列和后端，仅改变合法的分核选项；同时检查两路时间线、汇合等待、输出与 TPOT。overlap 增加不代表端到端变快。来源没有独立控核消融，本次未运行硬件。

回退 enable_multi_streams=0 时也要关闭 enable_prefetch，否则当前模型校验报错。保存并匹配图缓存，勿用切 eager 代替单项消融。

## 相关入口

- [权重预取](decode_weight_prefetch_ordering.md)
- [AFD](afd_attn_ffn_disaggregation.md)
- [跨流同步](graph_mode_multi_stream_cross_stream_sync_api.md)


## Evidence

- [longcat_flash_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md)（primary）
- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（implementation）
