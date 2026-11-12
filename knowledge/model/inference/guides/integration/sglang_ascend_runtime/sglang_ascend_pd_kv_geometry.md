---
type: Guide
title: SGLang Ascend PD的PP分层与DCP页交错传输合同
description: 解释AscendKVManager的2MiB批注册、C4/C128与draft导出顺序、DCP1到N本地/全局页映射和不支持的目标索引路径。
tags:
- task.implementation
- topic.kv_cache
- topic.parallelism
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/disaggregation/ascend/conn.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/disaggregation/ascend/transfer_engine.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/disaggregation/prefill.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/disaggregation/base/conn.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/disaggregation/common/conn.py
  role: supporting
created_at: '2026-11-08T11:53:43Z'
updated_at: '2026-11-08T11:53:43Z'
platforms: []
aliases:
- AscendKVManager
- _build_page_interleaved_dcp_plan
---

# SGLang Ascend PD的PP分层与DCP页交错传输合同

## 注册与分组

AscendKVManager继承通用Mooncake KV控制流程，但使用AscendTransferEngine。把KV、aux及所有state缓冲合为一次batch注册，以便MemFabric在2MiB对齐后合并小Tensor重叠范围；这不是逐Tensor原始地址已2MiB对齐的声明。注册失败口径仍须看实际engine，不能仅因函数无异常认定成功。

NPU额外状态类型为DSV4_C128和DSV4_C4_STATE，后者在950 CYCLE模式按每请求bank存Attention/Indexer压缩状态，与SWA分开；配对要求exact state indices，不能套GPU bundled SWA+C4状态顺序。

## PP及draft切片

V4压缩比列表分别统计C4和C128的全局/当前PP层范围：C128只切相应组；C4 state对Attention与Indexer两组分别切；主KV可能按[C4 KV,index K,index scale]三组切；950独立SWA按层切。普通MLA按kv_buf_groups切目标层，draft只由最后PP rank附加传输。Hybrid MLA prefill的PP局部条目与Decode全层条目按global layer id配对，不能只按列表下标zip。

send_kvcache明确拒绝dst_device_kv_indices（HiSparse目标device索引），这一限制不等于所有DCP或Host cache均被禁用。普通页序列先按双方连续索引分组，地址为base+page_index*item_len，长度为连续页数*item_len；自定义池逐层future传输，任一失败取消尚未完成future并返回失败，不保证已提交的所有传输被回滚。非自定义池合批所有层减少线程开销。

## Page-interleaved DCP

仅对该布局支持Prefill DCP=1到Decode DCP=N；其他不匹配组合报错。Decode prefix须对page_size*N整除。relative_page=src_page_offset+arange，owner=(decode_prefix/page_size+relative_page)%N；本地KV仅发送owner等于当前Decode rank的页，而global-slot条目把目标super-page展开为super_page*N+owner。源subset offset不能丢失，否则CP分片会写错目标页。

逐entry验证源page_bytes=token_item_len*page_size，global目标条目要求page_bytes*N、本地要求page_bytes；draft远端总按global slots，DSA indexer布局独立。whole-page直接传输不使用通用DCP pack buffer；dst layer/item metadata不一致应在发起拷贝前失败。

## 验证和回退

先验两端layer IDs、state类型、压缩比、page/item字节、target/draft边界与DCP所有权，再做单页/跨连续组与多PP阶段数据比对；覆盖prefix非零、CP subset和不合法拓扑的拒绝路径。不要只检查请求链路或传输状态码。回退到对齐的P/D并行配置/旧匹配拓扑时仍需重建缓存与会话，不能只改DCP数继续用原buffer。

## 上层注册顺序

Prefill从storage取KV pointer/length/item_len后，NPU只在允许transfer_draft_cache且最后PP stage附draft KV；Ascend将target与实际draft池的get_dcp_remote_decode_layout结果按注册顺序拼接，并随manager构造传入。层分片时draft还有最后layer-shard守卫。descriptor和pointer列表必须同行同序，不能单独改网络层来补缺项。CommonKVManager继承的terminal状态消息默认为room/status/prefill_rank三个未加tag的frame，控制面成功与KV数据验收分开。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
