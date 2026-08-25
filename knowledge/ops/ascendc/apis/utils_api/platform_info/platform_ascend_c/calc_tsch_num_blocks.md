---
type: API
title: CalcTschNumBlocks
description: 针对Cube与Vector分离模式，计算融合算子启动的numBlocks值，即AIV与AIC组合数量，结果通过SetSimdNumBlocks设置。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/CalcTschNumBlocks.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# CalcTschNumBlocks

## 功能说明
针对Cube、Vector分离模式，用于计算Cube、Vector融合算子的numBlocks。针对Vector/Cube融合计算的算子，启动时，按照AIV和AIC组合启动，numBlocks用于设置启动多少个组合执行，比如某款AI处理器上有40个Vector核+20个Cube核，一个组合是2个Vector和1个Cube核，建议设置为20，此时会启动20个组合，即40个Vector和20个Cube核。使用该接口可以自动获取合适的numBlocks值。
获取该值后，使用SetSimdNumBlocks进行numBlocks的设置。
## 函数原型
## 参数说明
## 返回值说明
返回用于底层任务调度的核数。
## 约束说明
无
