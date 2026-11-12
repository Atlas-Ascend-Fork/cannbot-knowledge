---
type: Guide
title: SGLang Ascend V4请求表：C128 sidecar与请求槽复用
description: 说明C128独立页表宽度、prefix命中早于request分配时的暂存协议，以及normal/PD decode释放顺序。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_req_to_token_pool.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_allocator.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/c128_sidecar_component.py
  role: implementation
created_at: '2026-11-08T12:07:57Z'
updated_at: '2026-11-08T12:07:57Z'
platforms: []
aliases:
- DSV4NPUReqToTokenPool
- req_to_c128_sidecar
---

# SGLang Ascend V4请求表：C128 sidecar与请求槽复用

## 为什么需要sidecar

C4可由full token地址派生，C128物理页由独立allocator分配，不能从full页号推算。因此DSV4 NPU request pool维护int32 `req_to_c128_sidecar`，每项为一个C128物理page id，宽度为ceil(context_len/(128*c128_page_size))，初始为0。

`write_c128`以压缩token位置更新刚跨越的page组；allocator的replace-prefix协议维护页引用数。普通full req_to_token和SWA映射继续承担原来的索引空间，sidecar不替代它们。

## Prefix与请求生命周期

prefix匹配可能发生在request slot分配之前。此时先把页号暂存在req.c128_prefix_page_ids；alloc成功后将新sidecar行清零，再安装prefix页并清暂存字段。若直接写未分配的行，会覆盖另一个请求或复用旧sidecar。

allocator在构造完成后注册反向引用。normal和PD decode request pool在释放请求槽之前先通知allocator，释放独立页与请求状态；PD预分配也遵守这一顺序。复用request slot必须观察到sidecar清空和state重置，而不是只看到full表重新写入。

## 验收方法

检查完整prefix/部分尾页各自归属、先命中后alloc、无命中分配、finish/abort和PD预分配失败后的页计数。确认C128 compressed position到page/offset的换算与c128_page_size一致。附加sidecar增加每请求表空间，换取独立C128页共享和回收；本次未跑生命周期测试，也未证明所有芯片可用。
