---
type: Runbook
title: 整块 Select 的掩码必须连续位打包
description: Select 的 selMask 是位打包的（每元素 1 bit）；逐行 Compare 的结果按 64B 行距摆放时，整块 Select 会连续读 count/8 字节并跨过行间隔，读到陈旧位而错位。掩码连续打包时，整块 Select 在 310P 上 count 512~4096 实测全对。
tags: [task.debugging, topic.implementation.masking, topic.precision, topic.compute.indexing]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Compare.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Select.md
    role: constraint
created_at: "2026-10-28T09:51:16Z"
updated_at: "2026-10-31T09:21:53Z"
platforms: ["310p"]
---

# 整块 Select 的掩码必须连续位打包

## 现象

分块线性注意力形态的 kernel 重写时，把“严格下三角掩码”从“逐行 Select”合并成“一次整块 Select”：

```cpp
readout();                                  // t2 = L（未掩码）
Select(lf, m1, t2, zeros2,
       SELMODE::VSEL_TENSOR_TENSOR_MODE, T64 * T64);   // tril(-1)
```

精度全灭（半 tile 形态的 f32 用例误差 ~1.1e0 量级）。但同一 kernel 的**上一阶段**（GEMM 读出的原始 L）是完全正确的：与期望 `tril(kkgβ @ kgqᵀ, -1)` 的差仅 1.2e-4（f16 舍入噪声）。逐阶段早退式 dump（每阶段全核写一份后 `PipeBarrier<PIPE_ALL>()` 再 return，避免跨核写竞态）显示：

- dbg=1 原始 L：max ~1.2e-4（正确）；
- dbg=2 Select 之后：max ~3.3e-1 ~ 5.4e-1（全 unit 坏）；
- dbg=3/4（P0、逆链）同样坏——误差是从 Select 往后传播的。

把 dbg=2 与 dbg=1 逐元素比对，Select 的实际行为是：

```
lower: sel==raw ratio: 0.4722222089767456
upper: sel==0 ratio: 0.6974206566810608
diag sample sel=[0,0,0,0] raw=[0.42,0.12,0.27,0.13]
bad lower sample: [(1,0, 0.0183, 0.0), (2,1, -0.0241, 0.0), (3,2, 0.0307, 0.0), ...]
bad upper sample: [(9,10, -0.0014, -0.0014), (9,11, 0.0256, 0.0256), ...]
```

即：严格下三角只有 47% 保住了原值（其余被整行零掉），上三角只有 70% 被清零（其余保留原值），对角线正确清零。掩码本身由逐行 Compare 生成、行内 64 元素，逻辑上严格 `j<i`。

另一条独立轨迹（310P，CANN 9.1.0）观察到同一现象的另一种表现：把立方算出的 `[64,64]` f32 矩阵用整张量 `Select` 一次处理 4096 元素，矩阵被清掉的不是上三角，而是**按段/块交错的错误位置**；同一段代码在“每行 64 元素”的形式下正确。该轨迹确认 f16 与 f32 两种数据类型都是同样的失效表现，因此不是数据类型问题——两条轨迹的掩码都是“逐行 64 元素、按行距摆放”，错位来源相同（见下节根因）。

## 适用场景

- 工程形态：AscendC kernel 内的掩码/选择运算（`Select`，`SELMODE::VSEL_TENSOR_TENSOR_MODE`），对象是片上整 tile 的矩阵。
- API 路径：`Select(dst, selMask, src0, src1, SELMODE::VSEL_TENSOR_TENSOR_MODE, count)`；`selMask` 是**位打包**缓冲（`Compare` 的 dst 按 bit 展开，`count` 个元素占 `count/8` 字节）。文档的 U 白名单是 `uint8_t/uint16_t/uint32_t/uint64_t`；本工具链实测 `int8_t` 也可用，保守写法用 `uint8_t`。
- 验证过的平台与 CANN 版本：Ascend310P3（dav-m200 / DAV_2002）+ CANN 9.1.0（实测）。
- 适用粒度：函数级（一个 tile 的掩码运算）。
- 路线优先级：**recommended_fastpath**——整块 Select 配单次 Compare 的连续位流，或逐行 Compare 配逐行 Select；两者都实测正确。
- 明确不适用 / 未验证场景：其他代际（A2/A3/950 等）未验证；f16 数据与其他 `SELMODE` 本轮未重测（A/B 用 float）；`count` > 4096 未测；掩码 bit 序只在本平台验证为 LSB-first。

## 判别方法

**根因**：`Select` 的 `selMask` 是**位打包**的——每元素 1 bit（`Compare` 的 dst 也按 bit 展开），64 个 float 元素只占 8 字节；`VSEL_TENSOR_TENSOR_MODE` 多轮 repeat 按 `count` 连续消费 `count/8` 字节。

逐行 `Compare(m1[i*T64], ..., T64)` 只在每行行首写 8 个有效字节，而 `m1` 的行距是 64 字节（int8 掩码张量 `[64,64]`，每行后 56 字节是间隔/陈旧字节）。随后对整 tile 调一次 `Select(..., T64*T64)`，Select 从掩码基址连续读 `4096/8=512` 字节，跨过 56 字节的行间隔，把间隔里的陈旧字节当成后续元素的掩码 → 按段/块交错地错选 `src0`/`src1`。

这不是 310P 的整块 Select 平台限制：只要掩码是 `count/8` 字节**连续位流**，`Select(..., count)` 在 310P 上 count=512/1024/2048/4096 实测逐元素全对。

判别方法（不需要猜硬件，直接测语义）：

1. 在同一流水线上加“阶段早退 dump”：`if (dbg==k) { dumpF(src, unit); PipeBarrier<PIPE_ALL>(); return; }`，并让**所有核**都走早退（否则别的核继续写同一区域，dump 会读到竞态数据）。
2. 把 dump 与“前一段的 dump”逐元素比对，分别在严格下三角/上三角统计“保持原值比例”和“被清零比例”。两者都不接近 1.0 且对角线正确 → 优先怀疑掩码的字节布局与 Select 的连续消费不匹配。
3. 检查掩码的实际字节：若掩码是逐行 Compare 写的 `[T64,T64]` int8，确认整块 Select 前每行只有前 8 字节有效、后 56 字节是间隔——这是本卡的失败形态。
4. 决定性判别：整块 Select 前把掩码缓冲分别预填 `0x00` 与 `0xFF`，再比对。若总错误数不变而错误位置分布随预填值翻转，即证明 Select 读到的是行间隔里的陈旧字节（布局问题），不是算错或掩码逻辑错。
5. 修复验证：把同一掩码改成逐行 Select，或把掩码改成单次 `Compare(count)` 生成的连续位流后整块 Select，误差应立即回到 1e-5 量级。

## 解决配方

掩码构造保持逐行 Compare（verbatim）：

```cpp
        for (int32_t i = 0; i < T64; ++i) {
            Duplicate(ifRow, static_cast<float>(i), T64);
            Compare(m1[i * T64], colIdx, ifRow, CMPMODE::LT, T64);   // j<i
        }
```

**before（逐行掩码 + 一次整块 Select，错误：掩码不连续）**：

```cpp
        Select(lf, m1, t2, zeros2,
               SELMODE::VSEL_TENSOR_TENSOR_MODE, T64 * T64);   // tril(-1)
        EARLY_DUMP(dbg == 2, lf);
```

**after 1（逐行 Select，正确）**：

```cpp
        // tril(-1) 掩码: 逐行 Select（掩码按行距摆放，Select 必须按行消费）
        for (int32_t i = 0; i < T64; ++i) {
            Select(lf[i * T64], m1[i * T64], t2[i * T64], zeros2,
                   SELMODE::VSEL_TENSOR_TENSOR_MODE, T64);
        }
        EARLY_DUMP(dbg == 2, lf);
```

**after 2（单次 Compare 连续位流 + 整块 Select，正确）**：

```cpp
        // 需要 4096 元素的 colIdxFull / ifRowFull 向量；Compare 一次写出 512B 连续位流
        Compare(m1, colIdxFull, ifRowFull, CMPMODE::LT, T64 * T64);
        Select(lf, m1, t2, zeros2,
               SELMODE::VSEL_TENSOR_TENSOR_MODE, T64 * T64);
        EARLY_DUMP(dbg == 2, lf);
```

不要试图用 8 字节行距把逐行 Compare 的结果“拼”成连续掩码：`Compare` 的 dst 需 32B 对齐，8B 行距不满足；需先落到对齐的临时区再搬运，代价更高。

**合并轨迹的替代解法（整张量三角化用掩码 `Mul`，verbatim）**：

```cpp
            {
                DataCopy(staging, gmScr[scr + A_LTRI],
                         DataCopyParams(TILE * 2 / 32, 1, 0, 0));
                DataCopy(staging2, gmScr[scr + A_M1],
                         DataCopyParams(TILE * 2 / 32, 1, 0, 0));
                SetFlag<HardEvent::MTE2_V>(ev2V);
                WaitFlag<HardEvent::MTE2_V>(ev2V);
                Cast<float, half>(tD, staging, RoundMode::CAST_NONE, TILE);
                Cast<float, half>(t2, staging2, RoundMode::CAST_NONE, TILE);
                Mul(aq, aq, tD, TILE);
                Mul(lf, lf, t2, TILE);
            }
```

注意 `Mul` 的整张量形式（4096）是可靠的；整块 `Select` 本身也可用，前提是掩码连续位打包——所以“用 0/1 掩码张量相乘”始终安全，而“整张量条件选择”要看掩码布局。

## 设计决策

- 逐行 Select 带来 tile 行数量级的 API 调用（本形态 64 次/掩码），在“每次 V-API 有显著固定开销”的平台上不是免费的。它不是唯一正确写法：单次 `Compare(count)` + 整块 Select 也已实测正确；选择取决于索引向量（`colIdxFull`/`ifRowFull`）的构造成本。
- 替代方案（本会话未采用）：用 GEMM 后直接只在 cube 侧产出下三角（例如把上三角乘零），可避免 Select；但需要额外的掩码乘子，代价更大。
- 掩码一律由 `Compare` 产出，不用 `SetValue`/标量循环构造（后者是独立的一类坑，见同批“SetValue 掩码不被 Select 识别”卡）。
- 合并轨迹说明：为什么不用“per-row 三角化循环”作为每 chunk 的常规手段——那是 64 次 `Select`，又回到逐行 V 调用；掩码槽 `Mul` 只需 2 次加载 + 2 次 `Cast` + 2 次 `Mul`。为什么掩码用 f16 槽而不是 f32：掩码值只有 0/1，f16 精确且省一半 scratch。
- 路线优先级：recommended_fastpath。

## 系统信息

- 平台：Ascend310P3 / dav-m200（8 vector core），CANN 9.1.0。
- 工程形态：CMake + `build.sh` 构建 `lib<generic>_ops.so`，torch extension 裸启动（`aclrtlaunch_*`）。
- 相关文件：`kernel/kernel_entry.cpp`（掩码与 Select）、`tests/precision_suite.py`（50 例精度套件，双门限 gate）；调试期 kernel 额外收 `dbg` 参数，用环境变量 `DBG_STAGE` 选择阶段。
- 调试支撑：`dumpF` 把 UB 的 f32 `[64,64]` Cast 到 f16 后写到出口缓冲的对应行区，python 侧从输出张量读回。
- 合并轨迹槽位：`A_LTRI`（下三角含对角 0/1）、`A_M1`（严格下三角 0/1）、`A_EYE`（单位阵）；均为 f16 `[64,64]`。
- A/B 复核工程：`pr190_b1_probe/`（独立 kernel，A=逐行掩码+整块 Select、B=单次 Compare 连续掩码+整块 Select、C=逐行对照；float 数据，`VSEL_TENSOR_TENSOR_MODE`）。

## 完整代码

逐行 Select 的完整因果单元：

```cpp
        for (int32_t i = 0; i < T64; ++i) {
            Duplicate(ifRow, static_cast<float>(i), T64);
            Compare(m1[i * T64], colIdx, ifRow, CMPMODE::LT, T64);
        }
        for (int32_t i = 0; i < T64; ++i) {
            Select(lf[i * T64], m1[i * T64], t2[i * T64], zeros2,
                   SELMODE::VSEL_TENSOR_TENSOR_MODE, T64);
        }
        EARLY_DUMP(dbg == 2, lf);
```

调试用阶段门控宏（verbatim）：

```cpp
#define EARLY_DUMP(COND, SRC)                          \
    do {                                               \
        if (COND) {                                    \
            dumpF(SRC, u);                             \
            PipeBarrier<PIPE_ALL>();                   \
            return;                                    \
        }                                              \
    } while (0)
```

## 性能影响

逐行 Select 相对整块 Select 增加“行数 − 1”次 V-API 调用；在 m200 上按每次数百 cycle 量级的固定开销计，这部分开销可以用“单次 Compare + 整块 Select”消除，但需要 4096 元素的索引向量。两条路径的具体倍率本会话未单独测量（未验证）。合并轨迹的掩码 `Mul` 形态把三角化从“每 chunk 64 次 `Select`”降为“2 次加载 + 2 次 `Cast` + 2 次 `Mul`”，是更优形态。

## 预防

- 任何“并行重写/合并 vector 调用”的优化，都要对掩码类 API 单独做一次语义回归（用 dump 比对，而不是只看最终精度用例）。
- 整块 Select 必须配 `count/8` 字节连续位打包的掩码；逐行 Compare 的结果按行距摆放，不能直接喂整块 Select。把这条写进 kernel 头注释。
- dump 比对时保证所有核都早退，否则你测到的是竞态，不是语义。
- 遇到 `Select`/`Compare` 等带掩码的向量原语，先在目标平台用“整张量 vs 单行”两种形式做一次小规模对拍，再决定用法。
- 掩码清零优先用“0/1 掩码张量 × 数据”，而不是“条件选择”；不要把“f16 与 f32 都错”当成数据类型问题（本卡两条轨迹的错都来自掩码布局）。

## 验证信号

来源说明：主轨迹来自 Ascend310P3 会话内逐阶段早退 dump 与逐元素比对；合并轨迹来自同平台会话内对整张量 `Select` 的实证结论与替代实现；A/B 复核为同平台独立探针 kernel。

- 原始 L（Select 前）与期望的 max 差 1.2e-4，属 f16 舍入噪声；同一 dump 在三次连续运行中逐位一致（来源平台：310P；证据等级：tool_observed）。
- 整块 Select 后：严格下三角“保持原值”比例 47.2%，上三角“已清零”比例 69.7%，对角线正确清零；各 unit 误差 max 3.28e-1 ~ 5.43e-1（来源平台：310P；证据等级：tool_observed）。
- 改逐行 Select 后，同一阶段 dump 误差回到 lf 3.8e-5 / P0 1.2e-5 / 逆链 3.3e-5 量级（来源平台：310P；证据等级：tool_observed）。
- 改后同一探针与参考逐值对齐（gk[0..31] 全部一致，见合并轨迹的修复后 dump）：整块→逐行是该项误差的**隔离修复**；该轨迹后来的全量 `50/50 PASS` 是多项改动叠加后的结果，不作本修复的单点归因（来源平台：310P；证据等级：tool_observed）。
- 合并轨迹：整张量 `Select(4096)` 在 f32 与 f16 下均给出错误结果，per-row（64）正确；改为掩码槽 `Mul` 后三角化正确，全套精度 `50/50 PASS`（来源平台：310P；证据等级：tool_observed）。其失败形态与 A/B 的 A 分支一致（逐行掩码未连续打包）。
- A/B 复核（310P，CANN 9.1.0，float）：逐行 Compare（64B 行距）+ 整块 Select(4096) 有 1988/4096 个元素错；把掩码缓冲预填 `0x00` / `0xFF`，总错数都是 1988，但分布从 first8=448 / rest56=1540 翻转为 first8=56 / rest56=1932，离线按“只读前 512B 连续位流”复算逐行精确吻合（来源平台：310P；证据等级：tool_observed）。
- A/B 复核：单次 `Compare(4096)` 连续位流（512B，LSB-first 展开与期望下三角 4096/4096 全中）+ 整块 Select，count=512/1024/2048/4096 全部 mismatch=0；逐行 Compare + 逐行 Select 对照 C 亦 mismatch=0；int8 与 uint8 掩码结果逐位相同（来源平台：310P；证据等级：tool_observed）。
- A/B 类型探测：half 作 selMask 可编译运行，但按原始 bit 解释（填 `0x3C00` 时输出在 bit 10..13 等位置为 1），**0/1 half 不等于布尔掩码**（来源平台：310P；证据等级：tool_observed）。
- 合并轨迹终版形态进入通过精度门的版本（来源平台：310P；证据等级：artifact_verified）。

## 失效边界

- **逐行构造、按行距摆放的掩码**不能直接喂整块 Select：Select 从基址连续读 `count/8` 字节，跨过行距即错位。连续位流掩码下整块 Select 在 count=512/1024/2048/4096 实测可用（310P，float）；>4096 未测。
- 逐行 Select 形式在行内 count=64 时实测可用（A/B 对照 C）；它与整块 Select 的差异在掩码布局，不在平台能力。
- 只在 `VSEL_TENSOR_TENSOR_MODE` + 位打包字节掩码 + f32（及合并轨迹的 f16）数据上验证；其他模式未验证。
- bit 序为 **LSB-first**（本 A/B 以 4096 bit 与期望下三角逐位全中验证）；其他平台/代际的 bit 序未跨平台验证。
- 合并轨迹的 `Mul` 整张量可用是隐含前提；若某平台 `Mul` 也有 count 限制，需一并改。
- 未决项（优先）：逐行 Select 的 V-API 成本在“每 unit 有多个掩码”的形态下可能成为新瓶颈（本形态未触及）；单次 Compare 需要 4096 元素索引向量，其构造成本未与本卡路径比较。

## 坏实践

- 把“早期版本的逐行 Select”当成可合并的历史包袱，在重写时顺手合并成整块，却没有把掩码一起改成连续位流——本会话正是这样引入回归，且因为原始 GEMM 正确，一度把怀疑引向逆链与输出。
- 依赖“对角线看起来对”来判断掩码整体正确。
- 把整块 `Select` 的失败误判为平台/类型限制，而不检查掩码是否连续位打包（A/B 已证连续掩码下整块 Select 正常）。
- 在可以用连续掩码走整块路径时，仍在热路径上保留 64 行 `Select` 循环（正确但多付调用开销）。

## 误诊

- **误诊 1**：怀疑掩码 `m1` 的内容/构造错（`colIdx`/`ifRow` 的 Compare 逻辑）、或掩码缓冲被覆写、或 `zeros2` 形状不对。逻辑本身正确，真正的问题是掩码的**字节布局**（行距）与整块 Select 的连续消费不匹配。
- **误诊 2**：把“三次 dump 结果不一致”读成 kernel 非确定性；实际是跨核 dump 区域互相覆盖的测量伪影——全核早退后三次逐位一致。
- **误诊 3**：怀疑 `Select` 的 `src1` 应为 `[64]` 向量而非 `[64,64]` 基址。基址等价，非根因。
- 合并轨迹起初怀疑掩码矩阵本身错（因为常量下三角构建也刚出过问题），实际两个问题独立：掩码值对、整块 Select 的掩码布局不连续。
