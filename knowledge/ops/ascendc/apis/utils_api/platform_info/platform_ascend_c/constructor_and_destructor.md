---
type: API
title: 构造及析构函数（PlatformAscendC）
description: 在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/constructor_and_destructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 构造及析构函数

## 功能说明
在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。
## 函数原型
## 参数说明
## 返回值说明
无
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [561002：TilingParse 未生效，CompileInfo 为空](../../../../runbooks/compilation/561002_tilingparse_compileinfo.md)（`exemplifies`）：诊断后的处置方向：GetShapeInfo 不再硬依赖 CompileInfo，null 时回退到 `ctx_->GetPlatformInfo()` + `PlatformAscendC` 直读 `coreNum`/`ubSize`；UT 直接编译 tiling.cpp 时需为 PlatformAscendC 追加 `platform` 链接库。；在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。。Runbook 给出 CompileInfo 为空时改由 PlatformAscendC 读取 coreNum/ubSize 的修复，API 卡定义该类的硬件信息能力。
<!-- cannbot:related:end -->
