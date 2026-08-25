---
type: API
title: RmsNorm Tiling
description: 获取RmsNorm kernel计算时所需的Tiling参数，包括通过GetRmsNormMaxMinTmpSize获取最大最小临时空间大小和GetRmsNormTilingInfo获取tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/RmsNorm-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# RmsNorm Tiling

host侧Tiling接口，用于获取RmsNorm kernel计算所需的Tiling参数，分两步：通过GetRmsNormMaxMinTmpSize获取最大和最小临时空间大小；通过GetRmsNormNDTilingInfo获取kernel侧所需tiling参数。

GetRmsNormMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。

GetRmsNormNDTilingInfo参数：ascendcPlatform平台信息；输入shape各维度(B,S,H)；typeSize数据类型字节数；isBasicBlock是否基本块；maxTmpSize可用临时空间；tiling输出RmsNormTiling结构体。约束：需保证H满足32B对齐。

<!-- cannbot:related:start -->
## 相关

- [A3 RMSNorm 不要用分母正值保护吞掉 NaN 传播](../../../../runbooks/precision/rmsnorm_nan_propagation_not_positive_guard.md)（`exemplifies`）：RmsNorm Tiling 与《A3 RMSNorm 不要用分母正值保护吞掉 NaN 传播》的实质衔接是：RmsNorm host tiling 直接生成 RmsNorm kernel 参数；同名结构体冲突、NaN/Rsqrt 与 UB 预算卡都作用于这套 tiling/kernel 契约。
- [RmsNormTiling 与 CANN 内置类型冲突 — 改名隔离](../../../../runbooks/compilation/tiling_type_name_does_not_shadow_cann_builtin.md)（`exemplifies`）：RmsNorm Tiling 与《RmsNormTiling 与 CANN 内置类型冲突 — 改名隔离》的实质衔接是：RmsNorm host tiling 直接生成 RmsNorm kernel 参数；同名结构体冲突、NaN/Rsqrt 与 UB 预算卡都作用于这套 tiling/kernel 契约。
- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](../../../../runbooks/precision/rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`exemplifies`）：RmsNorm Tiling 与《dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数》的实质衔接是：RmsNorm host tiling 直接生成 RmsNorm kernel 参数；同名结构体冲突、NaN/Rsqrt 与 UB 预算卡都作用于这套 tiling/kernel 契约。
- [golden BF16 rstd 归约误取 post-BF16 量化值](../../../../runbooks/precision/golden_bf16_rstd_post_bf16.md)（`exemplifies`）：RmsNorm Tiling 与《golden BF16 rstd 归约误取 post-BF16 量化值》的实质衔接是：RmsNorm host tiling 直接生成 RmsNorm kernel 参数；同名结构体冲突、NaN/Rsqrt 与 UB 预算卡都作用于这套 tiling/kernel 契约。
- [按 dtype 分配 UB 必须匹配 tiling 预算](../../../../runbooks/compilation/dtype_conditional_ub_allocation_matches_tiling_budget.md)（`exemplifies`）：RmsNorm Tiling 与《按 dtype 分配 UB 必须匹配 tiling 预算》的实质衔接是：RmsNorm host tiling 直接生成 RmsNorm kernel 参数；同名结构体冲突、NaN/Rsqrt 与 UB 预算卡都作用于这套 tiling/kernel 契约。
- [RmsNorm](rms_norm.md)（`same_topic`）：RmsNorm Tiling 与《RmsNorm》的实质衔接是：RmsNorm host tiling 直接生成 RmsNorm kernel 参数；同名结构体冲突、NaN/Rsqrt 与 UB 预算卡都作用于这套 tiling/kernel 契约。
<!-- cannbot:related:end -->
