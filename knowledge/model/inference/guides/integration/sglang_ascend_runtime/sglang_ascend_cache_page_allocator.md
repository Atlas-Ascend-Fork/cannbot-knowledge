---
type: Guide
title: SGLang NPU分页分配器的续写、Decode与回收合同
description: 说明NPUPagedTokenToKVPoolAllocator的小于200页Kernel分支、尾页复用、Decode新页计算、int32返回和Host去重回收。
tags:
- task.implementation
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/allocator_npu.py
  role: primary
created_at: '2026-11-08T11:53:40Z'
updated_at: '2026-11-08T11:53:40Z'
platforms: []
aliases:
- NPUPagedTokenToKVPoolAllocator
---

# SGLang NPU分页分配器的续写、Decode与回收合同

alloc_extend计算新增页数为sum(ceil(seq/page)-ceil(prefix/page))，可接受调用方预先给的num_new_pages来避免该处.item()读回。空闲页不足先merge_and_sort_free，仍不足返回None；不是无条件扩容。debug检查last_loc与prefix尾页一致，不能以非debug路径无检查推断非法输入也受支持。

新增页数<200时走sgl_kernel_npu.mem_cache.allocator.alloc_extend_kernel，输出临时int64，grid按batch；否则走alloc_extend_naive，临时int32。两条最终均返回.int()的int32索引，消费空闲页前缀。该旧内部Kernel导入不是上一轮公共operators.mem_cache.alloc_extend的相同签名。

Decode先用CPU长度算新增页需求；seq_len%page_size==1的请求拿新页，其余用last_loc+1。没有新增页时全部线性续写；有新增页时cumsum分派free_pages，防止非需新页行的索引越界。两个路径均保留页0/占位约定并依赖父分配器的free page结构。

free为空直接返回；非分组释放把索引移到CPU，以token_idx//page_size取unique页，再移回原设备释放，因此存在Host读回成本，不能称为纯设备无同步回收。free_group模式只追加拷贝，实际批量释放由父类完成。

验证续写跨页、整页边界、199/200页分发、空闲页不足、重复token同页回收与分组回收；检查未重复分配、没有误还活页、输出dtype和请求尾页一致。优化页数计算或回收前必须保持这些语义，不能只比较分配成功布尔值。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
