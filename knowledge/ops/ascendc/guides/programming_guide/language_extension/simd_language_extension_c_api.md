---
type: Guide
title: SIMD语言扩展层C API
description: C API开放芯片完备编程能力，支持以数组形式分配内存，一般基于指针编程。提供与业界一致的C语言编程体验。
tags: [task.lookup, topic.programming_model.language_extension]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/language_extension/simd_language_extension_c_api.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# SIMD语言扩展层C API

C API开放芯片完备编程能力，支持以数组形式分配内存，一般基于指针编程。提供与业界一致的C语言编程体验。
包含asc_simd.h文件来调用C API相应接口。如无特殊说明，包含该头文件即可满足接口调用需求。若API文档中有特殊说明，则应遵循API的具体说明。
对于C API，主要分为以下几类：
-   矢量计算，实现调用Vector计算单元执行计算的功能。
-   数据搬运，计算API基于Local Memory数据进行计算，所以数据需要先从Global Memory搬运至Local Memory，再使用计算API完成计算，最后从Local Memory搬出至Global Memory。执行搬运过程的接口称之为数据搬运API。
-   同步控制，完成任务间的通信和同步，比如asc_sync_notify/asc_sync_wait接口。不同的API指令间有可能存在依赖关系，从抽象硬件架构可知，不同的指令异步并行执行，为了保证不同指令队列间的指令按照正确的逻辑关系执行，需要向不同的组件发送同步指令。同步控制API内部即完成这个发送同步指令的过程。
-   系统变量，访问、获取系统内置变量，辅助计算API。
对于计算类API可以分为以下几类：
-   前n个数据计算：该类型API在计算时采用“紧密排布”的数据读取方式，即从起始位置开始，按顺序连续获取所需数据。例如，若需处理N个数据，则从源操作数的第0个位置开始，依次取至第N-1个位置。
-   高维切分计算：该类型API按照设定的规则“跳过部分数据”。适合处理需要间隔采样的场景，灵活度高，但需要额外配置相关参数。
-   同步计算：该类型API内部自动插入同步操作，易用性更强。

<!-- cannbot:related:start -->
## 相关

- [ASC_VDEQ_SIZE 未声明 — 勿直引 vector_compute.h](../../../runbooks/compilation/asc_simd_umbrella_header_for_c_api_symbols.md)（`related`）：包含asc_simd.h文件来调用C API相应接口。如无特殊说明，包含该头文件即可满足接口调用需求。；保留调用点与数据流不变，只把叶子声明头替换为 public C-API umbrella。；指南给出公共入口头，排障卡证明叶子声明头缺少 umbrella 前置定义并给出不改调用点的替换方式，形成 C API 头文件选择到编译修复的直接链路。
- [C-API asc_simd.h 编译缺 include 根](../../../runbooks/compilation/c_api_asc_simd_h_include.md)（`related`）：包含asc_simd.h文件来调用C API相应接口。如无特殊说明，包含该头文件即可满足接口调用需求。；include 根是 `asc/`（覆盖并列的 `include/` 与 `impl/`），**不是** `asc/include`、也**不是** `asc/impl`。；指南确定用户要包含 asc_simd.h，排障卡进一步规定 CMake 必须让该公共头及其 impl 依赖同时可解析，补齐 950 工程从 include 指令到 include 根的配置。
<!-- cannbot:related:end -->
