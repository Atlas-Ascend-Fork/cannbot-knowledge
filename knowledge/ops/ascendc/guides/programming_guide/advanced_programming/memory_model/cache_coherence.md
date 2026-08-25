---
type: Guide
title: 缓存一致性
description: 本文介绍NPU编程中常见的缓存一致性问题，说明DCache、ICache、SIMT DCache与GM的数据一致性。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/memory_model/cache_coherence.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 缓存一致性

本文介绍NPU编程中常见的缓存一致性问题，说明DCache、ICache、SIMT DCache与GM的数据一致性。
## 缓存一致性的基本概念
### Cache、Cache Line与缓存副本
Cache用于缓存后续可能重复访问的数据或指令，降低访问GM的开销。一次Cache加载通常不是只加载被访问的单个字节或单个变量，而是把该地址所在的一段连续数据作为一个整体加载到Cache中，这个整体称为Cache Line。
Cache Line是Cache加载、失效、写回的最小操作粒度。例如访问GM内存时，会将GM里一个Cache Line长度内相邻的数据加载到L2 Cache缓存，利用空间局部性提高访问效率。Cache Line是硬件真正搬入、标记、替换和写回缓存数据的最小粒度，直接影响性能和一致性。NPU架构版本2201支持L2 Cache、DCache和ICache。
