---
type: API
title: RmsNorm
description: 实现对shape为[B,S,H]输入数据的RmsNorm归一化，其中γ为缩放系数，ε为防除零的权重系数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/RmsNorm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# RmsNorm

对shape为[B,S,H]的输入数据做RmsNorm归一化。计算公式：y = x / sqrt(mean(x²) + ε) * γ，其中γ为缩放系数，ε为防除零系数。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过RmsNorm Tiling获取。模板参数isBasicBlock在满足基本块要求（H为64的倍数且小于2048，B*S为8的倍数）时可设为true提升性能。

接口参数：dstLocal输出归一化结果（shape与srcLocal一致）；srcLocal输入（shape [B,S,H]，尾轴H需32B对齐）；gammaLocal缩放系数（shape [H]）；sharedTmpBuffer临时缓存；epsilon防除零系数；tiling切分信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：dstLocal和gammaLocal的Tensor空间不允许复用；仅支持ND格式；H轴非32B对齐时需补齐到32B对齐；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [A3 RMSNorm 不要用分母正值保护吞掉 NaN 传播](../../../../runbooks/precision/rmsnorm_nan_propagation_not_positive_guard.md)（`exemplifies`）：RmsNorm 接口定义平方均值、epsilon 和缩放计算，本卡具体化该计算链必须保留规约 NaN，而不能用正值 guard 清洗。
- [BF16 gamma Cast 分阶段编排导致随机 NaN](../../../../runbooks/precision/bf16_gamma_cast_must_share_ordered_compute_stage.md)（`exemplifies`）：本卡最终消费者是 RmsNorm<float,false>，gammaFp32 与 srcFp32 都完成后才能调用。
- [Reduce work buf 额外占 UB 致 507035](../../../../runbooks/compilation/reduce_work_buf_ub_507035.md)（`exemplifies`）：Runbook 在 Add+RmsNorm 融合中验证为 Reduce work buffer 额外分配整行 fp32 会把大 H 的 UB 推到超限并触发 507035，为 RmsNorm 临时空间设计提供直接故障边界。
- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](../../../../runbooks/precision/rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`exemplifies`）：本卡只替换 RmsNorm rstd 末端，规约、均值、epsilon 链不变。
- [模板内 float→float Cast 使 fp32 分支全错](../../../../runbooks/precision/templated_float_input_must_bypass_same_type_cast.md)（`exemplifies`）：模板内 float→float Cast 使 fp32 分支全错 与《RmsNorm》的实质衔接是：float 到 float 不应进入窄化 Cast，应该保持原值或 Copy；同步、BF16 分阶段、native 类型、VL、舍入与 RmsNorm 案例分别说明真正需要 Cast 时的类型、时序和验证契约。
- [RmsNorm Tiling](rms_norm_tiling.md)（`same_topic`）：RmsNorm Tiling 与《RmsNorm》的实质衔接是：RmsNorm host tiling 直接生成 RmsNorm kernel 参数；同名结构体冲突、NaN/Rsqrt 与 UB 预算卡都作用于这套 tiling/kernel 契约。
<!-- cannbot:related:end -->
