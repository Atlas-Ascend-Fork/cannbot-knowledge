---
type: Runbook
title: "分块循环MTE2重载共享UB须V→MTE2边界栅栏"
description: "多块循环每轮 MTE2 重载同一 UB staging、块内 V 消费时，迭代边界必须带 V→MTE2 栅栏（SetFlag/WaitFlag<HardEvent::V_MTE2>），否则下一块重载抢在 V 读完前覆写：950 确定性「末块外全错」、310P 非确定漂移两种表型同根。"
tags: [task.debugging, topic.precision, topic.implementation.synchronization, topic.programming_model.execution_unit.vector, topic.data_movement, topic.memory]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/bb96c9c595c7a8e96745d365291769dc48319c22/plugins-community/ascendc-port-orchestrator/kb/okf/runbooks/field-notes/build/pb-47-chunk-loop-ub-write-after-read-hazard-a-per-tile-b.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/guide/programming_guide/advanced_programming/memory_model/memory_consistency.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/guide/programming_guide/advanced_programming/advanced_kernel_programming/intra_core_sync/mutex_multi_pipeline_sync.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/SetFlag_WaitFlag_ISASI.md
    role: supporting
created_at: "2026-07-09T16:00:00Z"
updated_at: "2026-11-25T10:00:57Z"
platforms: ["950", "310p"]
aliases: ["PB-47"]
---

# 分块循环MTE2重载共享UB须V→MTE2边界栅栏

> 原 OKF v1 卡号：**PB-47**（迁移件；950 实例证据等级见「## 失效边界」存量声明）。
> 现象分类：precision/data corruption；原卡观测置信度 single_run，本轮 310P 实例的修前非确定性来自修复注释（artifact_verified），修后数值为原始工具输出（tool_observed）。

## 现象

两个平台实例、两种表型、同一根因：

- **950 实例（2026-06-22，存量 PB-47 记录）**：selective_scan 反向 `grad_z` 确定性错值，签名极具辨识度——**除最后一个分块外每个分块都错**（末块没有后继重载去覆写它的缓冲）；被污染的值是后续某次迭代 MTE2 重载已写入的缓冲内容（L=512 时 chunk0 读到 `C[l=256]`）。
- **310P 实例（2026-11-16，本轨迹）**：CBAM 空间注意力内核在大空间用例上**非确定性**误差——同一输入多次运行 max/avg 漂移（区别于 950 的确定性表型）。触发几何为多块循环：空间维 HWP=16384 按 4096 分块 = 4 块的用例才暴露，单块/少块用例不触发。

两表型同根的机制解释：下一块 MTE2 重载落在当前块 V 读完之前还是之后是一场竞态——时序每次都吞掉同一份旧值就呈确定性表型，落点漂移就呈非确定表型。

## 适用场景

- 工程形态：AscendC chunked/tiled 内核——外层循环（L-chunk / 空间分块 / 收缩维分块）每轮顶部经 MTE2 **重载同一组共享 UB staging 缓冲**，块内稍后由 V pipe 消费。
- API 路径：MTE2（GM→UB 拷贝）与 V pipe 并发；`HardEvent`（V_MTE2 等）令牌。手工复用路径下，EnQue/DeQue 就绪通知只定序 MTE2→V、不提供 V→MTE2 反向定序（TQue 队列缓冲的 FreeTensor/AllocTensor 复用同步是另一条路径，不替代手工复用所需的显式栅栏）。
- 验证过的平台与版本：Ascend 950PR_957b + CANN 9.1.T500 + bisheng AIV（存量 PB-47 记录，`verified_on: soc=Ascend950PR_957b; cann=9.1.T500`）；Ascend 310P3（dav-m200 / `__NPU_ARCH__`=2002）+ CANN 9.1.0，aarch64（本轮轨迹）。
- 适用粒度：`pattern`——多块循环 + 共享 UB staging 的内核（跨算子同构模式）。
- 路线优先级：`recommended_fastpath`（显式 `V→MTE2` 栅栏——`SetFlag`/`WaitFlag<HardEvent::V_MTE2>`，几行、相对每块计算可忽略；双缓冲 per-chunk 私有缓冲按槽位同步、仍须显式栅栏，本轨迹未对比）。跨轮聚合 set/wait 或缺栅栏形态属违例（见「## 坏实践」）。
- 明确不适用/未验证：910B（DAV_2201）/A2/A3 未复测（同 AIV V/MTE2 并行管道架构，预期适用，无跨代见证）；`unverified_on: soc=Ascend910_V220`。

## 根因

外层循环每轮顶部 MTE2 重载的 UB 缓冲，与**上一轮**循环内 V pipe 对同一缓冲的消费之间无定序：手工复用路径下，AscendC 队列 EnQue/DeQue 就绪通知只自动定序 MTE2→V，**不提供 V→MTE2 反向定序**；迭代边界没有显式 `V→MTE2` 栅栏时，下一轮的 MTE2 重载在当前轮 V 算子读完之前就覆写缓冲。这是 [PB-17](pb_17_ub_aliasing_cross_row_v_mte2_hazard_silent_data_co.md)（单融合 `ProcessRow` 内跨行别名变体）的**跨迭代类比**：PB-17 是两个 UB 缓冲在行内别名，PB-47 是同一缓冲逐轮重载——同为 AIV V/MTE2 双管道并发危害类，触发语境与诊断签名不同，分卡收录。

310P 实例补充：单块平面没有"下一块重载"，且单块尾部由树后 `V_S`（向量同步）天然护住，故小用例全绿——**只有最大用例（块数 ≥2）暴露**是该竞态的典型信号。

## 判别方法

1. 多块/多 tile 循环重载共享 per-tile 缓冲的内核，检查该缓冲是否被同轮稍后的 V pipe 算子消费、且 V 消费与下一轮 MTE2 重载之间无 `V→MTE2` 事件。
2. 精度签名「除最后一个分块外全错」→ 直接怀疑本 hazard（950 确定性表型）。
3. 同输入多次运行 max/avg 漂移 + 失败仅出现在块数 ≥2 的几何 → 非确定表型（310P）；先审 staging 复用点，不要先怀疑设备/环境。
4. 静态审查：数每个通道 `SetFlag`/`WaitFlag` 的循环作用域配对，令牌收支逐轮平衡。

## 解决配方

在"当前块 V 消费完成"与"下一块 MTE2 装载"之间插入 `SetFlag/WaitFlag<HardEvent::V_MTE2>` 握手（V→MTE2 方向令牌——保护的是"读完了"而非"写好了"）。950 原卡形态为循环顶条件栅栏 `if (l0 > 0) SyncVtoMTE2();`（≈8 行）；310P 实例修前/修后（op78 CBAM 内核，逐字摘自修复 Edit）：

修前（块尾无栅栏，下一块重载可抢覆写）：

```cpp
            // 和: 原值（行垫零天然排除; [n,CHUNK) 恒 0 初值不参与）
            Add(sumA, sumA, af, n);
            // max: 垫列加法掩码 —— 有效列 x+0=x 精确, 垫列 0+NEG_BIG 排除
            if (needMask) {
                Add(af, af, nbRow, n);
            }
            Max(maxA, maxA, af, n);
        }
```

修后（`Max` 之后、循环闭括号前加 V→MTE2 对）：

```cpp
            // 和: 原值（行垫零天然排除; [n,CHUNK) 恒 0 初值不参与）
            Add(sumA, sumA, af, n);
            // max: 垫列加法掩码 —— 有效列 x+0=x 精确, 垫列 0+NEG_BIG 排除
            if (needMask) {
                Add(af, af, nbRow, n);
            }
            Max(maxA, maxA, af, n);
            // 跨块竞态律（case49 实测: HWP=16384=4 块时 max/avg 非确定错）:
            // 下一块 MTE2 重载 af/c16 前, 必须排空 V 对本块的消费
            // （单块平面由树后 V_S+GetValue 天然排空护住; 多块平面无此屏障）
            SetFlag<HardEvent::V_MTE2>(6);
            WaitFlag<HardEvent::V_MTE2>(6);
        }
```

（通道字面量 `6` 的选取依据：本 kernel 函数（op78_pool_310p）的 `SetFlag/WaitFlag<HardEvent::V_MTE2>` 仅此一处；同文件 op78_sgate_310p（K3）另有一处 V_MTE2 对、同样用通道 6——两处合计 V_MTE2 通道 0-5 从未占用，且本文件未用队列框架（无 EnQue/DeQue 内部分配）；迁移到其它内核时须先列全同一 HardEvent 的全部 set/wait 字面量（含队列框架经 AllocEventID 分配的部分）再取空位，eventID 合法范围随产品型号而定。）

## 设计决策

- 令牌方向选 V→MTE2（消费完成方向握手），不是 MTE2→V 的就绪通知：要保护的是"V 读完"而非"MTE2 写好"。
- 每块加栅栏而不是仅首块：块数参数化的内核任何块数都须正确；单块的天然护住（树后 `V_S`）不可依赖。
- 双缓冲只把同地址冲突从相邻轮推迟到相隔轮，并不免除栅栏：每个缓冲在再次写入前仍须确认上一使用者读完，双缓冲可按槽位同步（复用间隔变长）；仅在各块地址独立且本轮不再复用、或框架已提供等效依赖时才能省显式栅栏。本轨迹未对比，列备选。

## 系统信息

- 950 实例：Ascend950PR_957b，CANN 9.1.T500，bisheng AIV；selective_scan_source_a5 bwd_simd PASS-A L-chunk 循环（`Ct` 经 MTE2 装载、ysc `Mul(prodC, xall, Ct, CN)` 消费）。
- 310P 实例：Ascend 310P3（6 卡机），DAV_2002/dav-m200，CANN 9.1.0，aarch64（EulerOS）；CBAM 空间注意力内核（`kernel/op78_cbam.cpp`），HWP=16384 按 4096 分块 = 4 块共享 UB 载入缓冲（af/c16 系数缓冲）。

## 预防

- 多块循环 + 共享 UB staging 的内核模板评审固定项：循环边界逐通道核对 V→MTE2 定序。
- 测试套件必须含「最大几何用例 × 重复运行」的确定性检查，否则该类竞态漏网（单块/少块用例全绿不代表路径无坑）。

## 验证信号

- 950 实例（存量 PB-47 记录，fixed source）：UB-instrumentation 判决 `Ct in UB == truth C[l=256], diff 0.0`；修复 `if(l0>0) SyncVtoMTE2();` 后 grad_z MERE 1.499 → 1.85e-7（来源平台：950；证据等级：artifact_verified，迁移自 OKF 原卡白盒取证）。
- 950 向量化复验：2.69× scan 向量化重写（PR#37，merged main `bda9cb3c`）重走同一携带栅栏的分块循环，精度 30/30 truth-backed 保持——栅栏在向量扫描形态下仍必要且位置正确（来源平台：950；证据等级：artifact_verified，迁移记录）。
- 310P 修前（case 49，HWP=16384=4 块）：同输入 max/avg 非确定漂移（来源平台：310p；证据等级：artifact_verified，修复注释内嵌历史实测记载，非原始重复调用输出）。
- 310P 修复落地：内核 Edit 加 V_MTE2 排空 + 竞态律注释（来源平台：310p；证据等级：artifact_verified）。
- 310P 修后：case 49 PASS（err 3.193e-03 / gate 6.387e-03），电池 50/50；与 host 5HD 守卫同轮联合闭包，非本修复孤立对照（来源平台：310p；证据等级：tool_observed）。

## 失效边界

- **950 实例证据等级为存量迁移记录**（2026-06-22 外部会话，经 OKF 迁移件固定来源链入卡；对本摄入流水线属 agent_reported 性质的既往档案，非本轮轨迹复验）。本轮轨迹只实测核验 310P 实例。
- **310P 修后闭环无孤立对照**：本修复与 host 侧 5HD storage 守卫同窗落地、同次重建复测，50/50 是双修联合闭包；修前非确定漂移历史记载（本卡）与 5HD storage ratio=16.00 布局探针是两个可区分信号，支持双根因并存。
- 310P 非确定性的逐 bit 复现记录（run1/run2/run3 具体数值）未在轨迹留存，信号等级依赖修复注释的实测记载。
- 未验证：双缓冲替代方案；块数 ≥3 时是否需要更强握手；910B/A2/A3 跨代适用性。
- 与 [PB-17](pb_17_ub_aliasing_cross_row_v_mte2_hazard_silent_data_co.md)（跨行别名变体）分卡收录：同危害类、不同触发语境（分块循环重载 vs 行内别名）与签名，不合并。

## 坏实践

- 多块循环重载共享 UB 缓冲时不加 V→MTE2 定序，靠"测试碰巧全绿"当验证。
- 用 MTE2→V 就绪令牌充当反方向保护——方向错了保护不了读侧。
- 见非确定错先怀疑设备/环境：先审内核多块循环的 staging 复用点。

## 误诊

- 310P 实例无归因发散（多漂移判别 → staging 复用点直审 → 栅栏修复 → 非确定消除，机制闭环）。
- 950 存量记录中该缺陷曾以 UB-instrumentation（dump UB→GM-scratch 回读）白盒定案，未走弯路（迁移档案）。

<!-- 迁移自 porter kb/target/ascendc/（PB-47，convert_family_to_okf.py，M1，整档忠实搬运）；2026-11-16 重构为 Runbook 规范结构并并入 310P 第二实例，原卡证据内容（applies_to/verified_on/unverified_on、PB-17/EC-13/P-P106 交叉引用与两段 950 Evidence）全部保留于对应章节。原始交叉引用：PB-17（跨行别名兄弟卡，同 V→MTE2 危害类）、EC-13（HardEvent 同步清单）、P-P106（L-chunk + 并行扫描模式）。confidence/severity/reproduce_count 未升格。 -->
