---
type: API
title: FixpipeL0CToUB
description: 将L0C Buffer中的矩阵计算结果搬运至Unified Buffer，支持随路量化和格式转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/Fixpipe_L0CToUB.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# FixpipeL0CToUB

Fixpipe 是 L0C Buffer→Unified Buffer 的组合搬出接口，内部封装寄存器设置与数据搬运。头文件 `basic_api/kernel_operator_fixpipe_intf.h`。支持随路 scalar/tensor 量化、ReLU 和 NZ2ND/NZ2NZ/NZ2DN 格式转换。

按平台使用参数结构体：FixpipeParamsArch3510（950，支持 FP8/HIF8 等扩展量化模式）、FixpipeParamsM300（Atlas 200I/500 A2）。调用时模板 config 不能直接用 CFG_ROW_MAJOR 等预设值，须显式构造 `isToUB = true` 的 FixpipeConfig。

参数：dst 为 LocalTensor（UB，32B 对齐）；src 为 LocalTensor（L0C，NZ 64B 对齐）；intriParams；cbufWorkspace（tensor 量化参数，L1 32B 对齐）。关键字段：nSize[0,4095]、mSize[0,65535]、srcStride、dstStride、quantPre、deqScalar、reluEn、unitFlag(0/2/3)、dualDstCtrl（950 双目标模式 2'b00/01/10，按 M 或 N 维度拆分到两个 Vector Core 的 UB）、subBlockId。

数据类型 950：float→{int8_t,uint8_t,hifloat8_t,fp8_e4m3fn_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,bfloat16_t,int32_t}。Atlas 200I/500 A2：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。约束：mSize/nSize/ndNum 为 0 时 NOP；目标数据不能重叠写入；dualDstCtrl 仅支持 NZ2NZ/NZ2ND 场景。支持 950 和 Atlas 200I/500 A2。

<!-- cannbot:related:start -->
## 相关

- [Copy](../../cube_compute_tensor_api/cube_compute_store/copy_l0_c_to_ub.md)（`related`）：FixpipeL0CToUB 与《Copy》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [FixpipeL0CToGM](fixpipe_l0_c_to_gm.md)（`related`）：L0C→GM 与 L0C→UB Fixpipe 分别支持 GM 中转和 UB 直通融合数据流，目的层级决定后续 AIV 路径。
- [FixpipeL0CToL1](fixpipe_l0_c_to_l1.md)（`related`）：FixpipeL0CToUB 提供 L0C 结果直接交给 Vector 侧 UB 的通路，与 L0CToL1 的缓存复用场景形成明确的目的空间选型。
- [L1OrL0CUbDataMove](../../data_move_guide/l1_or_l0_c_ub_data_move.md)（`related`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《FixpipeL0CToUB》说明将L0C Buffer中的矩阵计算结果搬运至Unified Buffer，支持随路量化和格式转换。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [NZ2NZ](../cube_store_key_features/nz2_nz.md)（`related`）：L0C→UB 也可保持 NZ，并可结合双目标模式，但需满足其拆分约束。
- [SetFixPipeAddr](../cube_store_aux_config/set_fix_pipe_addr.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《FixpipeL0CToUB》说明将L0C Buffer中的矩阵计算结果搬运至Unified Buffer，支持随路量化和格式转换。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [SetFixPipeClipRelu](../cube_store_aux_config/set_fix_pipe_clip_relu.md)（`related`）：FixpipeL0CToUB 与《SetFixPipeClipRelu》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [SetFixpipePreQuantFlag](../cube_store_aux_config/set_fixpipe_pre_quant_flag.md)（`related`）：FixpipeL0CToUB 与《SetFixpipePreQuantFlag》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [随路量化与随路ReLU场景组合](../cube_store_key_features/accompanying_quantization_and_relu_scenario_combination.md)（`related`）：FixpipeL0CToUB 与《随路量化与随路ReLU场景组合》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [CopyL1ToFixpipe](../../cube_compute_tensor_api/cube_compute_load/copy_l1_to_fixpipe.md)（`same_topic`）：CopyL1ToFixpipe 与《FixpipeL0CToUB》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [DataCopy（L0C Buffer到UB数据搬运）](data_copy_l0_c_to_ub.md)（`same_topic`）：FixpipeL0CToUB 与《DataCopy（L0C Buffer到UB数据搬运）》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [L0C Buffer内存结构介绍](l0_c_memory_structure_intro.md)（`same_topic`）：FixpipeL0CToUB 与《L0C Buffer内存结构介绍》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [L0C Buffer到UB双目标模式](../cube_store_key_features/l0_c_to_ub_dual_target_mode.md)（`same_topic`）：FixpipeL0CToUB 与《L0C Buffer到UB双目标模式》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [SetFixPipeConfig](../cube_store_aux_config/set_fix_pipe_config.md)（`same_topic`）：FixpipeL0CToUB 与《SetFixPipeConfig》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [UnitFlag](../../cube_compute_tensor_api/mmad_compute_key_features/unit_flag.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《FixpipeL0CToUB》提供“将L0C Buffer中的矩阵计算结果搬运至Unified Buffer，支持随路量化和格式转换。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
<!-- cannbot:related:end -->
