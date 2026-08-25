---
type: API
title: Reciprocal
description: 单目矢量计算接口，对输入tensor按元素取倒数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Reciprocal.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Reciprocal

单目矢量计算接口，按元素计算倒数。头文件 `basic_api/kernel_operator_vec_unary_intf.h`。计算公式 dst_i = 1/src_i。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Reciprocal 低精度致 sigmoid 比对失败](../../../../../runbooks/precision/reciprocal_sigmoid.md)（`exemplifies`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《Reciprocal》说明单目矢量计算接口，对输入tensor按元素取倒数。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0](../../../../../runbooks/precision/arch35_sigmoid_z_exp_inf_sig_0.md)（`exemplifies`）：arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0 与《Reciprocal》的实质衔接是：该 sigmoid 失败由 exp(-z) 溢出和 subnormal FTZ 共同造成；Exp/Reciprocal/Clamp 接口及同类数值故障分别提供溢出阈值、稳定式和直接除法验证边界。
- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](../../../../../runbooks/precision/rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`exemplifies`）：Reciprocal 提供同类倒数接口对照；本卡最终选标量 1.0f/s，避免再次引入快速近似。
- [AscRcp](../../../c_api/vector_compute/asc_rcp.md)（`related`）：AscRcp 与《Reciprocal》都执行逐元素倒数；前者是 A2/A3 的 C 指针接口，后者是 LocalTensor 基础 API，操作契约相同而调用层不同。
<!-- cannbot:related:end -->
