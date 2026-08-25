---
type: "Runbook"
title: "NDDMA 最内层 srcStride=0 广播读越界"
description: "NDDMA 搬运需广播的输入时，若最内层（nd=0）srcStride=0，硬件按 stride=1 连读越界而非广播；用 loopSrcStride[0]==0 断言 + mask shape [1]→[N] 对照实验判别，修复方向为 loopSize[0]=1 循环填充。"
tags: ["task.debugging", "topic.precision", "topic.data_movement.data_copy", "topic.implementation"]
status: stable
sources: []
created_at: "2026-08-18T15:11:41Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# NDDMA 最内层 srcStride=0 广播读越界

## 现象

Ascend950 `masked_fill` 算子 Broadcast 路线（mask_predicate 范式，Regbase 实现）ST Real 运行 `bash run.sh` 后，多个 L0 用例部分元素不匹配，且全部集中在 mask 需要广播的场景：标量 `mask=[1]` 广播到 `[N]` 时 7/8 不匹配（唯一通过位置对应 `gmMask[0]`）；`mask=[449,1,1]` 广播时 224/512 不匹配。穿刺场景 `mask=[1,3]`（最内层有非零 stride）不受影响而通过。

## 适用场景

- **工程形态**：kernel 直调（Regbase + mask_predicate 范式，ops-registry-invoke 流程），Broadcast 路线（TilingKey=2 RANK≤4 / TilingKey=3 RANK>4）。
- **API 路径**：`DataCopy<uint8_t, ND, cfg>` + `MultiCopyParams<uint8_t, ND>`（NDDMA 多维搬运含随路广播），`CopyInBrc` 搬运 mask（uint8_t 类型）。
- **验证过的平台与 CANN 版本**：Ascend950（`--soc=ascend950`），CANN 9.1.0（cann-9.1.0）。
- **适用粒度**：`operator_family`（适用于所有走 NDDMA 广播搬运的 AscendC 算子，不限于 masked_fill）。
- **路线优先级**：`recommended_fastpath`（NDDMA 广播搬运本身是 Broadcast 路线的快路径，只需识别最内层 srcStride=0 的特例）。
- **不适用或未验证场景**：EleWise 路线（mask shape == x shape，无广播）不走 NDDMA 广播；穿刺场景（mask=[1,3] 等最内层有非零 stride）天然不触发；a2/a3 平台未验证（见 `## 失效边界`）。

## 判别方法

**触发**：走 NDDMA 搬运 mask（或任何需广播的输入）的 Broadcast 路线 kernel，ST Real 运行后 mask 需要广播的用例出现「部分元素不匹配 + 唯一正确位置恰为 `gmMask[0]` 对应索引」。不要把「全部不匹配」当唯一现象——当 `gmMask[0]` 之后的相邻内存恰好是合法数据（如 `mask=[449,1,1]` 有 449 个真实元素）时，表现为「读错位置」而非「越界垃圾」，失败计数可能不是 7/8 而是任意比例。

**可执行探针（按序）**：

1. **检查最内层 srcStride**：打印或断言 `nddmaParams_[IN_MASK].loopInfo.loopSrcStride[0]`，若为 0 即命中本 bug。最内层 NDDMA 维度（`nd=0`，对应 `loopSrcStride[0]`）不能为 0。
2. **ST 失败模式对照**：mask 需要广播的 case 出现「部分元素不匹配 + 唯一正确位置恰为 `gmMask[0]` 对应索引」即典型信号。标量 `mask=[1]` 时 1 个正确 + (N-1) 个垃圾；多维广播时按最内层 `loopSize[0]` 个一组重复该模式。
3. **对照实验**：把 mask shape 从 `[1]` 改为 `[N]`（消除最内层广播，srcStride 变非零），若同一 case 通过，则确认是 NDDMA 广播失效而非 kernel 逻辑错。穿刺场景 `mask=[1,3]`（最内层 srcStride=1，广播在外层 nd=1）天然构成这一对照——它通过即旁证「最内层 srcStride=0」才是触发条件。

**原始观测（tool_observed）**：

- `mask=[1]` 标量广播到 `[N]`：所有维度 stride=0，NDDMA mask 参数 `loopSize=[8,1,1,1], srcStride=[0,0,0,0]`，最内层 `nd=0` 的 `loopSize=8, srcStride=0`。ST 报 7/8 不匹配，唯一通过位置对应 `gmMask[0]`。
- `mask=[449,1,1]` 广播：最内层 `srcStride=0, loopSize=79`，ST 报 224/512 不匹配。
- 穿刺 `mask=[1,3]`：最内层 `nd=0` 的 `srcStride=1`（连续读 3 个真实元素），广播在外层 `nd=1`（`srcStride=0`），ST 通过——外层 srcStride=0 被正确处理。

**解释**：NDDMA DataCopy 的最内层维度（`nd=0`）不支持 `srcStride=0`。当 mask 的最内层维度需要广播（shape=1 → stride=0）时，`loopSrcStride[0]=0`，NDDMA 硬件不会按 stride=0 重复读取同一元素实现广播，而是按 stride=1 连续读取 GM，读到 `gmMask[1..loopSize-1]`（标量 mask 时为越界相邻内存；多维 mask 时为读错位置）。结果 UB 中 mask 数据 1 个正确 + 其余错位 → Select 选错 → 部分不匹配。外层维度的 srcStride=0 不受此限制（穿刺场景外层广播正常）。修复方向（解释层，非 verbatim）：检测 `loopSrcStride[0]==0` 时将 `loopSize[0]` 设为 1，循环多次 `DataCopy` 填充广播数据；完整函数体未在 trace 恢复。

## 验证信号

- ST Real 修复前 mask 广播用例部分不匹配：`mask=[1]` 标量 7/8 不匹配（唯一正确位置对应 `gmMask[0]`），`mask=[449,1,1]` 224/512 不匹配（来源平台:950；证据等级:tool_observed）
- ST Real 修复前通过率 342/604，修复后提升至 560/604（来源平台:950；证据等级:tool_observed）
- 穿刺场景 `mask=[1,3]`（最内层 srcStride=1，广播在外层）不触发本 bug，ST 通过（来源平台:950；证据等级:tool_observed）

## 失效边界

- **未验证，推断可迁移**：a2（包括已确认映射的 Ascend910B3）与 a3 平台的 NDDMA 行为推断一致（同属 AscendC 通用 DMA 语义），但未在本 trace 实测，不得写入 `platforms`。
- **不适用**：EleWise 路线（mask shape==x shape，无 NDDMA 广播）；mask 最内层有非零 stride 的穿刺场景。
- **边界**：当 mask 所有维度都需要广播（纯标量 mask `[1]`）且 `actualRank>5` 时，还需配合 `nddmaOuterIters_` 外层循环计数修复，二者独立但常同时触发。
- NDDMA「不支持最内层 srcStride=0」是硬件/微码限制还是 API 文档未明确的约束，未在 ascendc-api-best-practices 文档中找到明确说明。

## 误诊

- 早期误以为是 `CopyInBrc` 中 `loopDstStride` 计算与 `Init` 不一致导致——逐行对比后两者一致，排除。
- 早期怀疑 mask 数据搬运全错（连续读取 mask 数据而非广播），但 `L0_010`（mask=[449,1,1]）mask 有 449 个真实元素，`gmMask[0..78]` 是合法 mask 数据而非越界，只是「读错位置」而非「越界」——这反而印证了「硬件按 stride=1 读」的判断。

## 预防

- 写 NDDMA 广播搬运前，先确认 mask（或任何需广播的输入）的最内层 NDDMA 维度 `srcStride` 不为 0；若为 0，先重排维度或走「loopSize=1 + 多次调用」填充模式。
- 参考 adam kernel.h 的 NDDMA 参数计算逻辑，确认其对广播维度排布的处理。

<!-- cannbot:related:start -->
## 相关

- [DataCopy](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_gm_to_ub_nddma.md)（`exemplifies`）：官方 DataCopy 多维搬运接口定义 MultiCopyParams/Stride 的调用边界，是将 runbook 的 loopSize/loopSrcStride 探针映射回实际 API 参数的入口。
- [GetStride](../../apis/simd_api/basic_api/aux_data_structures/layout/get_stride.md)（`exemplifies`）：GetStride 与《NDDMA 最内层 srcStride=0 广播读越界》的实质衔接是：GetStride 从 Layout 读取 MakeStride 生成的维度步长，Crd2Idx 以该 stride 映射坐标；NDDMA stride=0 故障和 Layout 说明验证物理寻址边界。
- [GmUbDataMove](../../apis/simd_api/basic_api/data_move_guide/gm_ub_data_move.md)（`exemplifies`）：GmUbDataMove 与《NDDMA 最内层 srcStride=0 广播读越界》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [NDDMA 快速路径 C=1 中间轴漏维判别](nddma_c_1.md)（`related`）：C=1 卡说明把广播维误判为末轴会构造错误的最内层 NDDMA stride；它是本卡 loopSrcStride[0] 检查在真实高维快路径中的上游参数生成案例。
- [NDDMA多维dstStride致data搬运偏移的判别](nddma_dststride_data.md)（`related`）：两卡分别定位 NDDMA 最内层 srcStride=0 被当连续读和多维 dstStride 被错误应用；对照源/目的步长探针可快速区分广播读错与 UB 写偏移。
- [NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写](../compilation/nddma_nddmaconfig_datacopypad.md)（`related`）：srcStride 修正只能保证取数位置，非 32B 尾轴还需 loopRpSize 和字节粒度 DataCopyPad 回写；该卡补齐 NDDMA 广播修复后的对齐/搬出约束。
- [RANK大于5时NDDMA漏维只解释accum错误](rank_5_nddma_accum_var.md)（`related`）：当 RANK>5 时描述符只能覆盖部分维度，需外层循环补齐；该卡补充本 focal 在纯标量广播且 actualRank>5 时明确提到的独立漏维边界。
- [广播 CopyIn tile 跨段越界读判别](copyin_tile.md)（`related`）：目标卡证明广播维的 stride=0 不能直接当作 NDDMA 源广播，本卡证明 1D DataCopyPad 也不能从段内偏移连续读取广播源；二者共同要求显式按广播段循环/填充。
- [DataCopyPad stride 表示 block 间隙](datacopypad_stride_is_inter_block_gap.md)（`same_topic`）：DataCopyPad stride 表示 block 间隙 与《NDDMA 最内层 srcStride=0 广播读越界》的实质衔接是：这些卡都直接解释 DataCopyPad 的 stride 是有效 block 后的 gap，并覆盖32B单位、窄尾padding、逐行复制、非连续子块、NDDMA stride及官方GM→L1参数契约。
<!-- cannbot:related:end -->
