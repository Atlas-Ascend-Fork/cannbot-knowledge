---
type: Runbook
title: 广播 tile 写入量超缓冲容量 4 倍覆盖相邻张量
description: 把 128 元素的带参照 ρ 广播成 [4,32,128] f32 tile 时，写进了只有 4096 元素的复用缓冲（需 16384），4 倍越界覆盖相邻张量；改为专用物理尺寸的 rhoPad。
tags: [task.debugging, topic.memory, topic.implementation.memory_management]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/resource_management/TBuf/Get.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/operator.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_UBToUB_highdim_split.md
    role: constraint
created_at: "2026-10-28T09:51:47Z"
updated_at: "2026-10-28T09:51:47Z"
platforms: ["310p"]
---

# 广播 tile 写入量超缓冲容量 4 倍覆盖相邻张量

## 现象

在 310P（dav-m200）上重写分块扫描 kernel 时，带因子式 `q·2^(gk_i − ρ_r)` 需要"每通道一个标量"的带参照 ρ_r 与整段 `gk` 行块同长。第一版直接用 128 元素切片配大 `cnt`，被判为越读（见另一张"calCount 越读"卡），于是改成**先把 ρ 广播成整块 tile**：

```cpp
            // ---- 带参照 ρ_r（per-K 带中点）→ rhoAll [4,32,128] 广播 ----
            //   向量算子按 calCount 平铺读: 带 Sub 需与 gk 行块等长的 ρ 块,
            //   rho[128] 直用会越读相邻 msBuf —— 先行拷贝广播进 aq（因子期空闲）
            ...
            for (int32_t r = 0; r < 4; ++r) {
                for (int32_t row = 0; row < 32; ++row) {
                    DataCopy(aq[r * 4 * T64 * T64 + row * K128], rho[r * K128],
                             DataCopyParams(1, K128 * 4 / 32, 0, 0));
                }
            }
```

"因子期空闲，先借 `aq` 放广播结果"看起来安全（`aq` 是 Aqk tile 的落点，此时确实没被使用）。改完 dump 探针给出一个**极其干净的自证**：

```
1. rhoAll is CORRECT (matches emu) ✓ —— 广播本身内容对
2. gk row 16 matches ✓ —— 但 gk row 40 完全错:
   kernel [-58.5, -76.5, -67.0, -63.0, -59.5]  vs  emu [-41.9, -53.5, -49.2, ...]
   而 rhoAll[3] = ['-58.50', '-76.50', '-67.00', '-63.00', '-59.50']
```

即 **`gk` 的第 40 行与第 3 带的 ρ 广播行逐值相同** —— `gk` 被广播数据覆盖了。另有副签名：某些带 A 行反演出的 ρ 恰好比 emulation 偏 **+15**，正好是因子式里的上界 clamp 值（`Mins(…, 15)`），说明那些行读到的 ρ 是垃圾后被 clamp 夹住。

## 适用场景

- 工程形态：Kernel 直调（AscendC，UB 内多张量按相位复用）。
- API 路径：`DataCopy(dst, src, DataCopyParams(...))` 生成的"按行重复拷贝"广播；`TBuf::Get<float>()` 复用同一块 UB 承载不同相位的张量。
- 验证过的平台与 CANN 版本：Ascend310P3（DAV_2002 / m200）+ CANN 9.1.0，UB 240KB。
- 适用粒度：`operator_family`（任何"按相位复用 UB 缓冲"的 kernel）。
- 路线优先级：`recommended_fastpath`（为广播结果单独开一块容量正确的 TBuf）。
- 不适用 / 未验证场景：未在 A2/A3 验证同一越界无报错行为（未验证，推断可迁移）。UB 越界写**不会**触发断言/报错，只会静默覆盖邻居。

## 根因

`aq` 承载的是 Aqk tile：`[64,64] f32` = **4096 个 f32 = 16KB**。而这次广播写入的是 4 带 × 32 行 × 128 元素 = **16384 个 f32 = 64KB**。

```
写入需求 4 × 32 × 128 = 16384 f32 = 64KB
aq 容量             =  4096 f32 = 16KB
越界量              = 12288 f32 = 48KB = 4 倍容量
```

`DataCopy` 按 `aq[r * 4 * T64 * T64 + row * K128]` 计算目的偏移：`r=3, row=31` 时偏移 = `3*16384 + 31*128 = 53120` 个 f32 —— 远超 `aq` 的 4096，**越界下标直接被当成 UB 地址用**（UB 是平坦地址空间，`LocalTensor` 偏移不做任何容量检查）。这 48KB 覆盖了 `aq` 之后连续分配的若干张量，其中就包括 `gk`，所以 `gk` 的行 32~63 被写成第 2/3 带的 ρ 行——与探针看到的"`gk` 行 40 == `rhoAll[3]`"完全吻合。

判别签名（很值得记住）：**受害张量的某一行与"越界源"的某一行逐值完全相同**。一旦在 dump 里看到这种"不该相等的两行完全相等"，基本可以直接跳到"写入越界"这一结论，不必再查算术。

## 解决配方

`before`（借用 `aq` 放广播结果，容量差 4 倍）：

```cpp
            for (int32_t r = 0; r < 4; ++r) {
                for (int32_t row = 0; row < 32; ++row) {
                    DataCopy(aq[r * 4 * T64 * T64 + row * K128], rho[r * K128],
                             DataCopyParams(1, K128 * 4 / 32, 0, 0));
                }
            }
            SetFlag<HardEvent::MTE3_V>(ev3V);   // 广播落地后 V 方可读
            WaitFlag<HardEvent::MTE3_V>(ev3V);
```

`after`（专用 `rhoPad`：物理尺寸 = 广播需求 `[64,128]` f32，行 `16r..16r+15` 都是 ρ_r）：

```cpp
    pipe.InitBuffer(stBuf, T64 * K128 * sizeof(half));       // 16KB staging
    pipe.InitBuffer(rhoBuf, T64 * K128 * sizeof(float));      // 32KB rhoPad f32
    ...
    LocalTensor<float> rhoPad = rhoBuf.Get<float>();  // 行 16r..16r+15 = ρ_r
    for (int32_t r = 0; r < 4; ++r) {   // rhoPad: 行 16r..16r+15 = ρ_r
        for (int32_t row = 0; row < 16; ++row) {
            DataCopy(rhoPad[(16 * r + row) * K128], rho[r * K128],
                     DataCopyParams(1, K128 * 4 / 32, 0, 0));
        }
    }
```

配套把两处消费点都指向 `rhoPad`（A 构建按 `fb` 对齐、kgqB 按 16 行块）：

```cpp
                Sub(t2, gk[fb * K128], rhoPad[fb * K128], 16 * K128);
                ...
                for (jb = 0; jb < jHi; jb += 16) {          // 16 行块
                    cnt = 16 * K128;
                    Sub(t2, rhoPad[16 * r * K128], gk[jb * K128], cnt);
                    Maxs(t2, t2, -30.0f, cnt);
                    Mins(t2, t2, 15.0f, cnt);
                    Muls(t2, t2, LN2, cnt);
                    Exp(e2V, t2, cnt);
                    Mul(rV, rV, e2V, cnt);
                    Cast<half, float>(staging[jb * K128], rV, RoundMode::CAST_NONE, cnt);
                }
```

要点：
1. 广播结果的容器**必须按广播后的物理尺寸单独申请**，不能借用"相位上空闲"的别人缓冲；
2. 借用空闲缓冲是有效的 UB 复用手段，但**必须先核对容量 ≥ 写入量**，且写入偏移的极值（此处 `r=3,row=31`）要显式算一遍；
3. 为腾出这 32KB，同时把 staging 从双缓冲降为单缓冲（UB 总预算 240KB 内要平衡）。

## 设计决策

- 选"物理补齐 tile"而不是"逐行构建"：块形式能把带因子段的向量调用数从 64 次压到 4 次，性能上确实想要的；补齐 tile 只在每个 chunk 开头建一次（16 次 `DataCopy`），是"一次广播、多次消费"的合理代价。
- 放弃"借 `aq`"的理由：不是为了省 32KB，而是当时错误地假设 `aq` 16KB "够放 32 行"——漏乘了"4 个带"。这里的教训不在复用本身，而在**写入偏移的极值没算**。
- 当前方案在被验证时属 `recommended_fastpath`；但后续该整条块化路径被放弃（见失效边界），故本卡的推荐口径以"容量必须按写入极值核算"为准，不以"用 rhoPad 做广播"为准。

## 系统信息

- 平台：Ascend310P3（DAV_2002 / m200），CANN 9.1.0，UB 240KB / 8 核。
- 相关文件：`kernel/chunk_scan.cpp`（TBuf 声明、ρ 广播段、带因子构建段）；诊断脚本 `<diag-dir>/chunk_scan/emu6.py`（dump `gk` 行 16/40 与 `rhoAll` 四带首行）、`emu.py`/`emu_core.py`（host 同构 emulation）。
- 构建：`bash build.sh` → `build/lib<generic>_ops.so`。

## 完整代码

见 `## 解决配方` 的 before/after（借用 `aq` → 专用 `rhoPad`）及两处消费点改写。

## 预防

- 任何 `DataCopy`/`Duplicate`/向量写的目的偏移，**把循环变量的最大值代进去算一次绝对偏移**，与容器容量比较；`r` 和 `row` 双层循环最容易漏乘外层。
- 复用"相位空闲"缓冲时，在注释里写明"本轮写入量 = X，本缓冲容量 = Y，X ≤ Y"。
- 探针侧固定一条自检：dump 出的张量里若有两个不该相等的行**逐值相同**，直接判"写入越界"。

## 验证信号

来源：分块扫描 kernel（310P）重写期间的精度排查。以下均为本轨迹内的工具输出。

- 越界自证：探针显示 `gk` 行 40 = `[-58.5, -76.5, -67.0, -63.0, -59.5]`，与 `rhoAll` 第 3 带首行 `['-58.50','-76.50','-67.00','-63.00','-59.50']` **逐值相同**；同轮 `rhoAll` 本身与 emulation 一致、`gk` 行 16 一致（来源平台：310P；证据等级：tool_observed）。
- 副签名：某些带 A 行反演出的 ρ 比 emulation 偏约 +15，等于因子式的上界 clamp 值（来源平台：310P；证据等级：tool_observed）。
- 修复后：`aq` 与 band emulation 的误差降到 `2.612e-04`，且**逐迭代确定**（不再随迭代跳变）（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 前提是 UB 为平坦地址空间且 `LocalTensor` 偏移不做容量检查；若换成带运行时断言的编译选项或仿真器，行为会不同（未验证）。
- 本卡修复（32KB `rhoPad`）**并未留在终版 kernel**：块化路径整体退回逐行后，`rhoBuf`/`rhoPad` 被一并移除。原因是插入 4KB `betaBuf` 后 UB 布局整体位移，块化路径又出现新的错坏（见另一张"TBuf 切片越界"卡的现象），最终选择"逐行 + 只块化纯逐元素链"。
- 未验证场景：`DataCopyParams` 行拷贝跨 UB 尾部时是否有硬件裁剪（本例无裁剪迹象，未验证）。
- **未决项（优先）**：布局位移后块化路径的残留错坏从未被单独隔离——本卡证明了"借 `aq` 放广播"这一处越界，但没有证明"修掉它之后块化路径就完全正确"。下个接续点：在容量核算严格的独立缓冲上重做块化，逐段 bisect。

## 坏实践

- 借用"相位空闲"的缓冲却不核算写入量——`aq` 16KB 装 64KB 的广播结果，静默覆盖 48KB。
- 把"这个缓冲这时没用"当成"这个缓冲这时能随便写"。
- 看到 `gk` 被污染先怀疑 cumsum 或 `gk` 自己的写入点（轨迹里确实先这样查过一轮），而"两行逐值相同"本可以直接指向写入越界。

## 误诊

- 曾怀疑是 `prd` 别名（两个 `LocalTensor` 指向同一段 UB）（`agent_reported`）；实际是偏移越界，不是别名。
- 曾怀疑 `gk` 在 cumsum 之后被别处二次写入（`agent_reported`）；`gk` 之后只被读，没有写入点。
- **推断（非实测）**："48KB 越界覆盖到 `gk`"的落点是算术推导（写入量 16384 f32 vs 容量 4096 f32），与观测到的行号/值完全吻合，但未做"只广播不消费"的最小复现。
