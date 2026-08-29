---
type: API
title: Concat（排序操作）
description: 对数据进行预处理，将要排序的源操作数src一一对应的合入目标数据concat中，数据预处理完成后，可以进行Sort。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/Concat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Concat

对数据进行预处理，将要排序的源操作数src一一对应合入目标数据concat中，预处理完成后可进行Sort操作。

函数原型：template <typename T> __aicore__ inline void Concat(LocalTensor<T>& concat, const LocalTensor<T>& src, const LocalTensor<T>& tmp, const int32_t repeatTime)

参数：concat为目标操作数（输出）；src为源操作数（输入）；tmp为临时缓存；repeatTime为重复次数。约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetConcatTmpSize](get_concat_tmp_size.md)（`related`）：获取Concat接口所需的临时空间大小。；对数据进行预处理，将要排序的源操作数src一一对应合入目标数据concat中，预处理完成后可进行Sort操作。。GetConcatTmpSize 给 Concat 排序预处理接口计算所需临时空间，形成 Host 资源准备到 kernel 预处理的直接合同。
- [Sort](sort.md)（`related`）：焦点卡说明“预处理完成后可进行Sort操作”，候选卡则要求 Sort“配合Concat（预处理）和Extract（结果提取）使用”；Concat 是排序前的实际数据整形阶段，而不是仅同属排序目录的 sibling。
<!-- cannbot:related:end -->
