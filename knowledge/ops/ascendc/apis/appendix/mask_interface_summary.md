---
type: API
title: Mask接口汇总（附录）
description: 汇总 Atlas A2、A3 系列接口的 isSetMask 参数支持情况及 Mask 设置方式。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/Mask_interface_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---


# Mask接口汇总（附录）

以下内容针对如下型号生效： - Atlas A3 训练系列产品/Atlas A3 推理系列产品 - Atlas A2 训练系列产品/Atlas A2 推理系列产品 本节汇总了各接口中模板参数isSetMask的支持情况。 针对Tensor前n个数计算和Tensor高维切分计算两种接口，Mask设置方式分为以下情形： - isSetMask参数情况： - 模板参数有isSetMask，支持接口外设置Mask。 - 模板参数无isSetMask，不支持接口外设置Mask。 - 模板参数有isSetMask，该参数不起作用。 - Mask设置方式： - 接口内已设置Mask：接口内部调用SetMaskCount、SetVectorMask、SetMaskNorm、ResetMask。

适用：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。
