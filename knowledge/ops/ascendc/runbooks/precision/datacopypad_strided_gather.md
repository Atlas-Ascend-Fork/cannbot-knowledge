---
type: "Runbook"
title: "逐元素 DataCopyPad 做 strided gather 输出全零"
description: "把 DataCopyPad 降格为逐元素 strided gather（对 LocalTensor 切片 inTile[i] 以 ext{1,sizeof(T)} 搬单个 GM 元素）再 DataCopyPad(yGm, inTile) 写出，编译过无报错但输出全零；根因是 1-元素 DataCopyPad 未把 GM 值有效填入后续写出路径读取的那片 UB。判别方法：编译过+输出全 0 且 gather 循环出现 LocalTensor 切片+ext{1,sizeof(T)} 的 1-元素 DataCopyPad 即命中；元素级 GM 读写应改用 GlobalTensor.GetValue/SetValue。"
tags: ["task.debugging", "topic.precision", "topic.data_movement.data_copy", "topic.compute.indexing"]
status: stable
sources: []
created_at: "2026-08-18T08:54:47Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# 逐元素 DataCopyPad 做 strided gather 输出全零

## 现象

在 Ascend950（dav-3510 / arch35，CANN 9.1.0-beta.1）上对 `matrix_diag_part` 直调工程做精度验证。kernel 用 `TQue`+`AllocTensor`+逐元素 `DataCopyPad` 做 strided gather：对每个输出元素算出非连续跨步地址 `inputOffset = batchIdx*matrixSize + diagIdx*(N+1)`，取 `LocalTensor<T> elem = inTile[i]` 切片，以 `DataCopyExtParams ext{1, (uint32_t)sizeof(T), 0, 0, 0}`（blockCount=1、blockLen=单元素字节）调用 `DataCopyPad(elem, xGm_[inputOffset], ext, pad)` 搬一个 GM 元素，循环末尾再 `DataCopyPad(yGm_[outStart], inTile, outExt)` 把整片 UB 写回 GM。`make -j` 编译通过（`[100%] Built target`）、kernel 能 launch、`aclrtSynchronizeStream` 返回，无任何报错，但 8 个测试用例中 cases 0-4 全 `mismatch`：

```
x: [[ 0.  1.  2.  3.  4.  5.]
 [ 6.  7.  8.  9. 10. 11.]
 [12. 13. 14. 15. 16. 17.]
 [18. 19. 20. 21. 22. 23.]]
golden: [ 0.  7. 14. 21.]
output: [0. 0. 0. 0.]
```

case 0 为 `3/4 mismatch`、case 2 为 `7/8 mismatch`、case 3 为 `127/128 mismatch`；case 5 是空 tensor（ySize=0，无输出文件）；case 7（`[16,32,48]` 大批量）因逐元素 `DataCopyPad` 效率过低触发 `shell tool terminated command after exceeding timeout 120000 ms`。形态符合 `output_all_zero`：编译过 + 输出全 0 + 无报错。

## 适用场景

- **工程形态**：kernel 直调（`ops-direct-invoke`，`__global__ __aicore__` kernel + `<<<>>>` 启动）。
- **API 路径**：`AscendC::DataCopyPad`（`DataCopyExtParams` / `DataCopyPadExtParams`）、`GlobalTensor.GetValue/SetValue`、`LocalTensor` 切片、`TQue.AllocTensor`。
- **验证平台与 CANN 版本**：Ascend950（dav-3510 / arch35），CANN 9.1.0-beta.1；与 frontmatter `platforms: [950]` 严格一致。
- **适用粒度**：`operator_family`——任何 strided gather / 非连续地址元素搬运的 kernel，若误用逐元素 `DataCopyPad` 都会命中此现象。
- **路线优先级**：`recommended_fastpath`——元素级 strided GM 访问应走 `GetValue/SetValue`；`TQue`+`DataCopyPad` 仅留作类型推导触发。
- **不适用/未验证场景**：连续、对齐的大段 GM↔UB 搬运仍应使用 `DataCopyPad`（其设计用途）；a2/a3 未实测（见 `## 失效边界`）。

## 根因

`DataCopyPad` 是 DMA tile-copy API，设计用于在 `GlobalTensor` 与 `LocalTensor` 之间搬运**连续块**。本算子从 `x[..., i, i]` 做 strided gather，每个输出元素对应的 `inputOffset` 是非连续跨步地址。把 `DataCopyPad` 降格为"逐元素搬一个 `sizeof(T)` 字节"——对 `LocalTensor<T> elem = inTile[i]` 这种 `LocalTensor` 切片以 `ext{1, sizeof(T), ...}` 调 1-元素 `DataCopyPad`——后：

1. 该 1-元素 `DataCopyPad` 并未把 `xGm_[inputOffset]` 的值真正写入 `inTile` 后续 `DataCopyPad(yGm_[outStart], inTile, outExt)` 读出的那片 UB；实测写出全零，说明 `inTile` 内容未被该逐元素 `DataCopyPad` 链有效填充。循环中 `inTile.SetValue(i, inTile.GetValue(i))` 是自拷贝 no-op，无法补救。
2. 随后 `DataCopyPad(yGm_[outStart], inTile, outExt)` 把这片未初始化/零的 UB 搬到 GM，输出全零。

机制链：逐元素 `DataCopyPad` strided gather（1-元素 blockLen + `LocalTensor` 切片 dst）→ GM 值未有效落入写出路径读取的 UB → 写回 GM 全零。这不是"算式错"或"对齐越界"，而是"块搬运 DMA 被误用为元素级标量 gather"的语义不匹配。元素级 GM 读写应使用 `GlobalTensor.GetValue(offset)` / `GlobalTensor.SetValue(idx, val)`。

## 判别方法

- **触发（tool_observed）**：strided/非连续 gather 类直调 kernel `make -j` 编译通过、能 launch、`aclrtSynchronizeStream` 正常返回、无报错，但运行输出全零（如 `output: [0. 0. 0. 0.]` vs `golden: [0. 7. 14. 21.]`），且大 shape case 出现 120s 超时。
- **探针（executable check）**：审查 kernel 的 gather 循环，命中以下全部特征即为本判别：
  1. dst 是 `LocalTensor` 切片而非整片 buffer：`LocalTensor<T> elem = inTile[i];`；
  2. `DataCopyExtParams` 的 `blockLen` 取 `sizeof(T)`（1-元素搬运）：`DataCopyExtParams ext{1, (uint32_t)sizeof(T), 0, 0, 0};`；
  3. 源地址是跨步/非连续 GM 偏移：`DataCopyPad(elem, xGm_[inputOffset], ext, pad)`，`inputOffset` 随 `batchIdx/diagIdx` 跨步变化；
  4. 末尾用一次整片 `DataCopyPad(yGm_[outStart], inTile, outExt)` 把 UB 写回 GM。
  判别时须同时核验"编译过 + 输出全 0"与上述 1-元素 `DataCopyPad` gather 代码模式同时出现；连续对齐块搬运（`blockLen`=多元素、整片 dst）不触发。可选确认：把 gather 循环改为 `T val = xGm_.GetValue(inputOffset); yGm_.SetValue(idx, val);` 后重跑——输出由全零转为匹配 golden 即锁定根因（该 after 信号，未作为独立条目入 `## 验证信号`）。
- **观测（tool_observed，本 trace 实测 950）**：case 0 `output: [0. 0. 0. 0.]` vs `golden: [0. 7. 14. 21.]`、`Case 0: FAIL (3/4 mismatch)`，cases 0-4 全 mismatch（case 0 `3/4`、case 2 `7/8`、case 3 `127/128`）；case 7（`[16,32,48]`）逐元素 `DataCopyPad` 效率过低触发 `shell tool terminated command after exceeding timeout 120000 ms`。kernel 编译 `[100%] Built target`、无报错。
- **解释（interpretation）**：`DataCopyPad` 是 GM↔UB 的块搬运 DMA，语义要求连续对齐块；以 1-元素 `blockLen` + `LocalTensor` 切片 dst 做元素级 strided gather 时，该逐元素 `DataCopyPad` 未把 GM 值有效填入后续写回路径读取的 UB（是切片视图语义还是 1-元素 `blockLen` 的最小搬运粒度/对齐要求所致，本 trace 未做 UB dump 探针，仅由输出全零反推），写回 GM 即全零。判别要点是"编译过 + 输出全 0 + gather 循环为 1-元素 `DataCopyPad` on `LocalTensor` 切片"三特征同时成立——它把"算式/数值错"与"搬运语义错"区分开：算式无误而搬运未落值。修复方向是 gather 用 `GlobalTensor.GetValue/SetValue` 元素级读写；`TQue`+`DataCopyPad` 若为 bisheng auto-derivate 类型推导所需，应放在不参与输出的 dummy 搬运上。

## 验证信号

本卡验证来自 2026-08-11 在 Ascend950（dav-3510）+ CANN 9.1.0-beta.1 上 `matrix_diag_part` 直调工程的开发会话；以下均为该会话 tool_observed 实测。

- 修复前（逐元素 `DataCopyPad` strided gather）：case 0 `output: [0. 0. 0. 0.]` vs `golden: [0. 7. 14. 21.]`、`Case 0: FAIL (3/4 mismatch)`，cases 0-4 全 mismatch（case 2 `7/8`、case 3 `127/128`）（来源平台：950；证据等级：tool_observed）。
- 修复前副作用：case 7（`[16,32,48]` 大批量）逐元素 `DataCopyPad` 效率过低触发 `shell tool terminated command after exceeding timeout 120000 ms`（来源平台：950；证据等级：tool_observed）。
- kernel `make -j` 编译 `[100%] Built target`、能 launch、`aclrtSynchronizeStream` 返回、无报错，形态为编译过 + 输出全 0（来源平台：950；证据等级：tool_observed）。

## 失效边界

- 本判别与根因在 950（dav-3510 / arch35，CANN 9.1.0-beta.1）实测；a2/a3 未在本 trace 实测，**未验证，推断可迁移**（`GetValue/SetValue` 与 `DataCopyPad` 的语义是 Ascend C API 行为，推断跨架构一致，但需重测确认）。
- 连续、对齐的大段 GM↔UB 搬运不适用本卡结论——其设计用途就是 `DataCopyPad`；本卡仅针对"把 `DataCopyPad` 降格成逐元素 strided gather"这一误用。
- 逐元素 `DataCopyPad` 未有效填 UB 的机制级根因（切片视图语义 vs 1-元素 `blockLen` 的最小搬运粒度/对齐要求）本 trace 未做 UB dump 探针，仅由输出全零反推；`DataCopyPad` 对 1-元素 `blockLen` 的最小搬运粒度/对齐要求未在 trace 中查证。

## 坏实践

- 用 `DataCopyPad` 搬单个 `sizeof(T)` 字节做元素级 gather（`ext{1, sizeof(T), ...}` + `LocalTensor` 切片 dst）—— DMA 语义不匹配，输出全零且效率极低（case 7 超时）。
- 用 `inTile.SetValue(i, inTile.GetValue(i))` 自拷贝 no-op 来"补救"`DataCopyPad` 未填的 UB——无效。
- 看到"编译过、能 launch、stream 同步返回"就排除搬运路径问题——本故障恰好是无报错静默全零。

## 误诊

- 失败形态是"全零"而非"部分值错"，故与算式/数值逻辑错无关；判别要点是 gather 路径的 1-元素 `DataCopyPad` 模式，不是对角线索引公式。
- case 7 超时易被误判为"评测 harness 问题"，实为逐元素 `DataCopyPad` 路线对大 shape 的效率崩溃，是该误用的次生信号。

## 预防

- 区分"块搬运"与"元素级访问"：strided/非连续/标量 gather 用 `GlobalTensor.GetValue/SetValue`；连续对齐块搬运才用 `DataCopyPad`。
- 若 kernel 因 bisheng auto-derivate 必须保留 `DataCopyPad`，把它放在一个**不参与输出**的 dummy 搬运上，compute 逻辑用正确的 `GetValue/SetValue`，避免"为类型推导而写的 `DataCopyPad` 误混入实际数据通路"。
- 回归须覆盖非连续跨步地址的 gather case 与大 shape case，前者抓全零、后者抓超时。

<!-- cannbot:related:start -->
## 相关

- [DataCopyPad](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_pad_gm_to_ub.md)（`exemplifies`）：`DataCopyPad` 是 DMA tile-copy API，设计用于在 `GlobalTensor` 与 `LocalTensor` 之间搬运**连续块**。本算子从 `x［..., i, i］` 做 strided gather，每个输出元素对应的 `inputOffset` 是非连续跨步地址。；DataCopyPad（GMToUB非对齐数据搬运）从Global Memory将数据非对齐搬运至Unified Buffer时，可根据开发者的需要自行填充数据。SetPadValue用于设置DataCopyPad需要填充的数值。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN - GM -> VECOUT。runbook 展示把 GM→UB 块搬运误作逐元素随机 gather 会全零，API 卡限定其本职是 GM 到 UB 的非对齐块搬运。
- [DataCopyPad](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_pad_ub_to_gm.md)（`exemplifies`）：机制链：逐元素 `DataCopyPad` strided gather（1-元素 blockLen + `LocalTensor` 切片 dst）→ GM 值未有效落入写出路径读取的 UB → 写回 GM 全零。这不是"算式错"或"对齐越界"，而是"块搬运 DMA 被误用为元素级标量 gather"的语义不匹配。元素级 GM 读写应使用 `GlobalTensor.GetValue(offset)` / `GlobalTensor.SetValue(idx, val)`。；该接口提供将数据从Unified Buffer非对齐搬运至Global Memory的功能。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Unified Buffer -> Global Memory - VECIN -> GM - VECOUT -> GM - 如图1所示，对于32字节对齐搬运场景，从Unified Buffer读取的所有数据都会搬运至Global Memory。 - 如图2所示，对于非32字节对齐的场景，在读取Unified Buffer数据时会填入dummy假数据，对齐到32B，搬入Global Memory时会将dummy空数据丢弃，从而实现Unified Buffer到Global Memory的非对齐搬运。。runbook 的全零信号在错误 GM→UB gather 后由 UB→GM 整片写回暴露，API 卡明确该后半段只是块写回，不能补救前半段未落入 UB 的元素。
- [Gather 非 dim 维缩小时折叠步长错位](gather_non_axis_shape_shrink_requires_per_axis_source_strides.md)（`related`）：“- API 路径：host 传入 `x.stride(j)` 与 `index.size(j)`，device 侧按输出坐标 odometer 计算随机 GM 源地址，再用 `DataCopyPad` 搬运；”与“在 Ascend950（dav-3510 / arch35，CANN 9.1.0-beta.1）上对 `matrix_diag_part` 直调工程做精度验证。kernel 用 `TQue`+`AllocTensor`+逐元素 `DataCopyPad` 做 strided gather：对每个输出元素算出非连续跨步地址 `inputOffset = batchIdx*matrixSize + diagIdx*(N+1)`，取 `LocalTensor<T> elem = inTile［i］` 切片，以 `DataCopyExtParams ext{1, (uint32_t)sizeof(T), 0, 0, 0}`（blockCount=1、blockLen=单元素字节）调用 `DataCopyPad(elem, xGm_［inputOffset］, ext, pad)` 搬一个 GM 元素，循环末尾再 `DataCopyPad(yGm_［outStart］, inTile, outExt)` 把整片 UB 写回 GM。`make -j` 编译通过（`［100%］ Built target`）、kernel 能 launch、`aclrtSynchronizeStream` 返回，无任何报错，但 8 个测试用例中 cases 0-4 全 `mismatch`：”。focal 用逐维 stride 和逐元素 DataCopyPad 验证寻址，另一 Runbook 说明该搬运可全零或超时。
<!-- cannbot:related:end -->
