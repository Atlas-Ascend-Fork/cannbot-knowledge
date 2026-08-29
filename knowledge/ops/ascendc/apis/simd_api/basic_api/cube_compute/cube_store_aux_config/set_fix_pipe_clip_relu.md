---
type: API
title: SetFixPipeClipRelu
description: 在L0C Buffer到GM搬运随路量化后，设置ClipReLU操作的最大值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_aux_config/SetFixPipeClipRelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2]
---

# SetFixPipeClipRelu

DataCopy 数据搬运（L0C Buffer→GM）过程中进行随路量化后，设置 ClipReLU 操作的最大值。ClipReLU 计算公式为 min(clipReluMaxVal, srcData)。

参数：config 为 uint64_t 类型，表示 ClipReLU 的最大值 clipReluMaxVal。仅 Atlas 200I/500 A2 推理产品和 Kirin X90/9030 支持。

<!-- cannbot:related:start -->
## 相关

- [DataCopyL0CToGM](../cube_compute_store/data_copy_l0_c_to_gm.md)（`related`）：DataCopy 数据搬运（L0C Buffer→GM）过程中进行随路量化后，设置 ClipReLU 操作的最大值。ClipReLU 计算公式为 min(clipReluMaxVal, srcData)。；量化模式含 NoQuant、F322F16、F322BF16、DEQF16、VDEQF16、QF322B8_PRE、VQF322B8_PRE、REQ8、VREQ8，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag / SetFixpipeNz2ndFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。。SetFixPipeClipRelu 写入 L0C→GM 随路 ClipReLU 上限，DataCopyL0CToGM 明确在受支持平台消费该附加配置。
- [随路ReLU](../cube_store_key_features/accompanying_relu.md)（`related`）：开启Normal ReLU（reluPre=1）且同时配置clipReluPre=1并调用SetFixPipeClipRelu接口时，即Normal ReLU + ClipReLU，先执行`y = max(0, x)`，再执行`y = min(clipReluMaxVal, y)`，其中clipReluMaxVal通过SetFixPipeClipRelu接口设置。详见SetFixPipeClipRelu。；DataCopy 数据搬运（L0C Buffer→GM）过程中进行随路量化后，设置 ClipReLU 操作的最大值。ClipReLU 计算公式为 min(clipReluMaxVal, srcData)。。随路 ReLU 特性卡要求调用 SetFixPipeClipRelu 设置上界，API 卡给出 L0C 到 GM 搬运时的具体裁剪公式。
<!-- cannbot:related:end -->
