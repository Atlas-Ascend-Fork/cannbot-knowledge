---
type: API
title: 内存空间限定符
description: 在SIMD与SIMT混合编程中使用内存空间限定符__gm__来表示分配于设备侧全局内存的对象，全局内存对象可以声明为标量、用户自定义结构体的指针。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/extended_syntax/memory_space_qualifier.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 内存空间限定符

SIMD 与 SIMT 混合编程使用两种内存空间限定符。

__gm__：表示设备侧全局内存（Global Memory）对象，可声明为标量或用户自定义结构体的指针。

__ubuf__：表示 Unified Buffer 中的动、静态内存。静态内存大小在编译期确定，通过数组分配（如 __ubuf__ half staticBuf[1024]）；动态内存大小在核函数启动时配置，通过 extern 数组声明（如 extern __ubuf__ half dynamicBuf[]）。

<!-- cannbot:related:start -->
## 相关

- [纯 SIMT kernel 形参 __gm__ 导致编译失败](../../../../runbooks/compilation/pure_simt_parameters_do_not_use_gm_qualifier.md)（`exemplifies`）：SIMD 与 SIMT 混合编程使用两种内存空间限定符；保留纯 SIMT 的 `__global__` kernel 与寻址算法，只从函数形参移除 `__gm__`，让 普通 `const T *` / `T *` 承载 GM 地址。API 卡把 `__gm__` 定位于混合编程语法，运行手册给出纯 SIMT 编译前端中的相反形参写法和真实报错，形成编程模式切换时的具体边界。
<!-- cannbot:related:end -->
