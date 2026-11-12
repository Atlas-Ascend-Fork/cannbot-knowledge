---
type: Guide
title: SGLang Ascend DeepSeek-V4：SWA、C4、C128与压缩状态路由
description: 说明V4原始滑窗与两种压缩attention、NPU compressor/indexer、CP元数据切换及graph重放状态刷新，保留A3与950差异。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
- topic.graph_execution
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_dsv4_backend.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_memory_pool.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_rope.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_common_hooks.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/dsv4/compressor.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/dsv4/indexer.py
  role: implementation
created_at: '2026-11-08T12:07:56Z'
updated_at: '2026-11-09T04:32:54Z'
platforms: []
aliases:
- DeepseekV4AscendAttnBackend
- V4 HCA CSA SWA
---

# SGLang Ascend DeepSeek-V4：SWA、C4、C128与压缩状态路由

## 三种attention及硬件分支

V4每层只允许compress_ratio=0/4/128：0读取原始SWA，C4将压缩TopK作为[T,1,K]稀疏索引，C128读取完整压缩历史；二者都保留原始滑窗和sink。缺压缩缓存、元数据或C4物理页比例不匹配会报错，不会返回零掩盖问题。draft模型不建立C4/C128压缩层，只用SWA。

源码明确区分pre-950与Ascend950：主模型950用custom quant shared-KV attention/metadata，较早架构用非量化custom接口；DSpark draft分别使用公开quant host pair或torch.ops.npu host pair。950参数为kvquantmode1、tile64、rope64。接口存在不等于已证明每种模型/芯片组合可运行，平台保持未知。

## Compressor和indexer

融合compressor使用预排wkv/wgate、FP32 norm、预热的interleaved RoPE表，cache_mode=2。A3 explicit state table为二维逐状态地址，负无效位置先安全clamp索引再替换为已清零的正dummy；950 cycle table必须是一维int32 request bank，不能传A3二维表。增量prefill只写本chunk新完成的压缩组。loc 存在时，非 target-verify 的 prefill 若 cmp_kv 行数大于 loc 数量，会先裁剪到 loc 长度，允许此类合法 padding；其他 loc/输出行数不匹配才报错。

C4 indexer的K在pre-950为INT8+FP16scale，950为FP8+FP32scale；Q按K dtype选择动态量化。先RoPE再归一化Hadamard，weights_proj乘相应softmax/head尺度；侧流必须等待q_lora ready，主流等待Q和weights，compressor cache写先于TopK读取。native quant LI输出写入forward_metadata供同层压缩attention使用；BF16逐请求einsum是较慢参考回退。

## CP、投机与图刷新

CP先保存full元数据，再按策略本地Q位置选择逐token页表；有效KV长度=全局position+1，padding使用合法request0表和至少1长度。compressor需要全量token顺序时临时切回full字段，context manager在finally恢复本地字段及positions，避免后层误用全局元数据。

DSpark draft块为非因果块：每query可见尾部SWA加整个draft block，索引宽度128对齐；不能套用target的逐token因果规则。target verify中Eagle使用live长度加固定宽，DSpark/DFlash另带已扩张长度和live镜像，不能重复加宽。压缩RoPE位置普通verify选择组末完成token后移到组首；ragged路线按变长行偏移单独生成。

图预分配页表、1024 int32 kernel metadata、TopK和位置/loc缓冲。replay刷新live/final长度、C4/C128页表、SWA loc、压缩位置、explicit/cycle state、DSpark稀疏索引和kernel metadata；表缩窄按高水位清旧列，缺bundle清旧loc。stable compaction用cumsum+scatter_add避免动态NonZero。Eagle固定verify位置可全device生成；ragged和某些host metadata仍有CPU镜像/回读，不能称全路线无D2H。

## 检查步骤与边界

依次核对ratio、kernel page size、state寻址模式、组完成边界、请求/层局部索引和live/final长度。使用跨4/128边界、chunked prefill、prefix命中、宽→窄图bucket、空DP rank与多步draft比对eager/graph输出及缓存内容；本次没有运行这些案例。多步V4 draft为每步切换full/SWA写窗口，finally恢复原bundle，C4/C128输出置空，不能共享一整块写地址重复写各步。
