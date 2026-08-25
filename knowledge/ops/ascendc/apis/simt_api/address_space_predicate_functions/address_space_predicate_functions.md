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

<!-- cannbot:related:start -->
## 相关

- [__isUbuf](_is_ubuf.md)（`same_topic`）：《__isUbuf》处理“判断输入的指针是否指向Unified Buffer内存空间的地址。”。《地址空间谓词函数》明确“SIMT API地址空间谓词函数汇总，提供判断指针是否指向Global、UBuf、Local地址空间的断言能力。”，可直接用于核对SIMT UB 地址空间谓词、generic/ubuf 转换和指针形参限定合同。
- [地址空间转换函数](../address_space_conversion_functions/address_space_conversion_functions.md)（`same_topic`）：《地址空间转换函数》处理“SIMT API地址空间转换函数汇总，提供generic与Global、UBuf、Local间指针与地址值的双向转换能力。”。《地址空间谓词函数》提供“SIMT API地址空间谓词函数汇总，提供判断指针是否指向Global、UBuf、Local地址空间的断言能力。”，其具体合同或探针直接接入SIMT 地址空间转换与谓词验证、helper 形参地址限定合同。
<!-- cannbot:related:end -->
