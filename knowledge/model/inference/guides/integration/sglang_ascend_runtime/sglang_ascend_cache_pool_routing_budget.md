---
type: Guide
title: SGLang Ascend KV池选择、Indexer省层与DCP预算一致性
description: 说明NPU原生MHA/MLA/SWA/MiniMax池选择、Indexer实际层与预算同步、PD/HiCache省层守卫和target/draft
  DCP原始预算与builder入参容量。
tags:
- task.implementation
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/pool_configurator.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/kv_cache_configurator.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/configs/model_config.py
  role: implementation
created_at: '2026-11-08T12:21:43Z'
updated_at: '2026-11-09T04:34:03Z'
platforms: []
---

# SGLang Ascend KV池选择、Indexer省层与DCP预算一致性

## 选择与几何

KVCacheConfigurator在compressed V4专用路径后，对attention_backend=ascend且非mambaish配置，按hybrid SWA、MiniMax sparse、MLA、普通MHA选择原生NPU池。Mamba混合模型走另一组装路径，不能用单个ascend字符串反推一定NPUMLA。MHA/SWA的KV head数按attention TP/DCP划分；MiniMax index_dtype为model_dtype，和主KV dtype分别记录。

NPUMLA 从同一原始每rank token预算出发，target与draft的Indexer都覆盖预算×DCP。target在builder中以原始 max_total_num_tokens 乘DCP；NPU NextN draft执行宽度为1，_derive_pool_sizes 先按 draft_loc_space_scale=DCP 扩大容量，再传给builder，所以draft分支只是不再额外乘DCP，不能用原始预算直接分配。target的Indexer用allocator-global slot，target主KV再localize，draft/Indexer保留全局身份。分配器同时把size与page_size各乘DCP；只放大一轴会令页编号和局部块表错配。packed DSA FP8宽度只在kv_dtype为E4M3且arch35时计算，不将GPU FP8布局当通用NPU布局。

## 省层预算与分配必须同门控

共享topk层不访问自己的Indexer时可只为真实owner层分配；_should_elide_dsa_index_k在NPU PD模式非null或enable_hierarchical_cache时返回False，因为PD列表按位置切片、HiCache该层合同不支持这里的compact省略。HiSparse、draft、external linker也禁止该一般省层条件。

pool_configurator的cell bytes使用同gate计数，普通NPU非FP8按index_head_dim×KV dtype itemsize；可省层时统计不跳topk的实际层。layer shard按各rank最大owner数+1预留，不能只拿平均层数。实际池indexer_layer_ids与预算计数必须相同；否则浪费预算或分配超出规划。原生Host池可以镜像设备实际index layer子集，不等于所有HiCache入口已经允许开启本省层优化。

最终可用字节减fixed overhead，再除cell bytes并向下page对齐；零cell使用专用token上限，不能除零。通用MTP共享KV sharding入口显式拒NPU，不能把普通MTP可运行和共享shard功能混同。

验收用同份模型层映射、dtype、PD/HiCache/draft/DCP条件同时检查预算与实际Tensor字节，含Indexer scale及Host额外池；保留初始化后空闲量与真实分配，不以估算公式代替OOM/精度测试。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
