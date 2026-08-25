---
type: API
title: SoftmaxFlashV2
description: SoftmaxFlash增强版本，对应FlashAttention-2算法，支持通过isUpdate参数控制是否根据前一次的sum和max更新当前结果，支持ND和NZ格式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftmaxFlashV2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SoftmaxFlashV2

SoftmaxFlash增强版本，对应FlashAttention-2算法。将输入tensor[m0, m1, ...mt, n]（t大于等于0）的非尾轴长度相乘的结果看作m，则输入tensor的shape看作[m, n]。对输入tensor[m,n]按行做如下计算，不同的update值对应不同的计算公式，其中x、inmax和insum为输入，M、S、E均为输出。 update 为 false 与 true 时采用不同公式，具体输入输出关系见固定来源。

函数原型：template <typename T, bool isUpdate = false, bool isReuseSource = false, bool isBasicBlock = false, bool isDataFormatNZ = false, const SoftmaxConfig& config = SOFTMAX_DEFAULT_CFG>

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isUpdate：是否开启update部分中的计算。
- isReuseSource：该参数预留，传入默认值false即可。
约束：
- srcTensor和dstTensor的Tensor的空间可以复用，maxTensor和inMaxTensor的空间可以复用，expSumTensor和inExpSumTensor的空间可以复用。
- 除 SoftmaxMode::SOFTMAX_OUTPUT_WITHOUT_BRC 非拓展模式外，expSumTensor、maxTensor、expMaxTensor、inExpSumTensor 和 inMaxTensor 的 last 轴长度必须固定为 32 Byte。
- 对于输出ReduceMax的接口：

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。

<!-- cannbot:related:start -->
## 相关

- [flash在线softmax JIT重排致精度超阈](../../../../../runbooks/precision/flash_softmax_jit.md)（`exemplifies`）：《SoftmaxFlashV2》处理“SoftmaxFlash增强版本，对应FlashAttention-2算法，支持通过isUpdate参数控制是否根据前一次的sum和max更新当前结果，支持ND和NZ格式。”。《flash在线softmax JIT重排致精度超阈》提供“flash 在线 softmax 的 mi/li/oi 循环依赖对执行顺序敏感；loop_unroll_list、device_sched_mode、cube_nbuffer_setting 任一调离默认值都会改变 C1 任务执行顺序，引入 BF16 ULP 级累积误差 0.00048828 超逐位置阈值，三参数对在线 softmax 算子 banned。”，其具体合同或探针直接接入Flash softmax 的 update 状态、专用 Tiling 与在线 mi/li 依赖。
- [unroll s2 内层循环破坏 flash 在线 softmax 循环态](../../../../../runbooks/precision/unroll_s2_flash_softmax.md)（`exemplifies`）：《SoftmaxFlashV2》处理“SoftmaxFlash增强版本，对应FlashAttention-2算法，支持通过isUpdate参数控制是否根据前一次的sum和max更新当前结果，支持ND和NZ格式。”。《unroll s2 内层循环破坏 flash 在线 softmax 循环态》提供“对 flash attention 主循环 FLASH_LOOP_L4_s2_SA 把 unroll_list 由 {1} 扩为 {1,2} 会破坏 is_loop_begin/end 的循环态边界，使在线 softmax 的 li/mi 状态在 s2 步间错位、atten_out 大面积精度回归（8306526 误差点/阈值 41943，max_diff 0.066）。该展开路线 banned，性能优化改走 pass_option/TileShape。”，其具体合同或探针直接接入Flash softmax 的 update 状态、专用 Tiling 与在线 mi/li 依赖。
- [SoftMax Tiling使用说明](soft_max_tiling_usage.md)（`related`）：《SoftmaxFlashV2》处理“SoftmaxFlash增强版本，对应FlashAttention-2算法，支持通过isUpdate参数控制是否根据前一次的sum和max更新当前结果，支持ND和NZ格式。”。《SoftMax Tiling使用说明》提供“Ascend C提供一组SoftMax Tiling API，方便用户获取SoftMax kernel计算时所需的Tiling参数。”，其具体合同或探针直接接入Flash softmax 的 update 状态、专用 Tiling 与在线 mi/li 依赖。
- [SoftmaxFlashV3](softmax_flash_v3.md)（`related`）：V2 与 V3 都承载可复用 sum/max 的在线 Softmax；V2 还支持 NZ，而 V3 收紧为 ND 和特定 n/m 对齐条件，二者可用于按格式与约束选型。
- [SoftmaxFlashV3 Tiling接口](softmax_flash_v3_tiling_interface.md)（`related`）：《SoftmaxFlashV3 Tiling接口》处理“用于获取SoftmaxFlashV3接口所需的Tiling参数。”。《SoftmaxFlashV2》明确“SoftmaxFlash增强版本，对应FlashAttention-2算法，支持通过isUpdate参数控制是否根据前一次的sum和max更新当前结果，支持ND和NZ格式。”，可直接用于核对SoftmaxFlashV3 的 Kernel 参数、专用 Tiling、update 状态与在线 softmax 数值依赖。
- [SoftmaxFlash](softmax_flash.md)（`same_topic`）：《SoftmaxFlashV2》处理“SoftmaxFlash增强版本，对应FlashAttention-2算法，支持通过isUpdate参数控制是否根据前一次的sum和max更新当前结果，支持ND和NZ格式。”。《SoftmaxFlash》提供“Softmax增强版本，可根据上一次Softmax计算的sum和max更新本次结果，适用于last轴切轴场景，不开启update时等同于SoftMax。即将废弃，建议使用SoftmaxFlashV2。”，其具体合同或探针直接接入Flash softmax 的 update 状态、专用 Tiling 与在线 mi/li 依赖。
- [SoftmaxFlash Tiling接口](softmax_flash_tiling_interface.md)（`same_topic`）：《SoftmaxFlashV2》处理“SoftmaxFlash增强版本，对应FlashAttention-2算法，支持通过isUpdate参数控制是否根据前一次的sum和max更新当前结果，支持ND和NZ格式。”。《SoftmaxFlash Tiling接口》提供“注意：该接口后续即将废弃，新开发内容不要使用该接口。 用于获取SoftmaxFlash Tiling参数。”，其具体合同或探针直接接入Flash softmax 的 update 状态、专用 Tiling 与在线 mi/li 依赖。
- [SoftmaxFlashV2 Tiling接口](softmax_flash_v2_tiling_interface.md)（`same_topic`）：《SoftmaxFlashV2》处理“SoftmaxFlash增强版本，对应FlashAttention-2算法，支持通过isUpdate参数控制是否根据前一次的sum和max更新当前结果，支持ND和NZ格式。”。《SoftmaxFlashV2 Tiling接口》提供“用于获取SoftmaxFlashV2接口所需的Tiling参数。”，其具体合同或探针直接接入Flash softmax 的 update 状态、专用 Tiling 与在线 mi/li 依赖。
<!-- cannbot:related:end -->
