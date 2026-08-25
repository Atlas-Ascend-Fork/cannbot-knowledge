---
type: API
title: SetFixpipePreQuantFlag
description: DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置scalar量化参数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_aux_config/SetFixpipePreQuantFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetFixpipePreQuantFlag

DataCopy 数据搬运（L0C Buffer→GM、L0C Buffer→L1 Buffer）过程中进行随路 scalar 量化时，设置 scalar 量化参数。此参数代表整个输出矩阵使用的单一量化参数。

参数：config 为 uint64_t 类型，表示 scalar 量化参数。支持 950/a2/a3/Atlas 200I/500 A2/Kirin X90/9030，不支持 Atlas 推理 AI Core/Vector Core/Atlas 训练系列。

<!-- cannbot:related:start -->
## 相关

- [AscGetL0c2gmPrequant](../../../c_api/cube_compute/asc_get_l0c2gm_prequant.md)（`related`）：AscGetL0c2gmPrequant 与《SetFixpipePreQuantFlag》的实质衔接是：AscGetL0c2gmPrequant 读取随路量化前矢量地址，AscSetL0cCopyPrequant、总配置和 C++ prequant flag 是写入并启用同一状态的控制端。
- [FixpipeL0CToGM](../cube_compute_store/fixpipe_l0_c_to_gm.md)（`related`）：该参数在 Fixpipe 将 L0C 结果搬到 GM 时生效，二者构成参数设置与数据搬出的上下游。
- [FixpipeL0CToUB](../cube_compute_store/fixpipe_l0_c_to_ub.md)（`related`）：FixpipeL0CToUB 与《SetFixpipePreQuantFlag》的实质衔接是：Fixpipe L0C→UB 的搬出依赖 L0C 布局、Fixpipe 配置/地址、clip/quant 标志及双目标模式，所选卡均直接改变这条搬运。
- [SetFixPipeConfig](set_fix_pipe_config.md)（`related`）：SetFixpipePreQuantFlag 提供 scalar 量化参数，SetFixPipeConfig 把量化配置组织到 L0C 搬出路径。
- [AccompanyingQuantization](../cube_store_key_features/accompanying_quantization.md)（`same_topic`）：“AccompanyingQuantization”处理矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。；“SetFixpipePreQuantFlag”明确DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置scalar量化参数。。实质衔接：随路量化发生在 L0C 搬出路径，量化模式决定 scalar/Tensor 参数应写入寄存器还是 Fixpipe Buffer，并由对应搬出和配置接口落地。
- [CopyL1ToFixpipe](../../cube_compute_tensor_api/cube_compute_load/copy_l1_to_fixpipe.md)（`same_topic`）：CopyL1ToFixpipe 与《SetFixpipePreQuantFlag》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [矩阵搬出寄存器配置说明](cube_store_aux_config.md)（`same_topic`）：矩阵搬出寄存器配置说明 与《SetFixpipePreQuantFlag》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
<!-- cannbot:related:end -->
