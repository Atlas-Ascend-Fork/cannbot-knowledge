---
type: Runbook
title: DataCopyParams blockLen 单位是 32B 块
description: "行宽按块数而非元素数计；把 f32 行写成 4 块只落了半行，后 32 列恒零且跨重复调用自固化，看起来像“存储只写了一半”。"
tags: [task.debugging, task.migration, topic.precision, topic.alignment, topic.data_movement.data_copy]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMAndUB_highdim_split.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/impl/basic_api/dav_m200/kernel_operator_data_copy_impl.h
    role: implementation
created_at: "2026-10-28T09:51:47Z"
updated_at: "2026-10-28T09:51:47Z"
platforms: ["310p"]
---

# DataCopyParams blockLen 单位是 32B 块

## 现象

UB→GM 的逐行存储（每行一个连续 burst）在迁移后被"修正"了一次行宽：原参数 `DataCopyParams(8, 1, 0, 0)` 被改成 `DataCopyParams(4, 1, 0, 0)`，理由是"每行只有 64 个元素、一个元素算一块"。改完的失败形状非常规整：

- 输出**每行的后 32 列恰好为零**，前 32 列是正确值；
- 这个"半行零"在连续多次调用之间**完全稳定**——不会自愈、也不会随机漂移（每次调用都只写同样的前半行，后半行保持缓冲旧值）。

这种"列区间整齐缺失 + 跨调用固化"的形状很容易被读成"计算只算了半列 / Vector 掩码少了一半"，从而把排查引向计算侧。

## 适用场景

- **工程形态**：kernel 直调；UB↔GM（以及同族 GM↔UB）的 `DataCopy` + `DataCopyParams(blockCount, blockLen, srcStride, dstStride)`。
- **API 路径**：`AscendC::DataCopy` / `DataCopyParams`；CANN 9.1 的 `impl/basic_api/**/kernel_operator_data_copy_impl.h`（按 310P 的 arch 目录取用）。
- **验证过的平台与 CANN 版本**：Ascend310P3（DAV_2002 / m200）+ CANN 9.1.0。
- **适用粒度**：`platform_wide` —— 凡是走该 impl 的拷贝，`blockLen` 都以 32 字节块计。
- **路线优先级**：`recommended_fastpath`（按 dtype 字节数换算块数，是唯一正解；不存在"用元素数也行"的容错路径）。
- **不适用/未验证**：L0C→UB 的 `BLOCK_MODE_MATRIX` 模式下单位不同（该模式下有"blockLen 单位按更宽粒度"的另一条陷阱记录，本卡不覆盖）；其它代际的 impl 未验证。

## 根因

`DataCopyParams.blockLen` 的语义是**32 字节块的数量**，不是元素数量。CANN 9.1 的 DataCopy impl 里相邻 burst 的偏移就是这么算的：

```cpp
offsetSrc = offsetSrc + i * (intriParams.blockLen * ONE_BLK_SIZE + intriParams.srcStride);
offsetDst = offsetDst + i * (intriParams.blockLen * ONE_BLK_SIZE + intriParams.dstStride);
```

（`ONE_BLK_SIZE = 32`）

因此：

- 一行 64 个 f32 = 256 B = **8 块** → `blockLen=8`；
- 一行 64 个 f16 = 128 B = **4 块** → `blockLen=4`。

误改的版本把 f32 行写成 `blockLen=4`（=128 B），每行只搬了前 32 个 f32，后 32 列保留 UB/GM 里的旧内容（多数情况下是零）。本例 `blockCount=1`，两个 stride 字段不参与寻址，每行调用各自以本行基址为目标，所以唯一后果就是**每行少写后半行**；"跨调用稳定"也只是因为每次调用都同样少写，而不是越界污染或行间错位。判决依据是 impl 的字节语义 + "缺失区恰为 32B 整数倍"两条，不要把"固定错值"解释成越界写。

**同一个数字在不同 dtype 下不通用**：源算子（910B 侧）里也有 `(8, 1, 0, 0)`，但那是一行 128 个 f16 = 256 B。字节数巧合相同，元素数完全不同 —— 这是本卡最容易被误迁移的一点。

## 判别方法

1. 先确定**每行字节数**：`cols × sizeof(dtype)`。
2. 换算块数：`blockLen = 每行字节数 / 32`。不是整数就说明行本身没对齐，先解决对齐。
3. 用 impl 源码验一遍单位（一次 grep 即可），不要凭"元素数"直觉：

```bash
grep -rn "blockLen \* ONE_BLK_SIZE" \
  /usr/local/Ascend/cann-9.1.0/aarch64-linux/asc/impl/basic_api/
grep -rn "ONE_BLK_SIZE =" /usr/local/Ascend/cann-9.1.0/aarch64-linux/asc/include/
```

4. 用"缺失列的边界是否落在 32 列/8 元素这类整块边界上"反向确认：若缺失区间正好是 32B 的整数倍，几乎一定是块数换算问题，而不是掩码或计算问题。

## 设计决策

- 按"字节数 / 32"换算 `blockLen`，并把本行 dtype 与字节数写进代码注释：这是唯一与 impl 语义一致的表达，避免跨 dtype 抄同一个数字。
- 不在调用点保留"元素数"兼容分支：该 impl 不支持以元素为单位，写兼容分支只会制造新的静默半行。

## 系统信息

- 目标平台：Ascend310P3（DAV_2002 / m200），CANN 9.1.0。
- 形态：kernel 直调，UB↔GM 逐行 `DataCopy`；host 侧为 torch C++ 扩展。

## 完整代码

误改版本（每个 burst 只搬半行）：

```cpp
            for (int32_t r = 0; r < lenQEff; ++r) {  // 逐行 MTE3
                // 行宽恒为 T64 半精度 = 128B = 4 块。旧值 (8,1,0,0)=256B 是
                // 源算子 D=128 的行宽: ND=1 时每行多写 128B……
                DataCopy(gmOut[(static_cast<int64_t>(qRow + r) * H + h) * D +
                               dv * T64],
                         t2[r * T64], DataCopyParams(4, 1, 0, 0));
            }
```

正确版本（按 f32 行宽换算回来，并把"字节 vs 元素"写进注释）：

```cpp
            for (int32_t r = 0; r < lenQEff; ++r) {  // 逐行 MTE3
                // 行宽 = T64 个 fp32 = 256B = 8 块（gmOut/t2 均为 f32）。
                // 注意: 与源算子的 (8,1,0,0) 字节数相同纯属巧合——那边是
                // D=128 半精度行。曾误改成 (4,1,0,0) 只写半行（列 32-63
                // 成残留零, 且跨 rep 自我固化成稳定零假象）
                DataCopy(gmOut[(static_cast<int64_t>(qRow + r) * H + h) * D +
                               dv * T64],
                         t2[r * T64], DataCopyParams(8, 1, 0, 0));
            }
```

## 预防

- 把 `blockLen` 一律写成"字节数 / 32"，并在代码里写明本行的 dtype 与字节数，禁止直接抄源算子的数字。
- 迁移检查表新增一项：**逐个 DataCopyParams 复核 blockLen 的单位**（含同一次迁移里 dtype 被换过的地方）。
- 看到"整齐的列区间恒零"先用块边界假设排查，再怀疑掩码/计算。

## 验证信号

来源：本会话内一次开发轨迹（单条轨迹，单次上板；证据等级均为 `tool_observed`）。

- impl 源码实证：`offsetSrc = offsetSrc + i * (intriParams.blockLen * ONE_BLK_SIZE + intriParams.srcStride)`，`ONE_BLK_SIZE` 为 32 —— 单位是 32B 块。（来源平台：310P；证据等级：tool_observed）
- 误改 `(4,1,0,0)` 后，输出每行后 32 列恒零、且该零列签名在多次重复调用间稳定复现（探针对比"核内留证 vs GM 落地"的最大差达 9.56 量级，说明落地侧被截半）。（来源平台：310P；证据等级：tool_observed）
- 回退到 `(8,1,0,0)` 后该零列签名不再出现（同会话后续探针未再复现）。（来源平台：310P；证据等级：tool_observed）

## 失效边界

- **不覆盖 `BLOCK_MODE_MATRIX` 的 L0C 读出**：该模式下有独立的单位陷阱（曾在同会话里记录"blockLen 单位更宽、按 2048B 量级搬"），本卡的 32B 结论不适用于它。
- **不覆盖非 32B 对齐的行**：行字节数不是 32 的整数倍时不能直接换算，必须先处理尾块或改对齐策略。
- **未验证平台**：其它代际的 `DataCopy` impl 未逐一核对；若 impl 的单位不同（例如按 512B），本卡的数字不成立，但"去读 impl 的 burstLen/offset 计算式再换算"这个方法仍然成立。
- **未决项**：`DataCopyParams` 各字段在 `BLOCK_MODE_MATRIX` 下的精确单位表，本轨迹只留下单条观测，未做系统性核对。

## 坏实践

- **按元素数填 blockLen**：这是最自然的直觉，也是本卡要禁的那一条。
- **跨 dtype 抄同一个 DataCopyParams**：字节数凑巧相等时错误会被掩盖（复制过去看似"没改"），换了 dtype 才炸。

## 误诊

- **误诊（agent_reported）**：改 `(4,1,0,0)` 的理由是"每行只有 64 个元素、之前的 (8,1,0,0) 会多写半行"——把 **f32 行（256B = 8 块）误当成 f16 行（128B = 4 块）**，于是按 4 块写。判别：先算字节数（`cols × sizeof(T) / 32`）再看 impl，不要先动参数。
