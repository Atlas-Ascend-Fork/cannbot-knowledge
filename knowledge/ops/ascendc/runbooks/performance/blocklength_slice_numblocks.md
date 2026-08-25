---
type: "Runbook"
title: "blockLength 对齐 slice 致 numBlocks 塌缩单核"
description: "SwiGlu host tiling 把 blockLength 对齐到 slice 边界后，当 totalSlices < coreNum（极端 totalSlices=1）时 numBlocks=min(coreNum,totalSlices/minSlicesPerCore) 塌缩为 1，整 block 串行单核，大 shape case 退化约一个数量级；判别方法：对齐版大 slice case 成对耗时远高于不对齐版即命中。"
tags: ["task.debugging", "topic.tiling", "topic.performance.analysis", "topic.implementation.pipeline"]
status: stable
sources: []
created_at: "2026-08-18T15:58:27Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["a2"]
---

# blockLength 对齐 slice 致 numBlocks 塌缩单核

## 现象

在 Ascend910B3（DAV_2201，a2，CANN 9.2.0）上为 SwiGlu 支持跨 slice 批量路径，把 host tiling 的 `blockLength` 对齐到 `slice` 边界（`blockLength = slicesPerBlock * slice`）。本意是保证每 block 起点落在 slice 边界以便批量路径正确，但引入了隐性退化：对齐版 cann-bench 评测中大 slice case 串行单核、成对耗时远高于不对齐版——case 4（fp16, shape `[8192,16384]`, dim=0）慢约 25×，case 6（bf16）/case 8（fp32）同样退化约一个数量级。

## 适用场景

- **工程形态**：kernel 直调（ops-direct-invoke），host tiling 函数计算 `blockLength`/`numBlocks`/`slicesPerBlock`。
- **API 路径**：host `GetBlockNum()`/tiling 参数 `blockLength`；kernel `GetBlockIdx()` 多核切分。
- **验证平台与 CANN 版本**：实测 Ascend910B3 / DAV_2201（a2），CANN 9.2.0；frontmatter `platforms: [a2]` 严格对应此实测。
- **适用粒度**：`operator_family`——任何 host tiling 把 `blockLength` 对齐到 `slice` 的算子。
- **路线优先级**：`banned`（`blockLength` 无条件对齐到 slice 的策略在 `totalSlices < coreNum` 时 banned）；条件对齐（`totalSlices < coreNum` 时不对齐保持多核，否则对齐支持批量路径）属 `safety_fallback`。
- **不适用/未验证场景**：`totalSlices >= coreNum` 时对齐不会塌缩 numBlocks，不触发本退化。

## 根因

`numBlocks = min(coreNum, totalSlices / minSlicesPerCore)`；`slicesPerBlock = ceil(totalSlices / numBlocks)`；对齐口径下 `blockLength = slicesPerBlock * slice`。当某 case 的 `totalSlices` 很小（case 4 在对齐口径下 `totalOut = slice` → `totalSlices = 1`），`numBlocks` 塌缩到 1，整 block 只分给 1 个核，失去多核并行。不对齐版 v1 用 `numBlocks = min(coreNum, totalOut / MIN_ELEMS_PER_CORE)` 跑满 24 核，故对齐后慢约 25×（24 核 → 1 核）。case 6/8 的 slice 同样等于 totalOut（`totalSlices = 1`），同一机制退化约一个数量级。

机制链：blockLength 对齐 slice → totalSlices < coreNum 的 case 上可用 slice 数不够分给所有核 → numBlocks 塌缩为 1 → 整 block 串行单核 → 大 shape case 退化一个数量级。这不是"算力不够"，而是"对齐口径把多核并行度压没"。

## 判别方法

- **触发（tool_observed）**：host tiling 把 `blockLength` 对齐到 `slice` 边界后，cann-bench 评测中大 slice case（`totalSlices < coreNum`，典型 `totalSlices=1`）成对耗时远高于不对齐版（本 trace case 4 慢约 25×，case 6/8 退化约一个数量级）。
- **探针（executable check）**：跑 cann-bench 评测，比较大 slice case 在"对齐 blockLength"与"不对齐 blockLength"两版下的成对相对耗时：
  ```bash
  cd <cann-bench-root> && bash scripts/run_evaluation.sh \
    --source-dir <source-dir> --operator SwiGlu --device-id 0 2>&1 | \
    grep -E "case_4|case_6|case_8|综合得分"
  ```
  若大 slice case 在对齐版成对远慢于不对齐版（退化一个数量级以上），即命中。判别时须同时核验对齐口径下该 case 的 `totalSlices` 是否 `< coreNum`（host tiling 中打印 `totalSlices`/`numBlocks` 即可定位塌缩）。
- **观测（tool_observed，本 trace 实测 a2）**：对齐版 case 4 退化约 25×、case 6/8 退化约一个数量级，三者均 `totalSlices=1`、`numBlocks` 塌缩为 1 串行单核；不对齐版（v1）同样 case 多核并行、无退化。
- **解释（interpretation）**：多核并行度由 `numBlocks` 决定。`blockLength` 对齐到 slice 看似安全（保证 slice 边界），但在 `totalSlices < coreNum` 的 case 上可用 slice 数不够分给所有核，`numBlocks` 塌缩到 1，整 block 串行单核执行，大 shape case 退化一个数量级。判别要点：若对齐版大 slice case 成对远慢于不对齐版、且 `totalSlices < coreNum` → 即为 numBlocks 塌缩，优化方向是条件对齐（`totalSlices < coreNum` 时不对齐），而非加核或换 API。

## 验证信号

- blockLength 对齐 slice 版 cann-bench 评测：大 slice case（case 4，`totalSlices=1`）串行单核、耗时约 25× 慢于不对齐版 v1 多核路径（参照路线：v1 不对齐 blockLength 多核路径；来源平台:a2；证据等级:tool_observed）。
- 同次评测 case 6（bf16）/case 8（fp32）亦 `totalSlices=1`、`numBlocks` 塌缩为 1，耗时退化约一个数量级（来源平台:a2；证据等级:tool_observed）。

## 失效边界

- 本退化在 a2（910B3 / DAV_2201，24 核）实测；a3、950 平台未在本 trace 实测，**未验证，推断可迁移**（同属多核 `numBlocks` 切分模型，但核数不同，`totalSlices < coreNum` 阈值不同，需重测）。
- `totalSlices >= coreNum` 时对齐不塌缩 `numBlocks`，不触发本退化。
- 修复（条件对齐 `edit`）的 verbatim before/after 在归一化事件流中为占位（adapter 丢失），未从 trace 逐字恢复；判别与根因由对齐/不对齐版前后成对评测耗时对照支撑，修复后信号未独立隔离观测。

<!-- cannbot:related:start -->
## 相关

- [AscGetBlockIdx](../../apis/simd_api/c_api/sys_var/asc_get_block_idx.md)（`exemplifies`）：AscGetBlockIdx 与《blockLength 对齐 slice 致 numBlocks 塌缩单核》的实质衔接是：AscGetBlockIdx 与 block 数 API、系统变量共同定义多核索引；所选故障/性能卡直接用 blockIdx 解释错误切分、串行启动和尾核边界。
- [GetBlockIdx](../../apis/simd_api/basic_api/tool_interface/system_resources_and_variables/get_block_idx.md)（`exemplifies`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《blockLength 对齐 slice 致 numBlocks 塌缩单核》明确提供“SwiGlu host tiling 把 blockLength 对齐到 slice 边界后，当 totalSlices < coreNum（极端 totalSlices=1）时 numBlocks=min(coreNum,totalSlices/minSlicesPerCore) 塌缩为 1，整 block 串行单核，大 shape case 退化约一个数量级；判别方法：对齐版大 slice case 成对耗时远高于不对齐版即命中。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [NumBlocks](../../apis/simt_api/cooperative_groups/grid_group/num_blocks.md)（`exemplifies`）：blockLength 对齐 slice 致 numBlocks 塌缩单核说明SwiGlu host tiling 把 blockLength 对齐到 slice 边界后，当 totalSlices < coreNum（极端 totalSlices=1）时 numBlocks=min(coreNum,totalSlices/minSlicesPerCore) 塌缩为 1，整 block 串行单核，大 shape case 退化约一个数量级；判别方法：对齐版大 slice case 成对耗时远高于不对齐版即命中。
- [SIMD算子实现主块均分](../../guides/operator_practice/simd_operator_impl/vector_programming/multi_core_tiling/main_block_even_split.md)（`related`）：《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。；《blockLength 对齐 slice 致 numBlocks 塌缩单核》说明SwiGlu host tiling 把 blockLength 对齐到 slice 边界后，当 totalSlices < coreNum（极端 totalSlices=1）时 numBlocks=min(coreNum,totalSlices/minSlicesPerCore) 塌缩为 1，整 block 串行单核，大 shape case 退化约一个数量级；判别方法：对齐版大 slice case 成对耗时远高于不对齐版即命中。。二者在主块均分与三种尾块策略共同覆盖多核切分分支；Kernel用GetBlockIdx定位GM段，numBlocks塌缩故障验证Host切核结果上存在可执行的直接衔接。
- [跨 slice 批量 vector 源地址非 32B 对齐触发 507035](../compilation/slice_vector_32b_507035.md)（`related`）：性能卡说明按 slice 对齐 blockLength 会让小 slice 工作量塌缩到单核；本卡又禁止未对齐跨 slice 批量。
- [高级编程基本流程](../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/host_tiling_implementation.md)（`related`）：高级编程基本流程 与《blockLength 对齐 slice 致 numBlocks 塌缩单核》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [SwiGLU 高级 API 在非32B对齐 slice 上精度失败](../precision/swiglu_adv_api_fails_non_32b_aligned_slice.md)（`same_topic`）：《SwiGLU 高级 API 在非32B对齐 slice 上精度失败》明确“AscendC::SwiGLU 高级 API（adv_api/activation/swiglu.h）在 dav-2201 上对 slice*sizeof(T) 非 32B 整数倍的 case 产生大错值（fp32 slice=509 MARE≈2.5e9；fp16 全零 slice=506 MARE=93/65504），对齐 slice 正常。banned：非对齐 slice 不得用此 API，回退手写 SiLU 链。”；它与《blockLength 对齐 slice 致 numBlocks 塌缩单核》的“SwiGlu host tiling 把 blockLength 对齐到 slice 边界后，当 totalSlices < coreNum（极端 totalSlices=1）时 numBlocks=min(coreNum,totalSlices/minSlicesPerCore) 塌缩为 1，整 block 串行单核，大 shape case 退化约一个数量级；判别方法：对齐版大 slice case 成对耗时远高于不对齐版即命中。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
