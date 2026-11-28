---
type: Runbook
title: C API 除法不接受标量分母时显式构造寄存器操作数
description: 从实例化签名确认寄存器对寄存器重载，用受支持的广播补齐操作数而不改写舍入路径。
tags: ["task.debugging", "topic.compilation", "topic.precision"]
status: draft
sources: []
created_at: "2026-11-11T03:06:30Z"
updated_at: "2026-11-11T04:13:48Z"
platforms: ["950"]
---

# C API 除法不接受标量分母时显式构造寄存器操作数

## 适用场景

C API 包装层的寄存器除法表达式不能仅凭数学形式推断存在“寄存器除标量”重载。若受测签名要求两个寄存器操作数，应先把标量广播为匹配的寄存器值，再调用除法。

## 症状与记录

dav-3510 工程的 C API 包装层 `operator/` 实例化中，直接传入标量分母不能匹配受测除法重载；通过 `asc_fill_l` 等该环境支持的寄存器广播路径构造分母后，改走寄存器对寄存器调用。此观测不覆盖所有类型、命名变体或版本。

## 定位与处理

1. 查看调用点实际选择的重载，记录分子、分母和结果的寄存器类型、元素类型与掩码。
2. 用单个 VF 的最小表达式验证广播加除法组合，确认广播在当前作用域和 dtype 下可实例化。
3. 保留原分母的类型转换与精度；不要为了消除重载错误自动替换为乘预计算倒数。
4. 对尾部设置与有效分子一致的消费范围，避免将无效 lane 结果用于后续归约。

## 验证边界

按接口合同测试普通值、±0、极大极小值及非有限值，检查目标 dtype 的输出与参考除法。编译通过只证明受测重载可用。草稿：尚待目标编译器和设备复核。

相关：[寄存器 asc_div 调用约束](../../guides/regbase/asc_div_reference_contract.md)用于核对原始 C 接口；[广播与标量替代](../../guides/vector/broadcast_addressing_and_scalar_substitution.md)给出一般选型边界；[量化中的除法与乘倒数](../precision/quantization_reciprocal_rewrite_rounding.md)解释为什么不应顺手改算术路径。
