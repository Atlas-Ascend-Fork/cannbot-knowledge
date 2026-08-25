---
type: Guide
title: 算子自验证说明
description: 本文档面向Ascend C算子开发者，提供单算子融合进SuperKernel的验证样例。算子开发完成后，可通过本文档中的样例自行验证算子是否支持融合进SuperKernel，包括功能正确性与精度对齐。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/super_kernel/operator_self_verification.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 算子自验证说明

本文档面向Ascend C算子开发者，提供单算子融合进SuperKernel的验证样例。算子开发完成后，可通过本文档中的样例自行验证算子是否支持融合进SuperKernel，包括功能正确性与精度对齐。
当前SuperKernel特性有两种开启方式：npugraph_ex后端和GE图模式，两种方式在前端开启方式上有所不同。开发者通常只需选择其中一种进行验证；如需在两种方式下均验证算子兼容性，可以分别参考下文样例。
## 验证思路
通用的单算子自验证思路如下：
1. 构造一个仅包含待验证算子的torch.nn.Module：构造一个原始版本（不开启SuperKernel）和一个SuperKernel版本（在算子调用处标定SuperKernel范围）。
2. 分别用图模式编译并执行两个模型：原始版本作为基准，SuperKernel版本作为目标。
3. 比对两个版本的输出：若数值完全相等（或在可接受误差范围内），则证明算子在SuperKernel下功能与精度正确。
4. 补充多算子联合验证：单算子验证能够排查大部分SuperKernel适配问题，是验证流程中必要且高效的第一步。但部分问题（如Cache一致性导致的精度差异）在单算子场景下通常不会暴露，需要在多个算子融合后的实际模型中才会显现。因此，单算子验证通过后，建议进一步构建多算子联合用例或在实际模型中验证，以确保算子在整网SuperKernel场景下的兼容性。
## npugraph_ex后端验证样例
npugraph_ex后端开启SuperKernel融合时，编译后端需使用"npugraph_ex"，并在options中显式传入super_kernel_optimize=True。如需控制融合范围，可通过torch.npu.super_kernel_scope_begin/torch.npu.super_kernel_scope_end一对接口进行标定。
### 示例代码
以下示例以torch_npu.npu_moe_gating_top_k_softmax为例，演示在npugraph_ex后端下的SuperKernel单算子验证：
### 关键点说明
- torch.npu.super_kernel_scope_begin(scope_name)/torch.npu.super_kernel_scope_end(scope_name)：成对出现，配对的scope_name必须一致。相同的scope_name代表相同的融合范围，由用户控制。若传入None，则该范围内的算子不进行SuperKernel融合。
- torch.compile(model, backend="npugraph_ex", options={...}, dynamic=False)：通过npugraph_ex后端下发图，仅支持静态图（dynamic=False）。super_kernel_optimize=True是开启SuperKernel融合优化的必要开关；其他融合优化与调试参数（如super_kernel_optimize_options、super_kernel_debug_options等）请参见SuperKernel功能。

<!-- cannbot:related:start -->
## 相关

- [SuperKernel原理介绍](principles.md)（`related`）：自验证确认任务命中、输出和同步，防止只看图编译成功。
- [核函数直调算子额外适配说明](kernel_direct_call_adaptation.md)（`related`）：对使用 >> 的直调算子，自验证前还需增加 __sk__ 入口、参数结构体与 SK_BIND，并保持 Kernel Type；否则测试失败不能归因于融合计算本身。
- [算子适配说明](operator_adaptation.md)（`related`）：自验证应在算子满足 SuperKernel 全核同步、MIX 比例和 DCache 一致性约束后执行；适配卡给出验证失败时应回查的具体前置契约。
<!-- cannbot:related:end -->
