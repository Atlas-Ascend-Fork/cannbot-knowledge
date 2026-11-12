---
type: Guide
title: SGLang Ascend V4分配器：C128独立页与引用计数回收
description: 闭合full/SWA/C4派生地址与C128独立paged allocator的容量预检、prefix共享、投机预留和请求释放。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_allocator.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_req_to_token_pool.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/c128_sidecar_component.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_memory_pool.py
  role: implementation
created_at: '2026-11-08T12:07:56Z'
updated_at: '2026-11-09T04:31:35Z'
platforms: []
aliases:
- DSV4NPUTokenToKVPoolAllocator
- retain_c128_pages
---

# SGLang Ascend V4分配器：C128独立页与引用计数回收

## 地址族

DSV4 allocator先复用full/SWA分配，再为C128独立分配。C4只为full slot满足slot%4==3的组末生成slot//4；C128新增压缩token数是floor(seq/128)-floor(prefix/128)，最后位置由request sidecar确定。返回DSV4OutCacheLoc只包含各KV槽族，不包含固定ring compressor state。

## 分配与容量

extend在改变full/SWA分配前先精确计算C128需要的新页：ceil(floor(seq/128)/c128_page)-ceil(floor(prefix/128)/c128_page)。不足时可通过FULL叶子驱逐回收配套C128，避免单独挖掉共享prefix内部页形成孔洞。禁用prefix sharing后不能靠此回收；预检不足返回None，不能先分full再静默留下半完成状态。

decode依据page-aligned reserve长度预留投机窗口。普通单token C4位置压紧使用设备算子避免NonZero主机同步；多slot投机场景仍可能走bool indexing，不能声称所有分配路径无同步。available_size换算为原始token数，是full/SWA容量与C128可用容量×128的下界。

## 引用与释放

C128物理page由request和radix前缀分别retain，retain不自动去重；release每次调用先取唯一正page号，再对每页各减1引用，只有refcount恰降至0才还给free pool；一次release不能抵消同一页在retain输入中重复出现造成的多次增加。替换prefix只对差异页释放/retain，不能重复retain已有页。

free(full_indices)没有request身份，只释放full/SWA；完整free(req,pool)还须释放sidecar全部C128页、清sidecar并清请求作用域state，再复用request slot。漏掉后者可表现为跨请求污染或C128内存泄漏。clear重置各allocator与refcounts。

建议对部分尾页、共享完整prefix、分支插入、撤销投机、多次驱逐和request slot复用检查页引用总量及最终free容量；仅计full token释放量不足以验收。独立C128页可节省压缩存储但引入sidecar、引用计数和容量耦合；本次未执行压力/真机测试，平台范围待确认。
