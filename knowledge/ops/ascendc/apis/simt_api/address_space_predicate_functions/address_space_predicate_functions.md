---
type: API
title: 地址空间谓词函数
description: SIMT API地址空间谓词函数汇总，提供判断指针是否指向Global、UBuf、Local地址空间的断言能力。
tags: [task.lookup, topic.implementation.masking]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/address_space_predicate_functions/address_space_predicate_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# 地址空间谓词函数

SIMT API地址空间谓词函数集合，用于判断指针所指向的地址空间类型。包含__isGlobal（判断指针是否指向Global Memory地址空间，GM为设备端全局内存）、__isUbuf（判断指针是否指向Unified Buffer地址空间，UB为片上高速缓存）、__isLocal（判断指针是否指向Local地址空间）。这些谓词函数在编译期或运行期对指针的地址空间属性进行判断，支撑泛型编程、地址空间校验和安全检查。
