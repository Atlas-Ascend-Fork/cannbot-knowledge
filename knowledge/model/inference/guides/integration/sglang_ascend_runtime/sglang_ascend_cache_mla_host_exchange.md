---
type: Guide
title: SGLang MLA HiCache的AscendC分层流水与分量元数据
description: 说明MLA split Host镜像、packed FP8和Indexer层子集、MemFabric AIV地址重写、逐层H2D、target全层D2H及旧传输分支的MTP不兼容跳过。
tags:
- task.implementation
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/pool_host/mla.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/pool_host/npu_memfabric.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/managers/cache_controller.py
  role: supporting
created_at: '2026-11-08T12:04:51Z'
updated_at: '2026-11-09T04:34:03Z'
platforms: []
---

# SGLang MLA HiCache的AscendC分层流水与分量元数据

## Host镜像与选择

kernel_ascend要求page_first_kv_split，Host基础形状[page,layer,page_size,1,width]。K宽普通为kv_lora_rank，packed DSA FP8则使用native.k_width；RoPE/V独立分配但packed空V不参与搬运。Indexer只分配实际物理Indexer层数，可少于模型层数；FP32 scale镜像形状末维1，不得用主KV dtype估算其字节。

MemFabric Host开关同时选择mapped allocator和AscendC IO，预留预算汇总K、RoPE/V、实际Indexer层及4字节scale。普通pin memory不是AIV可直接解引用的mapped Host地址。

## 两种传输调度

旧transfer_kv_dim_exchange一次传所有层，仅device_layer_id==0触发，按native/Host切片组循环。AscendC稀疏copy则H2D每次限制一个层及其Indexer槽位，调用者逐层complete事件允许后续DMA与当前层计算重叠；D2H默认一次传target全层，不能据此推断包含全部draft状态。两种分支不能同时当成“均逐层流水”。

AscendC直接读取设备token索引，CPU索引用pinned staging异步上传并record_stream以延长生命周期，避免索引往返CPU。元数据8个header整数，每分量9整数：设备/Host基址、两侧层/页pitch、行字节和层区间；最多4分量。Host base逐个get_dva，返回0失败，转换后上传int64元数据；kv_exchange_copy非零抛异常。这里的宽度/pitch均按itemsize换算字节，不能把元素stride直接传成字节。

## 并行与草稿限制

索引先经过maybe_dcp_kernel_indices，dummy非源MLA Host池禁止load/backup；layer-shard进入独立逐层备份，但该函数只接受kernel/direct，kernel_ascend明确抛ValueError；不能把layer-shard与此Ascend IO组合写成可用。AscendC元数据要求Host与Device层编号空间兼容并检查区间。只有旧 `_npu_transfer_pool_slices` 路径会对 MTP draft 的 K/V 宽度或 dtype 不匹配告警并跳过，并对未分配Host镜像的draft Indexer告警不备份。AscendC H2D 则按 is_draft 直接选择对应 draft native 缓冲逐层提交，不经过这些告警/兼容检查；AscendC D2H 仅提交 target native 后返回。不能据target成功恢复声称所有草稿状态也已保存。

验证必须覆盖Indexer稀疏层映射、packed/非packed、scale、DCP与MTP、不兼容跳过日志、事件消费和跨流索引生命周期；比较相同请求的恢复精度及端到端TTFT/TPOT。源码的无同步设计意图不是本次实测收益。

## controller的索引设备选择

CacheController在kernel_ascend且AscendC IO开启时用pinned staging把Host索引异步上传，并保留设备索引；旧memcpy2d分支device_indices.cpu()会发生Host回读。这条入口差异决定是否能保留分层流水，不能只切Host池底层实现而沿用旧索引准备。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
