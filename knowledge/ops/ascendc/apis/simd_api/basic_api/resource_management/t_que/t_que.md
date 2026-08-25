---
type: API
title: TQue
description: TQue接口索引页，包含简介、AllocTensor、FreeTensor、EnQue、DeQue及队列状态查询方法。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQue/TQue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TQue

TQue是Ascend C中用于流水任务间通信和同步的队列数据结构，继承自TQueBind。模板参数pos指定队列逻辑位置（VECIN/VECOUT/A1/A2/B1/B2/CO1/CO2），depth指定队列深度即连续入队次数，mask用于ND与NZ格式转换。
队列深度推荐设置为1，编译器对该场景有特殊优化；Tensor原地操作场景需设置为0。depth与double buffer无关，即使depth为1仍可开启double buffer。
同一TPosition上TQue Buffer数量受硬件eventID限制（训练系列产品为4，其他产品为8），开启double buffer时可用Buffer数减半。Buffer耗尽后可调用FreeAllEvent释放同步事件再继续申请。
