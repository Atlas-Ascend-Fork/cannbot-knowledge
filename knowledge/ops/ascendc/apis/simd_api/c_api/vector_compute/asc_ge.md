---
type: API
title: AscGe
description: Ge（greater than or equal to），逐元素比较src0 >= src1是否成立，成立则输出结果为1，否则输出结果为0，每个元素的比较结果占一个bit。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_ge.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscGe

Ge（greater than or equal to），逐元素比较src0 >= src1是否成立，成立则输出结果为1，否则输出结果为0，每个元素的比较结果占一个bit。计算公式如下：
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src0、src1的起始地址需要32字节对齐。；dst按照小端顺序排序成二进制结果，对应src中相应位置的数据比较结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [GE图模式263: 自定义VF Select被禁](../../../../runbooks/compilation/ge_263_vf_select.md)（`exemplifies`）：《GE图模式263: 自定义VF Select被禁》给出“MaskedFill kernel 用 __simd_vf__/asc_vf_call 自定义 VF 实现 Select，aclnn 预编译全绿但 GE 图模式 TBE 动态编译生成坏 binary 触发 AI Core error 263（aivec）；须跑图模式的 regbase kernel 中自定义 VF 路线 banned。”；该约束/探针可直接复现、解释或前置验证《AscGe》中的“Ge（greater than or equal to），逐元素比较src0 >= src1是否成立，成立则输出结果为1，否则输出结果为0，每个元素的比较结果占一个bit。”。
- [aclnn 全绿但 GE 图模式 error 263 分层判别](../../../../runbooks/compilation/aclnn_ge_error_263.md)（`exemplifies`）：《aclnn 全绿但 GE 图模式 error 263 分层判别》给出“aclnn 预编译 ST 全绿但 GE 图模式 TBE 动态编译 RunGraph 触发 AI Core error 263(aivec) 时，用 plog/kernel-JSON/空张量探针区分「tiling 未传递误判」「tiling 大小未注册」「kernel 向量指令执行期崩」三类原因；arg5=0 不代表 tiling 未传递（sysParam 单独传递），空张量 RunGraph 成功即排除图基础设施。”；该约束/探针可直接复现、解释或前置验证《AscGe》中的“Ge（greater than or equal to），逐元素比较src0 >= src1是否成立，成立则输出结果为1，否则输出结果为0，每个元素的比较结果占一个bit。”。
- [AscGe](../reg/compare_and_select/asc_ge.md)（`same_topic`）：《AscGe》明确“逐元素比较两个源操作数是否大于等于，比较结果写入目的操作数对应比特位，为真则置1，否则置0。”；它与《AscGe》的“Ge（greater than or equal to），逐元素比较src0 >= src1是否成立，成立则输出结果为1，否则输出结果为0，每个元素的比较结果占一个bit。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscGeScalar](../reg/compare_and_select/asc_ge_scalar.md)（`same_topic`）：《AscGeScalar》明确“对源操作数执行逐元素比较，若src_i大于等于标量value则目的操作数对应结果位为1，否则为0，每个元素比较结果占一个bit。”；它与《AscGe》的“Ge（greater than or equal to），逐元素比较src0 >= src1是否成立，成立则输出结果为1，否则输出结果为0，每个元素的比较结果占一个bit。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
