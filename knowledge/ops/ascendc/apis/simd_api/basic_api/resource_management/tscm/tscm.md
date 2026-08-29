---
type: API
title: TSCM
description: TSCM接口索引页，包含简介、AllocTensor、FreeTensor、EnQue与DeQue。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TSCM/TSCM.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# TSCM

TSCM是数据通路目的地为TSCM Position时的队列管理结构，本质是TQueBind的别名（TQueBind<pos, TPosition::TSCM, depth, mask>），用于Vector与Cube之间的通信和同步。
模板参数pos支持VECIN、GM；depth推荐设置为1；mask的bit 2控制VECTOR0/VECTOR1在CUBE内存位置的映射关系（0为错开，1为相同）。
支持AllocTensor/EnQue/DeQue/FreeTensor完整生命周期，须严格配对使用，但不支持VacantInQue/HasTensorInQue等查询接口。常与Matmul高阶API配合使用，L1 Buffer(TSCM)从UB发起的Buffer块数量与Matmul对象数量之和最大为10个，超出可能引起未定义行为。
