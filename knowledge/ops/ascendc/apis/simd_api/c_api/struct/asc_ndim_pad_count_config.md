---
type: API
title: AscNdimPadCountConfig
description: 用于设置asc_ndim_copy_gm2ub接口各维度左右侧的padding元素个数。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/struct/asc_ndim_pad_count_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AscNdimPadCountConfig

asc_ndim_pad_count_config用于asc_set_ndim_pad_count接口中，设置asc_ndim_copy_gm2ub接口的各个维度左右侧的padding元素个数。

字段：loop1_lp_count：表示1维左侧需要补齐的元素个数。  单位为元素个数，取值范围为[0, 255]，默认值为0。；loop1_rp_count：表示1维右侧需要补齐的元素个数。  单位为元素个数，取值范围为[0, 255]，默认值为0。；loop2_lp_count：表示2维左侧需要补齐的元素个数。  单位为元素个数，取值范围为[0, 255]，默认值为0。；loop2_rp_count：表示2维右侧需要补齐的元素个数。  单位为元素个数，取值范围为[0, 255]，默认值为0。；loop3_lp_count：表示3维左侧需要补齐的元素个数。  单位为元素个数，取值范围为[0, 255]，默认值为0。；loop3_rp_count：表示3维右侧需要补齐的元素个数。  单位为元素个数，取值范围为[0, 255]，默认值为0。
