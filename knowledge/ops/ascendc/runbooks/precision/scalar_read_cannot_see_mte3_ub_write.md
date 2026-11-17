---
type: Runbook
title: 标量 GetValue 读不到 MTE3 写的 UB（op30 语境，最小探针不可复现）
description: op30 实内核中 UB→UB DataCopy（MTE3 写）后的标量 GetValue 即使加了 PIPE_ALL 也读到 0，改成 V 管道 Adds(+0) 后可见；但该现象在干净最小探针（含原失败序列、自动同步两态、180 trial）中不可复现——非 310P 固定语义，属复杂内核语境观察；稳妥写法仍是 V 物化/消掉标量读。
tags: [task.debugging, topic.implementation.synchronization, topic.programming_model.execution_unit.scalar]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/guide/programming_guide/advanced_programming/memory_model/memory_consistency.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/guide/technical_appendix/concepts_and_terms/memory_access/scalar_read_write.md
    role: supporting
created_at: "2026-10-28T09:51:16Z"
updated_at: "2026-11-05T03:51:50Z"
platforms: ["310p"]
---

# 标量 GetValue 读不到 MTE3 写的 UB（op30 语境，最小探针不可复现）

## 现象

Ascend310P3（dav-m200）上，kernel 把一个 `[64,64]` f32 结果从 `t2`（V 管道产出）搬到 `gk` 缓冲，供后续标量读取（带划分要用 `gk.GetValue(i*64)` 算跨度、算 `gkLast`）：

```cpp
            readout();
            DataCopy(gk, t2, DataCopyParams(TILE * 4 / 32, 1, 0, 0));
            SetFlag<HardEvent::MTE3_V>(ev3V);
            WaitFlag<HardEvent::MTE3_V>(ev3V);
```

之后标量读到**全 0**：`gkLast = gk.GetValue((T64 - 1) * 64)` 得到 0，带跨度全 0，`Duplicate(warmF, gkLast*LN2)` 填出 `2^0=1`，下游权重变成 `k·2^{+35}`（远大于 f16 上限，被夹成 65504 量级）。

关键观察：同一缓冲、同样的跨距读，在**它上方**的分区循环里（`gk.GetValue(bnd[nb-1]*64)`）看起来“能用”——但那是假象：当那些读也返回 0 时，`span = 0 − 0 = 0`，带划分退化为“每 16 行一带”，而弱门控用例恰好也是这个划分，所以从结果上看不出差别。这个“退化后仍正确”的巧合，是本 bug 拖了很久才定位的直接原因。

## 适用场景

- 工程形态：AscendC kernel 直调，UB 内张量在“搬运管道（MTE2/MTE3）”与“标量（Scalar）”之间交接。
- API 路径：`DataCopy`（UB→UB 走 MTE3）、`Adds(dst, src, 0.0f, n)`（V 管道物化）、`PipeBarrier<PIPE_ALL>`、`GetValue`；事件 `HardEvent::MTE3_V`。
- 验证过的平台与 CANN 版本：Ascend310P3（dav-m200 / DAV_2002）+ CANN 9.1.0。
- 适用粒度：**op30 语境观察**（310P 实内核中“MTE3 写 UB 后的标量读”）；最小探针（含原失败序列）不可复现，不得当作 310P 固定语义外推到所有“标量读 UB”的代码。
- 路线优先级：recommended_fastpath。
- 明确不适用 / 未验证场景：GM 读取（MTE2 写 UB）后的标量读在本会话可用（旧版 kernel 的 `tD.GetValue(r)` 一直正常）；910B 未验证。

## 判别方法

**根因（现象层结论，限本卡语境）**：UB→UB 的 `DataCopy` 在 m200 上由 MTE3 执行，op30 实内核中该缓冲的标量 `GetValue` 拿不到 MTE3 的写入结果——即使已经 `SetFlag/WaitFlag<MTE3_V>` 并在其后加了 `PipeBarrier<PIPE_ALL>()`，仍读到 0。对照：写者是 V 管道（`Duplicate`/`Add`/`Muls` 等）或 MTE2（GM→UB）时，标量读在该 kernel 的主数据路径上一直正确（另一处 `warmF` 读回的存疑已被复验澄清：隔离语境 180/180 可靠，见验证信号）。

**复验降级（2026-11-05）**：干净最小探针按原失败序列重建（`DataCopy`+`MTE3_V`+`PIPE_ALL`+`GetValue`），自动同步开/关两态 × 8 变体 × 3 rep **全部 PASS**（标量读回 64/64 非零且正确）；V 写 + `PIPE_ALL` → 标量读 180/180 可靠（`V_S` 事件亦可用）。即“MTE3 写对标量架构性不可见”在最小语境**不可复现**，现象属 op30 实内核语境相关（复杂搬运链/多核/布局的哪个成分触发未定）——本卡按“语境观察 + 稳妥写法”取用，不作为平台语义。

**判别探针**（原始观测量）：在“搬运后、下游消费前”对同一索引做两次 dump——一次直接读 `gk.GetValue((T64-1)*64)`，一次把该缓冲整体 dump 到 GM 再回读。若直接读恒为 0、GM 回读非 0，且中间仅隔一个 `DataCopy` + `SetFlag/WaitFlag<MTE3_V>` + `PipeBarrier<PIPE_ALL>`，即可判定为写者管道可见性问题，而不是索引越界或数值错误。

## 解决配方

**解法 A（最小改动）：把这次拷贝改由 V 管道完成**（用一个不改变数值的计算型原语，兼作“物化”）：

```cpp
            // gk ← t2 经 V 管道拷贝（标量 GetValue 读不到 MTE3 写的 UB ——
            // UB→UB DataCopy 走 MTE3, 探针实证 gkLast=0; Adds(+0) 走 V）
            Adds(gk, t2, 0.0f, TILE);
```

同一处还加了“标量读 V 写数据前必须排水”的护栏：

```cpp
            {
                Duplicate(warmF, gkLast * LN2, 128);
                Exp(warmF, warmF, 128);
                PipeBarrier<PIPE_ALL>();
                glF = warmF.GetValue(0);
            }
```

**解法 B（更稳）：干脆不要标量读**。上面这段最终被整体删掉，`glF = 2^{gkLast}` 改在标量单元直接算（`KExp2(gkLast)`）：

```cpp
            // 2^gk_last: 设备标量 exp（向量回读的标量读不可靠, 与 gkLast 同律）
            const float glF = KExp2(gkLast);
```

理由：`gkLast` 本身已经是标量寄存器里的值，绕一圈“写进 UB 再读回来”没有任何收益，只引入跨管道可见性问题；而 `2^x` 在标量单元用位技巧 + 泰勒多项式即可（约十几条标量指令）。

**解法 C（本会话实现过）：让写者变成 MTE2**。当数据必须留在 UB、又必须被标量读时，把“该列的标量来源”做成一次 GM 往返——V 写的结果推 GM，再 `DataCopy` 回 UB（MTE2 写），标量读这个 MTE2 写的视图：

```cpp
            // ---- 列 0 GM 往返（标量 GetValue 只对 MTE2 写可靠 —— V 写的
            //      缓冲直读在强门例取错值; 列0 每行同值, 取首块即可）----
            PipeBarrier<PIPE_ALL>();
            DataCopy(colF, gk, DataCopyParams(T64, 1, 7, 0));
            PipeBarrier<PIPE_ALL>();
            pushAt(GKC, colF.ReinterpretCast<half>(), 64);
            DataCopy(colF, gmScr[scr + GKC],
                     DataCopyParams(64 * 8 * 4 / 32, 1, 0, 0));
            SetFlag<HardEvent::MTE2_V>(ev2V);
            WaitFlag<HardEvent::MTE2_V>(ev2V);
            PipeBarrier<PIPE_ALL>();   // 标量读前仍需全屏障：MTE2→V 事件对
                                       // 不保证标量管有序（见 runtime/
                                       // scalar_metadata_table_needs_256b_copy_and_barrier.md）
```

（注：块内注释“标量 GetValue 只对 MTE2 写可靠——V 写的缓冲直读在强门例取错值”为当时怀疑的原始记录，后经复验澄清：V 写 + `PIPE_ALL` 的标量读在隔离语境 180/180 可靠、主数据路径一直正确——以“判别方法/失效边界”为准，代码仅记录实际形态。）

代价是一次 MTE3 出去 + 一次 MTE2 回来（约几十字节）；收益是“标量读”这条路径的写者变成本会话唯一被证实可靠的 MTE2。该段后来随门控前缀和构建回退而被移除，因此**终版是否仍存在 V 写→标量读，请以代码为准，不要假设本卡已覆盖**（见失效边界）。

## 设计决策

- 为什么用 `Adds(x, y, 0.0f)` 而不是补更多同步：同步解决的是“顺序”，而实测问题是“可见性”（顺序已满足、值仍为 0），只有换写者管道能解。
- 为什么同时保留 `PipeBarrier<PIPE_ALL>` 护栏：V 写→标量读的顺序本卡未用事件对覆盖。源码核对（CANN 9.1.0 `impl/basic_api/kernel_event.h:61-65`）表明枚举**存在** `V_S`/`MTE2_S`/`MTE3_S` 方向（2002 的 `EventToIndex` 走恒等映射，方向均有效），与旧版卡片“枚举无 V→Scalar 方向”的表述不符；`V_S` 事件对是候选，本卡采用已实测可靠的 `PipeBarrier<PIPE_ALL>`（隔离探针 mode2 已实测 `V_S` 事件可用；既有卡 [scalar_output_v_mte3_loss_readback](scalar_output_v_mte3_loss_readback.md) 亦记录 `V_S` + `GetValue` 逐位正确的独立案例）。
- 为什么优先“消掉标量读”：每消除一次跨管道读，就消除一类不确定性；且 `KExp2` 比“写 64 元素 + `Exp` + 读回”更便宜。
- 路线优先级：recommended_fastpath。

## 系统信息

- toolchain：CANN 9.1.0，bisheng/ccec，`cmake` + `ascendc.cmake`，SOC_VERSION=Ascend310P3。
- 目标平台：Ascend310P3（dav-m200 / DAV_2002）。
- 缓冲：`gk`/`gk2` 为 `[64,64]` f32；`warmF` 为 128 元素 scratch。
- 可用事件：`HardEvent::MTE2_V`、`MTE3_V`、`V_MTE3`、`MTE1_M`、`V_S`、`MTE2_S`、`MTE3_S`（`kernel_event.h:61-65`，2002 恒等映射均有效）；本卡实测用过前四种。
- 工程自动同步开关：bisheng 工程默认开；复验对开/关两态做了干净探针对照，结果一致（均正确）。

## 完整代码

解法 A（V 管道物化）与解法 C（GM 往返）的完整段已在上节内联。可直接复用的最小替换单元：

```cpp
            // before: DataCopy(gk, t2, DataCopyParams(TILE * 4 / 32, 1, 0, 0));
            //         SetFlag<HardEvent::MTE3_V>(ev3V);
            //         WaitFlag<HardEvent::MTE3_V>(ev3V);
            // after:
            Adds(gk, t2, 0.0f, TILE);   // 走 V 管道，标量 GetValue 可见
            // 注意：其后标量 GetValue 前仍需 PipeBarrier<PIPE_ALL>()（见预防）
```

## 性能影响

本卡是正确性修复，且**性能上是净收益**：删掉“写 UB + `Exp` + 读回”的一段（含一次 `Duplicate`、一次 64 元素 `Exp`、一次全屏障）换成约十几条标量指令；`Adds(gk, t2, 0.0f, TILE)` 与它替代的 `DataCopy(gk, t2, 512 块)` 指令数相当（一次 V 调用 vs 一次 MTE3 调用）。

## 预防

- 标量要用的值，尽量在标量侧算出来；不要“写进 UB 再读回来”。
- 必须从 UB 读标量时，问清楚写者是哪个管道：MTE3（UB→UB `DataCopy`）→ 本卡语境实证不可读（最小探针不可复现、机制未定），不要依赖；V → 加 `PipeBarrier<PIPE_ALL>` 后再读（隔离复验 180/180 可靠），并把读到的值 dump 出来验证一次。
- 调试跨管道可见性问题时，用“同一个值的两条独立路径”交叉验证（例如同时打印 `gkLast` 和由它派生的张量），否则“看起来能用”会误导。

## 验证信号

来源说明：本卡来自 Ascend310P3 会话内 dbg dump 的定位过程（`gkLast` 读到 0、下游饱和）与修复后的复测。

- 修复前：`gkLast` 标量读为 0，下游权重饱和到 f16 上限量级（`k·2^{+35}`）（来源平台：310P；证据等级：tool_observed）。
- 修复前：带跨度 `span` 恒为 0，带划分退化为每 16 行一带（在弱门控用例上与正确划分相同）（来源平台：310P；证据等级：tool_observed）。
- 改为 V 管道 `Adds(+0.0f)` 后标量读恢复，`gk` dump 与参考一致（来源平台：310P；证据等级：tool_observed）。
- 修复后的版本进入 `50/50 PASS` 的全套精度门（来源平台：310P；证据等级：tool_observed）。
- 复验（2026-11-05，310P chip 2）：干净最小探针按原失败序列重建，自动同步开/关两态 × 8 变体 × 3 rep 全 PASS（标量读回 64/64 非零且正确）；V 写 + `PIPE_ALL` → 标量读 180/180 可靠，`warmF` 配方全对（来源平台：310P；证据等级：tool_observed）。
- 源码核对：CANN 9.1.0 `kernel_event.h:61-65` 枚举含 `V_S`/`MTE2_S`/`MTE3_S`，2002 的 `EventToIndex` 走恒等映射（来源平台：CANN 9.1.0 源码；证据等级：artifact_verified）。

## 失效边界

- 只在 Ascend310P3 + CANN 9.1.0、op30 实内核语境验证；“MTE3 写不可被标量读”**不是**该 SoC 的固定语义（最小探针两态不可复现；源码亦存在 `MTE3_S` 事件方向）——语境相关，触发成分（复杂搬运链/多核/布局）未定。
- “V 写 + `PIPE_ALL` + 标量读”在隔离语境 180/180 可靠（原 `warmF` 存疑已被复验澄清）；但在 op30 实内核中该路径当时未单独再验，终版以“删掉标量读”绕过。
- `Adds(x, y, 0.0f)` 作为“复制”依赖编译器保留该指令；开高优化后未重复验证。
- 未决项（收窄）：触发“MTE3 写→标量读旧值”的语境成分（搬运链形态/多核/布局）未定位——复现需带 op30 原语境；`V_S` 事件对替代 `PIPE_ALL` 在 op30 实内核语境的效果未实测（隔离探针 mode2 与既有卡 [scalar_output_v_mte3_loss_readback](scalar_output_v_mte3_loss_readback.md) 已各自实证可用，见设计决策）；标量写→MTE3 读的反向问题（`SetValue` 后推 GM 槽）本会话也遇到，未单独成卡验证。

## 坏实践

- 用 `DataCopy`（UB→UB）搬运“马上就要被标量读”的数据。
- 以为加了 `SetFlag/WaitFlag` + `PipeBarrier<PIPE_ALL>` 就等价于“标量能看到”。
- 用“某些用例结果对”证明标量读正常（退化路径可能与正确路径同结果）。

## 误诊

- 最初怀疑“`GetValue` 大索引越界/单位错”（例如把元素索引当成字节索引），并去核对 `8064` 这类常量；实际索引是对的，值是 0。
- 也怀疑过“广播矩阵写错”，因为现象表现为 `2^{gk}` 全为 1——那是 `gkLast=0` 的下游表现。
