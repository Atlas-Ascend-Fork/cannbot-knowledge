---
type: API
title: DataCopy
description: 多维数据搬运接口，支持自由配置搬入的维度信息及对应的Stride。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMToUB_NDDMA.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# DataCopy

多维数据搬运接口，支持自由配置搬入的维度信息及对应的Stride。

多维数据搬运接口，相比于基础数据搬运接口，可更加自由配置搬入的维度信息以及对应的Stride。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN

支持的数据通路：具体支持的数据通路为（以逻辑位置TPosition表示）：

- Global Memory -> Unified Buffer
    - GM -> VECIN


本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

参数说明：T：源操作数或者目的操作数的数据类型。；dim：搬运的数据维度，数据类型为uint8_t，支持的维度为[1, 5]。；config：搬运配置选项，NdDmaConfig类型，定义如下，具体参数说明请参考[表3](#table_nddma_3)。 struct NdDmaConfig {     static constexpr uint16_t unsetPad = 0xffff;     bool isNearestValueMode = false;     uint16_t loopLpSize = unsetPad; // Left padding size of all dimensions, must be less than 256.     uint16_t loopRpSize = unsetPad; // Right padding size of all dimensions, must be less than 256.     bool ascOptimize = false;       // used for Ascend C optimization on special scenario. };；dst：输出 目的操作数，类型为LocalTensor。；src：输入 源操作数，类型为GlobalTensor。

约束：一条指令所能获取的所有数据的地址范围宽度不能超过40位（1TB），即：；源操作数的每一次循环的大小为：(loopLpSize + loopSize + loopRpSize -1 ) * loopSrcSize，目的操作数的每一次循环的大小为：(loopLpSize + loopSize + loopRpSize -1 ) * loopDstSize，所有的循环的大小加起来不超过2的40次方位。；当每层循环的dstStride为升序序列，则不同循环间的地址空间不能交织或者重叠。以一个2D Padding场景为例，loopSrcStride、loopDstStride第二个维度的stride值最小是3，数据3不能落在维度1的循环中。；该接口通过NDDMA进行数据搬运，对应的NDDMA Cache大小为32KB，在使用DataCopy接口进行数据搬运前，需要使用NdDmaDci接口刷新缓存，否则多核场景下读写同一块Global Memory地址可能会导致部分核读取数据错误。

<!-- cannbot:related:start -->
## 相关

- [DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零](../../../../../runbooks/precision/datacopy_gm_to_ub_non_32b_aligned_silent_zero.md)（`exemplifies`）：DataCopy 与《DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零》的实质衔接是：该 DataCopy 是 GM→UB NDDMA，多维 shape/stride、NdDmaDci 与非对齐 padding 是直接契约；所选故障卡覆盖漏维、stride=0 和 cache 刷新边界。
- [DataCopyPad 加载缺少 Pad 参数导致编译失败](../../../../../runbooks/compilation/datacopypad_gm_to_ub_requires_pad_params.md)（`exemplifies`）：DataCopy 与《DataCopyPad 加载缺少 Pad 参数导致编译失败》的实质衔接是：该 DataCopy 是 GM→UB NDDMA，多维 shape/stride、NdDmaDci 与非对齐 padding 是直接契约；所选故障卡覆盖漏维、stride=0 和 cache 刷新边界。
- [NDDMA 快速路径 C=1 中间轴漏维判别](../../../../../runbooks/precision/nddma_c_1.md)（`exemplifies`）：DataCopy 与《NDDMA 快速路径 C=1 中间轴漏维判别》的实质衔接是：该 DataCopy 是 GM→UB NDDMA，多维 shape/stride、NdDmaDci 与非对齐 padding 是直接契约；所选故障卡覆盖漏维、stride=0 和 cache 刷新边界。
- [NDDMA 最内层 srcStride=0 广播读越界](../../../../../runbooks/precision/nddma_srcstride_0.md)（`exemplifies`）：官方 DataCopy 多维搬运接口定义 MultiCopyParams/Stride 的调用边界，是将 runbook 的 loopSize/loopSrcStride 探针映射回实际 API 参数的入口。
- [NDDMA多维dstStride致data搬运偏移的判别](../../../../../runbooks/precision/nddma_dststride_data.md)（`exemplifies`）：DataCopy 与《NDDMA多维dstStride致data搬运偏移的判别》的实质衔接是：该 DataCopy 是 GM→UB NDDMA，多维 shape/stride、NdDmaDci 与非对齐 padding 是直接契约；所选故障卡覆盖漏维、stride=0 和 cache 刷新边界。
- [NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写](../../../../../runbooks/compilation/nddma_nddmaconfig_datacopypad.md)（`exemplifies`）：《DataCopy》给出“多维数据搬运接口，支持自由配置搬入的维度信息及对应的Stride。”；该约束/探针可直接复现、解释或前置验证《NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写》中的“Ascend950/CANN9.1.0 下 NDDMA DataCopy 的非 32B 对齐尾轴须显式设 NdDmaConfig.loopRpSize 右填充(仅 loop0 进硬件指令)且 UB→GM 回写用 DataCopyPad(DataCopyExtParams) 字节粒度；缺 padding 或用 DataCopy(DataCopyParams)(blockLen 以 32B 块为单位)会触发 DYN_COMPILE_FAILURE。”。
- [RANK大于5时NDDMA漏维只解释accum错误](../../../../../runbooks/precision/rank_5_nddma_accum_var.md)（`exemplifies`）：NDDMA DataCopy 暴露多维 loopSize 与 stride 描述符，本卡的核心约束是描述符只覆盖至多五维，额外维度必须由外循环补齐。
- [DataCopy](data_copy_gm_to_ub_nd2_nz.md)（`related`）：NDDMA 处理任意多维 stride 搬入，而 ND2NZ 接口同时完成格式转换；应按目标布局是否为 NZ 选择。
- [数据搬运](data_move.md)（`related`）：DataCopy 与《数据搬运》的实质衔接是：该 DataCopy 是 GM→UB NDDMA，多维 shape/stride、NdDmaDci 与非对齐 padding 是直接契约；所选故障卡覆盖漏维、stride=0 和 cache 刷新边界。
- [数据搬运概念（概述）](../../data_move_guide/overview/data_move_concept.md)（`related`）：概述将 NDDMA 定位为多维自由 stride 搬运，适合超出普通高维切分表达能力的场景。
- [DataCopyPad](data_copy_pad_ub_to_gm.md)（`same_topic`）：DataCopy 与《DataCopyPad》的实质衔接是：该 DataCopy 是 GM→UB NDDMA，多维 shape/stride、NdDmaDci 与非对齐 padding 是直接契约；所选故障卡覆盖漏维、stride=0 和 cache 刷新边界。
- [NdDmaDci](../data_move_aux_config/nd_dma_dci.md)（`same_topic`）：DataCopy 与《NdDmaDci》的实质衔接是：该 DataCopy 是 GM→UB NDDMA，多维 shape/stride、NdDmaDci 与非对齐 padding 是直接契约；所选故障卡覆盖漏维、stride=0 和 cache 刷新边界。
<!-- cannbot:related:end -->
