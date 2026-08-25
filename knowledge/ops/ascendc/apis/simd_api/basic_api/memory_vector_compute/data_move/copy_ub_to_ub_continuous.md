---
type: API
title: Copy
description: 支持UB之间的连续数据搬运，数据搬运时格式和内容保持不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/Copy_UBToUB_continuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Copy

支持UB之间的连续数据搬运，数据搬运时格式和内容保持不变。

支持Unified Buffer和Unified Buffer之间的连续数据搬运，数据搬运时格式和内容保持不变。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Unified Buffer -> Unified Buffer - VECIN -> VECCALC - VECIN -> VECOUT - VECCALC -> VECIN - VECCALC -> VECOUT - VECOUT -> VECIN - VECOUT -> VECCALC

支持的数据通路：具体支持的数据通路为（以逻辑位置TPosition表示）：

- Unified Buffer -> Unified Buffer
    - VECIN -> VECCALC
    - VECIN -> VECOUT
    - VECCALC -> VECIN
    - VECCALC -> VECOUT
    - VECOUT -> VECIN
    - VECOUT -> VECCALC


本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

参数说明：T：源操作数或者目的操作数的数据类型。支持的数据类型请参考[数据类型](#zh-cn_topic_0000002567699435_section42191353048181)。；isSetMask：参数不生效，保持默认值true即可。；dst：输出 目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。起始地址需要保证32字节对齐。；src：输入 源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。起始地址需要保证32字节对齐。 源操作数的数据类型需要与目的操作数保持一致。；count：输入 参与搬运的元素个数。

约束：位于Unified Buffer的地址必须32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。；isSetMask参数不生效，保持默认值true即可。

<!-- cannbot:related:start -->
## 相关

- [fp32 UB 非 VL 拷贝须用带掩码 Reg](../../../../../runbooks/precision/non_vl_fp32_ub_copy_needs_masked_reg_load_store.md)（`exemplifies`）：Copy 与《fp32 UB 非 VL 拷贝须用带掩码 Reg》的实质衔接是：该 Copy 是 32B 对齐的 UB 连续搬运；DataCopy 对应入口、UB-UB 搬运指南、AscCopy 与非 VL 掩码故障共同说明通路、对齐和尾块边界。
- [模板内 float→float Cast 使 fp32 分支全错](../../../../../runbooks/precision/templated_float_input_must_bypass_same_type_cast.md)（`exemplifies`）：模板内 float→float Cast 使 fp32 分支全错 与《Copy》的实质衔接是：float 到 float 不应进入窄化 Cast，应该保持原值或 Copy；同步、BF16 分阶段、native 类型、VL、舍入与 RmsNorm 案例分别说明真正需要 Cast 时的类型、时序和验证契约。
- [连续计算API](../../../../../guides/programming_guide/library_api/basic_api/interface_classification/continuous_compute_api.md)（`explains`）：Copy 与《连续计算API》的实质衔接是：该 Copy 是 32B 对齐的 UB 连续搬运；DataCopy 对应入口、UB-UB 搬运指南、AscCopy 与非 VL 掩码故障共同说明通路、对齐和尾块边界。
- [连续非对齐场景优化](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/continuous_unaligned_optimization.md)（`explains`）：Copy 与《连续非对齐场景优化》的实质衔接是：该 Copy 是 32B 对齐的 UB 连续搬运；DataCopy 对应入口、UB-UB 搬运指南、AscCopy 与非 VL 掩码故障共同说明通路、对齐和尾块边界。
- [AscCopy](../../../c_api/reg/reg_load/asc_copy.md)（`related`）：Copy 与《AscCopy》的实质衔接是：该 Copy 是 32B 对齐的 UB 连续搬运；DataCopy 对应入口、UB-UB 搬运指南、AscCopy 与非 VL 掩码故障共同说明通路、对齐和尾块边界。
- [UB与UB数据搬运](../../data_move_guide/ub_ub_data_move.md)（`related`）：Copy 与《UB与UB数据搬运》的实质衔接是：该 Copy 是 32B 对齐的 UB 连续搬运；DataCopy 对应入口、UB-UB 搬运指南、AscCopy 与非 VL 掩码故障共同说明通路、对齐和尾块边界。
- [AscCopy](../../../c_api/vector_compute/asc_copy.md)（`same_topic`）：AscCopy 与《Copy》的实质衔接是：AscCopy 是 UB→UB 搬运；basic Copy、UB 搬运指南和 Reg Copy提供连续、高维/掩码入口，非整 VL 的 fp32 案例说明何时必须改用 masked Reg load/store。
- [Copy](copy_ub_to_ub_mask_highdim_split.md)（`same_topic`）：Copy 与《Copy》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [DataCopy](data_copy_ub_to_ub_continuous.md)（`same_topic`）：《DataCopy》说明支持UB之间的连续数据搬运，数据传输过程中保持原始格式和内容不变。；《Copy》说明支持UB之间的连续数据搬运，数据搬运时格式和内容保持不变。。二者在两页分别给出UB到UB连续Copy与高维切分DataCopy，直接决定连续布局和切分布局下的接口选择上存在可执行的直接衔接。
- [数据搬运](data_move.md)（`same_topic`）：Copy 与《数据搬运》的实质衔接是：该 Copy 是 32B 对齐的 UB 连续搬运；DataCopy 对应入口、UB-UB 搬运指南、AscCopy 与非 VL 掩码故障共同说明通路、对齐和尾块边界。
<!-- cannbot:related:end -->
