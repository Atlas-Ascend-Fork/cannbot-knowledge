---
type: Runbook
title: "pass1 消耗 C/D 事件不回填，多 chunk 首量子悬挂"
description: "两趟结构里 pass1 每量子 Wait 了 MTE3_MTE2/MTE3_V，却只在 pass2 回填 SetFlag；chunk 数≥2 时下一 chunk 首量子等不到事件，aicore timeout 507014（chunk=1 恰好看不出来）。"
tags: [task.debugging, topic.implementation.synchronization, topic.precision]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/SetFlag_WaitFlag_ISASI.md
    role: primary
created_at: "2026-10-28T09:52:17Z"
updated_at: "2026-11-02T07:57:34Z"
platforms: ["310p"]
---

# pass1 消耗 C/D 事件不回填，多 chunk 首量子悬挂

## 现象

一个变长 softmax 反传内核按"两趟 + chunk 切分"实现：pass1 逐序列累加统计量，pass2 按 flat 量子重读并逐行写出；chunk 之间复用 UB 缓冲，用 `MTE3_MTE2`（保护 MTE2 引擎与输出缓冲覆写）与 `MTE3_V`（保护 V 管读）两对事件隔离。单 chunk 用例能跑（`err=1.846e-02`），一旦 chunk 数变成 2，用例直接挂死并报硬件超时：

```
Message info[0]:RTS_HWTS: Aicore timeout, slot_id=18, stream_id=3, task_id=3
error code is 507014 ... aicore timeout ... fault kernel_name=<generic>_310p
```

同一份代码在 chunk=1 时完全正常，说明不是算子逻辑错，而是事件账目在"跨 chunk"这条路径上不闭合。场景：kernel 直调、Ascend310P3（dav-m200）、CANN 9.1.0。

## 适用场景

- 工程形态：kernel 直调；多 chunk / 两趟（统计+写出）结构，UB 缓冲跨阶段复用。
- API 路径：`SetFlag/WaitFlag<HardEvent::MTE3_MTE2>`、`<HardEvent::MTE3_V>`、`<HardEvent::V_MTE2>`，事件为计数型。
- 验证过的平台与 CANN 版本：Ascend310P3（DAV_2002 / dav-m200）+ CANN 9.1.0；未在其他平台实测。
- 适用粒度：`platform_wide`（所有"生产者/消费者跨 chunk 复用缓冲"的事件账目）。
- 路线优先级：`recommended_fastpath`（在 pass1 每量子对称回填 C/D）。
- 明确不适用 / 未验证场景：chunk 数恒为 1 或每 chunk 重新分配缓冲的实现不触发本卡。

## 根因

事件是**计数型信号量**：一个 `WaitFlag` 消耗一次 `SetFlag`。本内核里：

- 两个守卫各管一边：`firstQuant` 只豁免**全核首个量子**对 `evE`（V_MTE2）的等待（此前无任何 SetFlag）；C/D 的等待由 `mte3Armed` 守卫——首个 pass2 量子结束前 C/D 从未被 Set，等它必悬挂，所以在那之前 pass1/pass2 都不 Wait C/D；
- `SetFlag<MTE3_MTE2>(evC)` / `SetFlag<MTE3_V>(evD)` 只写在 **pass2 的量子末尾**（写完才置 `mte3Armed = true`）；
- 于是 chunk≥2 起，pass1 的量子在 `mte3Armed` 为真时**消耗**一次 C/D（保护 MTE2 引擎与输出缓冲覆写），但 pass1 末尾只回填 `evE`、不回填 C/D——每量子净欠一账；
- 这笔欠账不需要等很久：chunk1 的 pass1 首量子消耗掉上一 chunk pass2 留下的最后一对 C/D 之后，**下一个等 C/D 的量子**（同 pass1 的后续量子，或本 chunk pass2 的首量子）就再也等不到 → aicore timeout 507014。

为什么 chunk=1 看不出来：整个 chunk 内 C/D 的账目只在 pass2 内部自洽（Wait 一个、回填一个），pass1 从不等 C/D（`mte3Armed` 尚为假），欠账路径完全没有被走到。

## 解决配方

修复点：pass1 每个量子结束时，若"上一轮 pass2 已经 arm 过 C/D"（`mte3Armed`），就把本量子消耗的那一份补回去，使账目对称：

```cpp
                SetFlag<HardEvent::V_MTE2>(evE);
                if (mte3Armed) {
                    // 账目对称：本量子消耗了 C/D（护 MTE2 引擎与 oF 覆写），
                    // 必须回填，否则下一 chunk pass2 首量子 Wait(evC) 悬挂
                    SetFlag<HardEvent::MTE3_MTE2>(evC);
                    SetFlag<HardEvent::MTE3_V>(evD);
                }
            }
```

函数级说明：插入位置在 pass1 内层循环"每量子结束"处、紧接原有的 `SetFlag<V_MTE2>(evE)` 之后；**等待与回填使用同一个守卫 `mte3Armed`**（`firstQuant` 只豁免全核首个量子对 evE 的等待，不参与 C/D 账目），两侧对称才构成"每个 Wait 都有对应 Set"的闭环。守卫不同侧是本卡缺陷的镜像：只给等待加守卫、不给回填加，账目照样欠。

## 设计决策

- 选择"在 pass1 每量子补回 C/D"而不是"把 pass1 的 Wait 删掉"：pass1 的 Wait 是必要的（它要等上一轮 pass2 的 MTE3 真正读完输出缓冲，否则会覆写）；删掉会引入真实竞态。
- 没有把 C/D 改成一次性 arm、全生命周期只 Wait 一次：事件是计数的，一次性 arm 无法表达"每量子一次"的复用节奏。
- 用 `mte3Armed` 而不是无条件补：首个 chunk 的 pass1 并未消耗 C/D，无条件补会让下一轮多一个 Set（事件悬挂方向反转）。
- 等待侧与回填侧必须用**同一**守卫：等待带守卫而回填不带（或反之）都会造成"消耗数 ≠ 回填数"的单侧欠账/过账；示意代码若丢掉等待侧守卫，还会凭空显得首 chunk 第二量子必挂——真实源码两侧同守卫，欠账只出现在跨 chunk 路径。

## 系统信息

- 工具链：CANN 9.1.0，Ascend310P3（dav-m200）；kernel 直调 + torch 扩展，`BUILD_OK: build/lib<generic>_ops.so`。
- 涉及文件：`kernel/<generic>.cpp`（pass1/pass2 事件账目）；定向探针跑 mc=1/mc=2 对比。

## 完整代码

改前（源码逐字，仅省略与事件无关的计算体：等待带 `mte3Armed` 守卫，回填没有——等待与补事件不对称）：

```cpp
                    if (firstQuant) {
                        firstQuant = false;
                    } else {
                        // 三通道全等：上一量子可能是 pass2（MTE3 读 oF/r16）
                        // 或 pass1（V 读 raw/dF/yF），覆写 raw/dF 与 V 写 oF
                        // 均需护
                        WaitFlag<HardEvent::V_MTE2>(evE);
                        if (mte3Armed) {
                            WaitFlag<HardEvent::MTE3_MTE2>(evC);
                            WaitFlag<HardEvent::MTE3_V>(evD);
                        }
                    }
                    loadQuant(s, rows);
                    // … 统计 …
                    SetFlag<HardEvent::V_MTE2>(evE);
                    // ✗ mte3Armed 时上面消耗了 C/D，此处只回填 evE → 跨 chunk 欠账
        // ---- pass2: 逐量子写出（同结构守卫，末尾三者全回填）----
                if (firstQuant) {
                    firstQuant = false;
                } else {
                    WaitFlag<HardEvent::V_MTE2>(evE);
                    if (mte3Armed) {
                        WaitFlag<HardEvent::MTE3_MTE2>(evC);
                        WaitFlag<HardEvent::MTE3_V>(evD);
                    }
                }
                loadQuant(s, rows);
                // … 写出 …
                storeQuant(s, rows);
                SetFlag<HardEvent::MTE3_MTE2>(evC);
                SetFlag<HardEvent::MTE3_V>(evD);
                SetFlag<HardEvent::V_MTE2>(evE);
                mte3Armed = true;
```

改后（源码逐字，修复点唯一：pass1 量子末尾补上与等待同守卫的回填）：

```cpp
                    if (firstQuant) {
                        firstQuant = false;
                    } else {
                        WaitFlag<HardEvent::V_MTE2>(evE);
                        if (mte3Armed) {
                            WaitFlag<HardEvent::MTE3_MTE2>(evC);
                            WaitFlag<HardEvent::MTE3_V>(evD);
                        }
                    }
                    loadQuant(s, rows);
                    // … 统计 …
                    SetFlag<HardEvent::V_MTE2>(evE);
                    if (mte3Armed) {
                        // 账目对称：本量子消耗了 C/D（护 MTE2 引擎与 oF
                        // 覆写），必须回填，否则下一 chunk pass2 首量子
                        // Wait(evC) 悬挂
                        SetFlag<HardEvent::MTE3_MTE2>(evC);
                        SetFlag<HardEvent::MTE3_V>(evD);
                    }
```

## 预防

- 事件账目按"每个 Wait 必有对应 Set"逐条对账；新增 Wait 时同一提交里补上对称 Set。
- 两趟结构的验收用例必须至少覆盖 chunk=2；chunk=1 不能作为跨轮账目的验收。
- 守卫变量（`firstQuant`/`mte3Armed`）的置真时机写成注释，避免后续调整顺序时反向悬挂。

## 验证信号

- 修复前（chunk 数≥2）：`RTS_HWTS: Aicore timeout, slot_id=18, stream_id=3, task_id=3`、`error code is 507014 ... fault kernel_name=<generic>_310p`（来源平台：310P；证据等级：tool_observed）。
- 修复前（chunk 数=1）：单 chunk 用例 `err=1.846e-02` —— 同代码同数据，仅 chunk 数不同（来源平台：310P；证据等级：tool_observed）。
- 修复后（chunk 数=2）：两 chunk 用例 `err=1.889e-04`、`err=9.529e-04`（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 只适用于"事件按量子/轮次计数复用"的结构；若改用每 chunk 重建缓冲或改用 `PipeBarrier<PIPE_ALL>`，本卡的账目不再需要（但代价不同，未实测）。
- `mte3Armed` 的置真时机必须严格是"首个 pass2 量子结束后"；提前置真会让 pass1 提前进入"等 C/D"的分支而无人回填，悬挂点前移。
- 未验证：多核并发（每核独立事件 id）下是否还有跨核共享资源的账目；本轨迹的 mc 指 chunk 数而非核数。
- **未决项（优先）**：507014 的具体触发条件（是 Wait 永不满足导致的看门狗，还是硬件队列满）未在机制层确认；本卡结论来自"chunk=1 通过 / chunk=2 超时 / 补 C/D 后通过"的对照。

## 坏实践

- 用 chunk=1 的用例验收两趟结构：跨轮账目的错误恰好在轮数为 1 时不可见。
- 只在一处补 SetFlag（例如只补 evC）就收工：C/D 两个方向各自独立计数，缺一个仍会悬挂。
- 把 507014 当环境/设备问题重试：本例是确定性的账目错误，重试只会重复超时。

## 误诊

- 误诊（agent_reported）：先按"死锁"排查了 `firstQuant` 守卫（怀疑首个量子的免等逻辑让初始化时的 `SetFlag` 变成双置位），并做了一版"去掉初始化 SetFlag"的改动；该改动没有解决超时，后来定位到真正原因是 pass1 不回填 C/D。
- 误诊（agent_reported）：还一度因为探针只打印尾部（`tail -16`）把"用例逐条通过"误读成"整体挂死"；后续放开打印才看到真实进度。
