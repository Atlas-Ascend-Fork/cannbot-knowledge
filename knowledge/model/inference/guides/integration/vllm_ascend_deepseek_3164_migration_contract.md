---
type: Guide
title: vLLM Ascend DeepSeek V4/V4.1 版本迁移：TP sinks、DP replay 与 Engram
description: 记录3164对DeepSeek V4/V4.1移除legacy DSA-CP模型分支、修正DP/PCP decoder replay、Engram异构block32旋转及视觉dummy最大特征预算，供升级适配与性能回归定位。
aliases:
- DeepSeek V4 V4.1 3164 migration
- DecoderReplayPlan DP PCP compaction
- Engram block-diagonal rotation table
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/deepseek_v4/model.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/deepseek_v4/dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/deepseek_v4/indexer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/deepseek_v4/mm_preprocess.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/deepseek_v4/mtp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/deepseek_v41/decoder_replay_layers.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/deepseek_v41/decoder_replay_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/deepseek_v41/dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/deepseek_v41/engram/common.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/deepseek_v41/indexer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/deepseek_v41/model.py
  role: implementation
created_at: '2026-11-03T06:35:09Z'
updated_at: '2026-11-04T03:07:25Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend DeepSeek V4/V4.1 版本迁移：TP sinks、DP replay 与 Engram

本卡固定3164；7d9e的V4.1 cut层KV预写、首SWA builder和运行时replay对象接入另见[7d9e运行时迁移](vllm_ascend_7d9e_runtime_delta_contract.md)，不能把旧cut+1起点直接搬到新版本。

固定差异 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd` 的完整 unified diff 与必要上下文已读，未将目标整文件标为FULL；既有ceac卡继续作为旧版本证据。本次没有上游导入、真实模型、NPU、图、多卡或性能运行。

## TP sinks 与旧 DSA-CP 分支退役

V4/V4.1模型不再用enable_dsa_cp选择全head sinks或Replicated wq_b，改为TP-local sinks及ColumnParallelLinear；need_gather_q_kv构造参数被移除。SP MoE的attention前AG/后RS不再因旧DSA-CP例外跳过。DSpark与MTP的sink加载同样裁到head_start/head_end，不能将ceac配置flag硬套到新模型类。

V4 target/MTP/DSpark仍通过weight_loader写sink，以配合Native layerwise meta reload；V4.1此次只是改为narrow，相关loader仍有直接copy_，不能据同族名称宣称它也得到相同的reload生命周期保证。indexer ratio4 backend名称从DSAC4迁为DSAIndexer，ratio128另一路保留；实际派发还需与对应attention变更成对检查。

## Decoder replay：协调执行长度而非只裁本地行

V4.1 replay删除PCP>1且DP>1的旧直接禁用分支，但SP、PP、DCP与microbatch仍拒绝；prefill需NONE或FULL_DECODE_ONLY，Engram位置、DSpark草稿和窗口条件继续约束。移除单个gate不代表所有组合完成实机验收。

每step prepare先清rows/context_factory/padded_rows、replay PCP、DP tokens与metadata，初始化在capture/profile早退前完成，避免旧step状态泄漏。DP>1时若配置跳过DP allreduce或协调则直接不compact。计划分别保存kept_lens、execution num_tokens、requires_compaction与uses_pcp_replay；dummy实际token强制0，但保持原collective padding。

PCP按global tail保留owner，空rank仍requires_compaction；没有有效PCP replay plan时不按每rank本地尾独立裁剪。普通非compact保留 `num_tokens_after_padding`，不能用实际sum缩窄idle rank通信。DP CPU group allreduce共享两行数据：各replica的compact flag与补齐执行长度，只要一方裁剪，所有replica使用新的cross-DP counts。

本rank不compact但peer compact时rows保持None、复用原attention metadata与PCP layout，仅进入新forward context。compact rank则重建query offsets、dropped前缀、row/position/slot/replay start与metadata，PCP同步重建global restore映射；旧TP分区buffer gather分支被移除。不能因rows=None就跳过context_factory。

forward_context为新执行长度显式准备is_padding：selected真实行从外层gather，其余True；没有外层mask时按actual前缀False。MC2 mask同时与完整padding取交集，保留未裁剪批次已有masked行，finally恢复旧mask。slot_mapping在compact时None、非compact保留outer；metadata也按是否compact选择。不能只检查shape忽略跨DP长度、padding与EPLB热度标志。

## Engram 旋转与视觉预算

Engram加载现在校验global_rotation严格[hidden,hidden]且hidden可32整除，再验证block-diagonal。对角32块可以不同：全部相同时返回单块，否则返回block table；gate分别执行二维共享块或三维逐块FP32逆旋转。旧“必须重复同一block32”仅适用ceac。模型将真实返回的二维/三维rotation移到device后注册nonpersistent buffer，不再把任意table强copy到eye32。

V4视觉dummy不再假设正方形最大特征。每aligner行多IMAGE_NEW_LINE成本，预算扣除COMPRESS_PAD_TO-1后搜索LLM网格，满足max_wh_ratio，优先patch面积再token长度。profiling/显存规划若仍用旧square，可能低估最坏视觉输入。真实resize/token/权重协议继续按[视觉接入](vllm_ascend_deepseek_v4_vision_input_contract.md)固定版本核对。

V4.1 indexer在构造时注册topk/compress_ratio与query quant两个JIT warmup需求，依赖model runner打开registry窗口；不再以独立warmup脚本文件存在作为已预热证据。

## Agent 升级验收

先锁定旧/新提交、配置字段退役、TP head分片、SP归约次数与sink实际loader；再覆盖DP一方裁剪/一方idle、PCP零真实行、dummy、首步capture/profile、跨step清理、mask恢复、异构旋转、非方形最大视觉输入。索引/布局/保留行精确比较，Engram和模型输出按实际dtype参考；最后测真实communication、compile/TTFT和端到端性能。知识检索与静态diff不替代这些运行结果。
