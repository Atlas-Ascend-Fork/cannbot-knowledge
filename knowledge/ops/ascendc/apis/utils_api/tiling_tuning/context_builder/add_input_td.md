---
type: API
title: AddInputTd
description: 为算子增加输入Tensor的描述
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/AddInputTd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AddInputTd

## 功能说明
为算子增加输入Tensor的描述
## 函数原型
## 参数说明
## 返回值说明
当前ContextBuilder的对象。
## 约束说明
输入的index需要基于算子IR定义，按照IrInstanceNum声明顺序来排布；
调用AddInputTd前需要调用NodeIoNum与IrInstanceNum接口

<!-- cannbot:related:start -->
## 相关

- [IrInstanceNum](ir_instance_num.md)（`related`）：“输入的index需要基于算子IR定义，按照IrInstanceNum声明顺序来排布”；“参数 instanceNum 为按输入 index 顺序声明的实例化个数向量”。IrInstanceNum 生产动态输入实例顺序，AddInputTd 必须按该顺序消费 index。
- [NodeIoNum](node_io_num.md)（`related`）：“调用AddInputTd前需要调用NodeIoNum与IrInstanceNum接口”；“先通过 NodeIoNum 设置输入输出个数，再通过 IrInstanceNum 设置每种输入的实例化个数”。NodeIoNum 是 AddInputTd 索引布局的显式前置，决定输入 index 空间。
<!-- cannbot:related:end -->
