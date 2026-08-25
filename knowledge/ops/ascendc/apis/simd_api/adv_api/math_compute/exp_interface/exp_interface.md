---
type: API
title: Exp接口
description: 按元素取自然指数，可选泰勒展开计算，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Exp_interface/Exp_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Exp接口

按元素取自然指数，可选泰勒展开计算，并提供临时空间大小获取接口。

按元素取自然指数，用户可以选择是否使用泰勒展开公式进行计算，计算公式如下： - 设置泰勒展开项数为0，即不使用泰勒展开公式进行计算，公式如下： - 设置泰勒展开项数不为0，即使用泰勒展开公式进行计算，公式如下： xA i 代表源操作数的整数部分，该值通过floor(x)获取。xB i 代表源操作数的小数部分。 泰勒展开公式如下：

本接口组包含 Exp。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 向量管 FTZ 刷新次正规 exp 为零](../../../../../runbooks/precision/ascend950_ftz_exp.md)（`exemplifies`）：Ascend950 向量管 FTZ 刷新次正规 exp 为零 与《Exp接口》的实质衔接是：该卡锁定 Ascend950 Exp 次正规输出 FTZ；Exp 接口、clamp/overflow/subnormal 姊妹故障和 softplus 极值用例共同验证硬件边界与可修软件因素。
- [Exp 默认 INTRINSIC FTZ 致 subnormal 残留失配](../../../../../runbooks/precision/exp_intrinsic_ftz_subnormal.md)（`exemplifies`）：Runbook 用真实 subnormal 输入证明高阶 Exp 默认 INTRINSIC 路径受 FTZ 影响，并以 TAYLOR 配置对照闭合误差；这是 Exp 接口算法选择在极小值域的具体精度边界。
- [arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0](../../../../../runbooks/precision/arch35_sigmoid_z_exp_inf_sig_0.md)（`exemplifies`）：arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0 与《Exp接口》的实质衔接是：该 sigmoid 失败由 exp(-z) 溢出和 subnormal FTZ 共同造成；Exp/Reciprocal/Clamp 接口及同类数值故障分别提供溢出阈值、稳定式和直接除法验证边界。
- [exp 输入 clamp 上界用 threshold 用户参数致溢出](../../../../../runbooks/precision/exp_clamp_upper_bound_must_decouple_from_user_threshold.md)（`exemplifies`）：exp 输入 clamp 上界用 threshold 用户参数致溢出 与《Exp接口》的实质衔接是：故障由用户 threshold 充当 Exp 安全上界导致；Exp、Clamp/Mins、Sigmoid 公式及溢出/FTZ/Softplus 分支案例共同限定固定上界和极值验收。
- [Exp](exp.md)（`same_topic`）：Exp 与《Exp接口》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
- [GetExpMaxMinTmpSize](get_exp_max_min_tmp_size.md)（`same_topic`）：Exp 总页定义 MaxMinTmpSize、FactorSize 与 Exp 调用的完整 workspace 流程。
- [GetExpTmpBufferFactorSize](get_exp_tmp_buffer_factor_size.md)（`same_topic`）：GetExpTmpBufferFactorSize 与《Exp接口》的实质衔接是：该因子查询与 Exp、Exp 接口页及最大最小临时空间查询共同定义固定 UB 容量下单次可计算元素数。
<!-- cannbot:related:end -->
