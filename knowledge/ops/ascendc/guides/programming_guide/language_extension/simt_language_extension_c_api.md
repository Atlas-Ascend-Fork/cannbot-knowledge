---
type: Guide
title: SIMT语言扩展层C API
description: SIMT编程基于AI Core的硬件能力实现，当前，SIMT语言扩展层支持的C API类别如下：
tags: [task.lookup, topic.programming_model.language_extension]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/language_extension/simt_language_extension_c_api.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# SIMT语言扩展层C API

SIMT编程基于AI Core的硬件能力实现，当前，SIMT语言扩展层支持的C API类别如下：

-   同步与内存栅栏：提供同步与内存栅栏接口，解决线程间可能存在的数据竞争以及线程的同步问题。
-   原子操作：提供对Unified Buffer或Global Memory上的数据与指定数据执行原子操作的一系列API接口。
-   Warp函数：提供对单个Warp内32个线程数据进行处理的一系列API接口。
-   数学函数：提供处理数学运算的函数接口集合。
-   访存函数：提供开启Cache Hints的Load/Store函数。
-   地址空间谓词函数：提供判断输入指针所属地址空间的函数接口集合。
-   地址空间转换函数：提供不同地址空间地址值与指针之间相互转换的函数接口集合。
-   协作组：提供更细粒度的线程间协作的API接口。
-   调测接口：SIMT调试场景下使用的相关接口。
