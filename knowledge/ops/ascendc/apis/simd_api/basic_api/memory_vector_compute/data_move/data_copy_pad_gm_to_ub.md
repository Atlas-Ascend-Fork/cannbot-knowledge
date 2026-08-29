---
type: API
title: DataCopyPad
description: 将数据从GM非对齐搬运至UB，可根据需要自行填充数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_GMToUB.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# DataCopyPad

将数据从GM非对齐搬运至UB，可根据需要自行填充数据。

DataCopyPad（GMToUB非对齐数据搬运）从Global Memory将数据非对齐搬运至Unified Buffer时，可根据开发者的需要自行填充数据。SetPadValue用于设置DataCopyPad需要填充的数值。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN - GM -> VECOUT

本接口组包含 逻辑位置TPosition, SetPadValue, SetPadValue。

本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [507035 C 超 per_buf_elems 致 Phase1 UB 越界](../../../../../runbooks/compilation/datacopypad_phase1_chunk_loop_per_buf_elems_507035.md)（`exemplifies`）：`DataCopyPad` 写 `19686*4 = 78744` 字节到 `50784` 字节 buffer；将数据从GM非对齐搬运至UB。Runbook 的 507035 由 GM→UB DataCopyPad 的 blockLen 超过目标 UB 容量直接触发，API 卡确定搬运方向；修复必须在该契约上按 per_buf_elems 分 chunk。
- [DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零](../../../../../runbooks/precision/datacopy_gm_to_ub_non_32b_aligned_silent_zero.md)（`exemplifies`）：“参考 `layer_norm_v3` 参考实现（CANN 自带），1D GM→UB 用 `DataCopyPad`：”与“DataCopyPad（GMToUB非对齐数据搬运）从Global Memory将数据非对齐搬运至Unified Buffer时，可根据开发者的需要自行填充数据。”分别给出两端正文事实；runbook 以实际非对齐统计全零故障给出 DataCopyPad 修复配方，API 卡则定义 GM→UB 非对齐搬运能力，前者是后者在排障任务中的具体使用实例。
- [DataCopyPad CopyIn 小输入 32B DMA 越界](../../../../../runbooks/compilation/datacopypad_copyin_32b_dma.md)（`exemplifies`）：`DataCopyPad` 的 CopyIn 不论 `DataCopyExtParams.blockLen` 写多少，**底层 DMA 引擎以 32 字节（1 DataBlock）为最小读取粒度**访问 GM。 DataCopyPad（GMToUB非对齐数据搬运）从Global Memory将数据非对齐搬运至Unified Buffer时，可根据开发者的需要自行填充数据。 Runbook 把 GM→UB DataCopyPad 的逻辑非对齐搬运与 32B 物理读取粒度连接起来，决定 Host 实际分配下限。
- [DataCopyPad stride 表示 block 间隙](../../../../../runbooks/precision/datacopypad_stride_is_inter_block_gap.md)（`exemplifies`）：这里的 stride 字段是相邻 block 有效 payload 之间的额外 gap。DataCopyPad 已按硬件块粒度组织 UB 行；再写入 `padRowBytes-rowBytes` 会把对齐差重复计入地址推进。以有效字节数 `L`、对齐后行宽 `P` 为例，正确下一行地址是当前行起点加 `P`；错误配置又加 `(P-L)`，实际推进变成 `P+(P-L)`，因此从第二行开始访问错误位置。；DataCopyPad（GMToUB非对齐数据搬运）从Global Memory将数据非对齐搬运至Unified Buffer时，可根据开发者的需要自行填充数据。SetPadValue用于设置DataCopyPad需要填充的数值。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN - GM -> VECOUT。runbook 的错误正发生在 GM 到 UB 的多行 DataCopyPad 参数上，API 卡限定了该搬运方向和填充语义，便于把 stride 修复放到正确重载。
- [DataCopyPad 加载缺少 Pad 参数导致编译失败](../../../../../runbooks/compilation/datacopypad_gm_to_ub_requires_pad_params.md)（`exemplifies`）：dav-3510 的 GM 到 UB 扩展重载签名要求 `DataCopyPadExtParams<T>`；将数据从GM非对齐搬运至UB，可根据需要自行填充数据。运行手册的四参数修法直接依赖 GM→UB DataCopyPad 的填充参数合同，API 卡给出该方向的通路与填充语义。
- [DataCopyPad 尾块改逐行一维搬入](../../../../../runbooks/precision/datacopypad_partial_2d_blocks_use_per_row_copy.md)（`exemplifies`）：“选择逐行 `blockCount=1`，因为它把每个 GM 行起点和 UB 行起点显式化，可以用一次改动隔离 stride 语义。”；“将数据从GM非对齐搬运至UB，可根据需要自行填充数据。”。Runbook用 DataCopyPad 的 GM→UB 能力实现逐行单 block 搬入，并以显式起点绕开多行 stride 歧义。
- [DataCopyPad 无匹配重载 LocalTensor 实参不一致](../../../../../runbooks/compilation/datacopypad_localtensor.md)（`exemplifies`）：只要在同一个 DMA 调用里出现 `LocalTensor<int8_t>`（字节模式缓冲）与 `LocalTensor<T>` / `GlobalTensor<T>`（typed 队列/输出）混用，即命中本判别；将数据从GM非对齐搬运至UB，可根据需要自行填充数据。运行手册的编译判别要求 GM→UB DataCopyPad 两端保持同一元素模板类型，API 卡标定该方向的 GlobalTensor 到 Unified Buffer 通路。
- [多块 DataCopyPad dst 基址非 32B 对齐崩溃](../../../../../runbooks/compilation/datacopypad_dst_32b.md)（`exemplifies`）：**API 路径**：`AscendC::DataCopyPad(dst LocalTensor, src GlobalTensor, DataCopyExtParams, DataCopyPadExtParams)`，多块搬运（`blockCount>1`，`DataCopyExtParams.blockLen`/`srcStride`/`dstStride` 均以字节为单位）。；DataCopyPad（GMToUB非对齐数据搬运）从Global Memory将数据非对齐搬运至Unified Buffer时，可根据开发者的需要自行填充数据。SetPadValue用于设置DataCopyPad需要填充的数值。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN - GM -> VECOUT；runbook 的多块 dst 基址故障实际调用该 GM 到 UB 非对齐搬运接口，API 卡用于核对方向和能力边界。
- [窄尾 tile 行距错位：补齐 UB gap](../../../../../runbooks/precision/datacopypad_narrow_tile_needs_explicit_ub_row_gap.md)（`exemplifies`）：分别在 GM→UB 的 `dstStride` 与 UB→GM 的 `srcStride` 中补上相同的 UB gap：；DataCopyPad（GMToUB非对齐数据搬运）从Global Memory将数据非对齐搬运至Unified Buffer时，可根据开发者的需要自行填充数据。。Runbook 的修复在 GM→UB 搬入端设置 dstStride，目标 API 卡确认该方向使用带填充的 DataCopyPad，从而定位正确的 copy-in 接口与 UB 行距参数。
- [逐元素 DataCopyPad 做 strided gather 输出全零](../../../../../runbooks/precision/datacopypad_strided_gather.md)（`exemplifies`）：`DataCopyPad` 是 DMA tile-copy API，设计用于在 `GlobalTensor` 与 `LocalTensor` 之间搬运**连续块**。本算子从 `x［..., i, i］` 做 strided gather，每个输出元素对应的 `inputOffset` 是非连续跨步地址。；DataCopyPad（GMToUB非对齐数据搬运）从Global Memory将数据非对齐搬运至Unified Buffer时，可根据开发者的需要自行填充数据。SetPadValue用于设置DataCopyPad需要填充的数值。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN - GM -> VECOUT。runbook 展示把 GM→UB 块搬运误作逐元素随机 gather 会全零，API 卡限定其本职是 GM 到 UB 的非对齐块搬运。
- [SetPadValue](../data_move_aux_config/set_pad_value_isasi.md)（`related`）：设置DataCopyPad非对齐搬运时需要填充的数值，支持GM到UB的填充数据自定义。；DataCopyPad（GMToUB非对齐数据搬运）从Global Memory将数据非对齐搬运至Unified Buffer时，可根据开发者的需要自行填充数据。SetPadValue用于设置DataCopyPad需要填充的数值。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN - GM -> VECOUT。配置卡产生自定义 pad 值，搬运卡在 GM→UB 非对齐 DataCopyPad 中消费该配置。
- [DataCopyPad](data_copy_pad_ub_to_gm.md)（`same_topic`）：DataCopyPad（GMToUB非对齐数据搬运）从Global Memory将数据非对齐搬运至Unified Buffer时，可根据开发者的需要自行填充数据。；该接口提供将数据从Unified Buffer非对齐搬运至Global Memory的功能。。两端记录同一 DataCopyPad 非对齐搬运契约的 GM 到 UB 与 UB 到 GM 两个方向，联合阅读可按数据流方向选择入口并核对填充与丢弃 dummy 数据的差异。
<!-- cannbot:related:end -->
