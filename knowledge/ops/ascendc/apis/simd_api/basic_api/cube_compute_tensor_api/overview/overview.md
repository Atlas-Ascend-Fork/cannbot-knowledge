---
type: API
title: 概述
description: TensorAPI 矩阵计算概述，介绍矩阵计算单元与搬入、Mmad、搬出的基础计算流程。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/overview/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 概述概述概述

## 矩阵计算单元

矩阵计算单元的详细描述请参考LINK。

## 矩阵计算流程

Tensor API针对矩阵计算编程模型提供了两类接口，分别承载Cube核中各个通路的搬运能力和计算能力，如下图所示：

**图1**  普通矩阵基础计算流程图

1. 通过`Copy`接口将A、B原始矩阵的Global Memory数据搬运到L1 Buffer中（如果存在Bias/随路量化，则同样通过`Copy`搬运到L1 Buffer中）。详细内容请参考矩阵计算的搬入。

2. 通过`Copy`接口将A、B矩阵分别加载到L0A Buffer和L0B Buffer上准备计算（如果存在Bias/随路量化，则通过`Copy`将L1 Buffer中的Bias数据/量化系数数据搬运到BiasTable Buffer/Fixpipe Buffer上）。详细内容请参考矩阵计算的搬入。

3. 通过`Mmad`接口对L0A Buffer、L0B Buffer、BiasTable Buffer上面的数据进行矩阵计算，并输出结果到L0C Buffer上。详细内容请参考Mmad计算。

4. 通过`Copy`接口将L0C Buffer的数据进行处理并搬出到Global Memory，`Copy`接口可以利用Fixpipe Buffer数据进行如随路量化、Relu等操作。详细内容请参考矩阵计算的搬出。
