---
type: Optimization
title: CV 混合核下 vec 子核按行交错切分，消除多子核冗余并行
description: 将vec子核的行工作按交错方式切分。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/03-aiv-subcore-s1-split.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：CV 混合核下 vec 子核按行交错切分，消除多子核冗余并行

> **单一优化点：** 在 cube-vec 混合核（CV，1 个 cube 配 N 个 vec 子核）架构下，若 vec 关键路径阶段的工作循环起点恒为 0、未使用 `GetSubBlockIdx()`，则同核组内 N 个 vec 子核冗余执行完全相同的代码、处理全量行、写同一 workspace 槽（数据幂等、无精度问题），浪费 `(N-1)/N` 的 vec 算力。改为按子核交错切分行循环，使每个子核只处理不重叠的 `splitM` 行块，vec 有效并发度提升至 N 倍。

---

## 1. 已有模式与变更

**已有模式（baseline）：** vec 工作循环起点恒 0、步长固定 `splitM`，`GetSubBlockIdx()` 返回值仅声明保存、未参与切分：

```text
subBlockIdx = GetSubBlockIdx()                      // 0..N-1，但循环未用到
for s1Off = 0; s1Off < tileRows; s1Off += splitM:    // 【已有】N 个子核都从 0 起，遍历全部行
    rowsThis = min(splitM, tileRows - s1Off)
    compute_and_writeback(s1Off, rowsThis, s1Off * rowStride)
```

**变更（仅改循环边界，循环体逻辑不变）：**

- 【变更】行循环起点 `0` → `subBlockIdx * splitM`。
- 【变更】行循环步长 `splitM` → `subBlockNum * splitM`（每子核认领第 `subBlockNum` 个 `splitM` 块）。
- 【不变】循环体写回偏移仍为 `s1Off * rowStride`（天然使各子核写不重叠行段）。
- 【不变】跨核 flag 保持 mode2（`0x2`），**不新增、不修改任何 cross-core flag**。
- 【不变】总工作量与下游消费的输出布局完全不变。

**`expected_speedup_pct`：** 约 `(N-1)/N × 100` 的 vec FLOP 冗余被消除（如 N=2 时约 50%）。但实际 wall-clock 收益受限于两点：(1) 依赖 N=`GetSubBlockNum()`；(2) 仅当 vec 是瓶颈资源（`aiv_time >= aicore_time`）时该冗余消除才转化为端到端收益。若 cube 已接近瓶颈，整体收益被 cube 转移限制（属预期，非缺陷）。典型 N=2 且 vec 强瓶颈场景：vec 关键路径周期约减半，端到端 task duration 改善为「定性正向」而非固定百分比。

---

## 2. 参数变更表

| parameter | baseline | v1.1 | unit | remark | constraint |
|---|---|---|---|---|---|
| loopStart | `0` | `subBlockIdx * splitM` | row | 行循环起点；【变更】 | `subBlockIdx < subBlockNum`；起点 `< tileRows` 时循环才进入 |
| loopStep | `splitM` | `subBlockNum * splitM` | row | 行循环步长；【变更】交错间距 | `subBlockNum * splitM > 0`；步长须使各子核块满足向量 API 对齐/掩码约束 |
| splitM | per-tile 行块大小 | per-tile 行块大小（不变） | row | 单次迭代处理行数 | 须满足向量 API 的 datablock 对齐（如 dealRowCount 对齐）；`splitM >= 1` |
| tileRows | tile 内 vec 阶段总行数 | 不变 | row | vec 阶段本 tile 负责的总行数 | 尾块 `tileRows % (subBlockNum*splitM) != 0` 时仍须正确（见 §3 红线） |
| rowsThis | `min(splitM, tileRows-s1Off)` | `min(splitM, tileRows-s1Off)`（不变） | row | 本次实际行数 | 尾块可能 `< splitM`，须走非满批路径 |
| writeOffset | `s1Off * rowStride` | `s1Off * rowStride`（不变） | elem | workspace 写回偏移 | 天然保证各子核行段 `[s1Off, s1Off+rowsThis)` 互不重叠；基址须 32B 对齐 |
| crossCoreFlagMode | mode2 (`0x2`) | mode2 (`0x2`)（不变） | - | cube↔vec 组级同步 | 【禁止变更】保持 1→N 广播 / N→1 汇聚；不新增 flag、不分配 per-子核 sigId |
| headWaitPos | 循环外 | 循环外（不变） | - | 头同步 Wait 位置 | 空核子核也须执行（不得移入循环或删除） |
| tailSetPos | 循环外 | 循环外（不变） | - | 尾同步 Set 位置 | 空核子核也须执行（见 §3 红线） |

---

## 3. 结构变更模式

**抽象结构：** 将一段「起点恒 0、步长 `splitM`、`GetSubBlockIdx()` 未使用」的 vec 行循环，改为「起点 `subBlockIdx*splitM`、步长 `subBlockNum*splitM`」的交错切分，使同核组 N 个子核各自认领互不重叠的 `splitM` 行块。循环体写回偏移 `s1Off * rowStride` 天然使各子核写不同行段，无需子核间数据同步。cube 侧下游按完整 `tileRows` 行块消费，由 N 个子核各写一段拼满。

**伪代码（含尾块/空核子核处理）：**

```text
subBlockIdx = GetSubBlockIdx()          // 0 .. subBlockNum-1
subBlockNum = GetSubBlockNum()          // 同组 vec 子核数（CV 1:N 下为 N）

CrossCoreWaitFlag<0x2, PIPE_V>(sigId)   // 头同步：cube→vec 广播，每子核都 Wait（在循环外）

start = subBlockIdx * splitM            // 【变更】起点
step  = subBlockNum * splitM            // 【变更】步长

for s1Off = start; s1Off < tileRows; s1Off += step:   // 空核子核：start>=tileRows → 不进入循环
    rowsThis = min(splitM, tileRows - s1Off)          // 尾块：rowsThis 可能 < splitM
    // 各子核只从 cube 产出的完整块读自己行段（不全量读后再丢弃）
    readRowBlock(mmTensor, s1Off * rowStride, rowsThis)
    compute(rowsThis)
    writeback(s1Off * rowStride, rowsThis)            // 行段互不重叠

CrossCoreSetFlag<0x2, PIPE_V>(sigId)    // 尾同步：vec→cube 汇聚，每子核都 Set（在循环外，空核也执行）
```

> 红线：头 Wait 与尾 Set 必须在 for 循环**之外**。空核子核（`start >= tileRows`，循环不进入）也必须执行这两个同步，否则同组 cube 的 N→1 汇聚因少收一个 Set 而挂死。

---

## 4. 反模式

- **pattern:** 为每个子核分配独立 cross-core sigId 或改成 1:1 同步 | **reason:** 破坏 mode2 组级语义，cube 侧无法广播/汇聚 | **metrics:** flag 数爆炸、同步开销上升、可能死锁
- **pattern:** 头 Wait / 尾 Set 写在 for 循环内部 | **reason:** 空核子核循环不进入 → 不发 Set → cube N→1 永久挂死 | **metrics:** 死锁（功能错误，非性能）
- **pattern:** 各子核仍全量读 cube 完整块再丢弃自己不负责的行 | **reason:** 冗余从「计算」挪到「搬运」，MTE2 未减 | **metrics:** mte2 搬运量不降反升，端到端无收益
- **pattern:** 各子核写同一原子累加地址或重叠行段 | **reason:** 数据竞争，破坏幂等性 | **metrics:** 精度 mismatch / 随机 NaN
- **pattern:** `splitM` 不满足向量 API datablock 对齐 / 尾块强行满批 | **reason:** 触发对齐异常或越界写 | **metrics:** 运行时异常 / 越界
- **pattern:** cube 侧按子核切分（cube 也感知 subBlockIdx） | **reason:** cube 产出须保持完整 `tileRows` 行块供 N 子核拼读；cube 切分会破坏拼满语义 | **metrics:** 行段空洞 / 下游读到未覆盖区域
- **pattern:** 持久 UB 行索引缓存仍按单子核容量定容 | **reason:** 各子核只写自己行段但缓存须覆盖完整不变范围 | **metrics:** 跨迭代读到被覆盖的陈旧分区

---

## 5. 硬件约束表

| resource | capacity | baseline_usage | v1.1_usage | constraint |
|---|---|---|---|---|
| vec 子核数 (subBlockNum=N) | 芯片相关，ascend-hardware 获取 | N 个子核冗余执行全量 | N 个子核各处理 1/N | `GetSubBlockNum() > 1` 才有收益；N=1 时跳过本策略 |
| vec FLOP 利用率 | 100% (满并发) | `1/N`（冗余稀释） | `~1`（无冗余） | 冗余消除上限 `(N-1)/N` |
| UB 容量 | 芯片相关，ascend-hardware 获取，禁硬编码 | 持久缓存按完整范围定容 | 不变（各子核独立 UB 隔离） | 分区索引按全局行偏移 `s1Off*statWidth`；容量按完整不变范围，非单子核 |
| workspace/GM 行块 | tileRows 行 | N 子核重复写全量 | N 子核各写不重叠段 | 行段并集 == `[0, tileRows)`，无重叠、无空洞；基址 32B 对齐 |
| cross-core flag (mode2) | 1 组 sigId | 1 广播 + 1 汇聚 | 1 广播 + 1 汇聚（不变） | 禁止新增 flag / per-子核 sigId；空核也须发 Set |
| 向量 API 对齐 | datablock 对齐 | splitM 满足 | splitM 满足 | 尾块 rowsThis `< splitM` 须走非满批路径（mask/Pad） |

---

## 6. 协同建议

**独立性声明：** 本策略可独立执行。它仅改 vec 行循环边界与同步位置，不改输出布局、不改 cube 侧逻辑、不改其他 vec 阶段。

**synergistic_with:**
- `01-softmax-scalar-to-vector`：标量归约向量化降低单子核 vec 周期，与子核切分叠加（前者降每子核工作量常数，后者提并发倍数）。
- `02-softmax-stats-s2-cache`：跨迭代 UB 缓存消除重复 MTE2；切分后各子核只访问自己行段分区，缓存定容不变。
- `04-batch-cast-loop-elimination`：整块批量 Cast 替代逐行循环；与子核切分正交（Cast 仍在每子核自己的行段内做整块）。

---

## 7. 验证要点

**compile_check:**
- `GetSubBlockIdx()` / `GetSubBlockNum()` 返回值已接入循环边界（非仅声明）。
- 头 Wait / 尾 Set 在 for 循环之外（编译期可见，非循环内）。
- 未引入任何新的 `CrossCoreSetFlag`/`CrossCoreWaitFlag`，mode 仍为 `0x2`。
- splitM 仍满足向量 API 对齐约束；尾块非满批路径存在。

**accuracy_check:**
- **尾块 shape（`tileRows % (subBlockNum*splitM) != 0`）：** 必须从 FAIL→PASS。激活空核子核路径（`start >= tileRows` 循环不进入但 flag 仍发），验证无挂死、无行段空洞。
- **`actualCols % 8 != 0` shape：** 须从 FAIL→PASS（本策略不改列向 Cast/Pad，但须确认切分不破坏既有尾列路径）。
- 满批 shape（能被 `subBlockNum*splitM` 整除）结果与修改前一致（幂等冗余被切分后数学等价）。
- 大 batch / 多 head（多核组）下结果稳定，无随机 NaN 或 mismatch。
- 各子核行段并集 == cube 下游读取的 `[0, tileRows)`，无重叠、无空洞。

**performance_check:**
- vec 总周期数 / `aiv_vec_time` / `aiv_scalar_time` 绝对值下降约 N 倍（子核冗余消除）。
- mte2/mte3 搬运量不上升（各子核只读/写自己行段，非全量）。
- `aiv_scalar_ratio` 向目标 `< 30%` 靠拢。
- task duration 改善方向正确；若 cube 原本接近瓶颈，整体收益受 cube 转移限制（预期，需配合 cube 侧优化进一步突破）。

## 检索卡（短卡）

动作：将vec子核的行工作按交错方式切分。
范围：一个cube配N个vec子核的CV混合核。
检索词：cube-vec混合核、CV、vec子核、按行交错切分。
