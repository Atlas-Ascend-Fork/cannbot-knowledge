---
type: Optimization
title: 同步与 Barrier（NPU 三层同步机制）
description: NPU 管道同步（set_flag/wait_flag/pipe_barrier）、跨核同步（sync_block_*）、UnitFlag
  机制、编译器自动同步注入，以及 910_95 Reg-based 与 910B FFTS 的差异；含“本案例未验证某些写读形态下
  barrier 对 DMA 的排序、跨 program 数据可见性需独立验证”的实测记录。
tags: [task.optimization, topic.implementation.synchronization, topic.implementation.pipeline, topic.programming_model.execution_unit.cube, topic.programming_model.execution_unit.vector, topic.implementation.debugging]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Extension_Ops/sync_block.md
  role: primary
created_at: '2026-08-14T00:00:00Z'
updated_at: '2026-09-08T09:05:00Z'
platforms: [a2, '950']
---
# 同步与 Barrier（NPU 三层同步机制）

触发场景：编写 Cube-Vector 协作 kernel（`al.scope`）；`tl.dot` 后紧跟 Vector 后处理需保证数据就绪；多 Block 协作；循环含 `tl.dot` 且循环次数可能为 0；排查 deadlock / barrier timeout / 数据竞争。

## 同步三层架构

```
跨核同步 (Block Sync)：sync_block_set / sync_block_wait / sync_block_all —— 基于 FFTS 或 Reg-based 硬件
管道同步 (Pipe Sync)：set_flag / wait_flag / pipe_barrier —— 同一 Block 内不同 Pipeline 间 Event Flag
UnitFlag 同步：unit_flag_cond / unit_flag_mode —— 嵌入宏操作（如 mmadL1），处理循环可能不执行的依赖
```

## 管道同步（最细粒度）

NPU 多 Pipeline（MTE1/MTE2/MTE3/M/V/FIX）并行执行，有数据依赖时通过 Event Flag 保证顺序。每个 Pipe 有 8 个 Event ID（EVENT_ID0~7），`(set_pipe, wait_pipe, event_id)` 三元组配对。

| 操作 | HIVM IR | 说明 |
|------|---------|------|
| SetFlag | `hir.set_flag` | set_pipe 上置 Flag，通知 wait_pipe 数据就绪 |
| WaitFlag | `hir.wait_flag` | wait_pipe 上等待 Flag |
| PipeBarrier | `hir.pipe_barrier` | 等该 Pipe 所有先前操作完成（重量级） |

典型 Pipe 组合：MTE1→M（L1 加载完通知 Cube）、MTE2→M、M→MTE3（Cube 完通知写回）、M→FIX、M→V。

## 跨核同步（Block Sync）

Triton 层 API（`triton.language.extra.cann.extension`）：

| API | 角色 | 语义 |
|-----|------|------|
| `al.sync_block_set(sender, receiver, event_id)` | 生产者 | "我已完成，你可以读" |
| `al.sync_block_wait(sender, receiver, event_id)` | 消费者 | "等你完成我再读" |
| `al.sync_block_all(mode, event_id)` | 全局屏障 | 所有核心同步到同一点 |
| `al.debug_barrier(sync_mode)` | Vector 内部 | Vector 内部流水线阶段同步 |

参数：`sender`/`receiver` 取 `"cube"`/`"vector"` 且**不能相同**；`event_id` 范围 **0-15**（16 个独立通道）；PIPE 可自动推断（cube→vector：`PIPE_FIX`/`PIPE_MTE2`；vector→cube：`PIPE_MTE3`/`PIPE_MTE2`），也可显式指定。

`sync_block_all` 的 mode：`all_cube` / `all_vector` / `all` / `all_sub_vector`。

SyncBlockMode 枚举（HIVM 层）：ALL_CUBE=0, ALL_VECTOR=1, ALL_SUB_VECTOR=2, BARRIER_CUBE=3, BARRIER_VECTOR=4, ALL=5。

## UnitFlag —— 循环可能不执行的场景

当循环次数可能为 0 时，循环内 set_flag/wait_flag 配对被打破，UnitFlag 通过条件化同步解决。模式：DISABLED(0b00) / ENABLED_WITHOUT_UPDATE(0b10) / ENABLED_WITH_UPDATE(0b11)。

## 自动同步注入（编译器代劳）

HIVM 编译器提供自动同步注入 Pass，**用户通常不需要手写管道同步**：

| Pass | 特点 |
|------|------|
| InjectSync | 启发式，编译快，基本正确 |
| GraphSyncSolver | 图求解，编译慢，同步更优 |

InjectSync 选项：`sync-mode`（NORMAL 插 set/wait_flag；BARRIERALL 插 pipe_barrier，调试用）、`enable-unit-flag`、`assume-alive-loops`（假设循环至少执行一次，简化分析）。

## 代码模式

基本 Cube-Vector 同步：

```python
@triton.jit
def basic_sync_kernel(a_ptr, b_ptr, c_ptr, N):
    with al.scope(core_mode="cube"):
        result = tl.dot(tl.load(a_ptr + tl.arange(0, 128)), tl.load(b_ptr + tl.arange(0, 128)))
        al.sync_block_set("cube", "vector", 0)

    with al.scope(core_mode="vector"):
        al.sync_block_wait("cube", "vector", 0)
        tl.store(c_ptr + tl.arange(0, 128), result * 2.0)
```

Flash Attention 流水线（多 event_id 并行同步）：

```python
with al.scope(core_mode="cube"):
    for start_n in range(0, N, BLOCK_N):
        qk = tl.dot(q, k)
        al.sync_block_set("cube", "vector", 0)
        al.sync_block_wait("vector", "cube", 1)
        pv = tl.dot(p, v)
        al.sync_block_set("cube", "vector", 2)

with al.scope(core_mode="vector"):
    for start_n in range(0, N, BLOCK_N):
        al.sync_block_wait("cube", "vector", 0)
        m_new, l_new, softmax_out = _softmax(qk, m_prev, l_prev)
        al.sync_block_set("vector", "cube", 1)
        al.sync_block_wait("cube", "vector", 2)
        acc = _update_output(pv, softmax_out, acc)

with al.scope(core_mode="cube"):
    al.sync_block_all("all", 0)
```

Vector 内部同步（store 后再 load 同址）：

```python
with al.scope(core_mode="vector"):
    tl.store(out_ptr + offsets, data)
    al.debug_barrier(al.SYNC_IN_VF.VST_VLD)
    loaded = tl.load(in_ptr + offsets)
```

## 910_95 特别注意（Reg-based vs FFTS）

| 特性 | 910B 系列 | 910_95 系列 |
|------|----------|------------|
| 跨核同步机制 | FFTS | Reg-based（寄存器 SetFlag/WaitFlag） |
| ffts_base_addr | 必须设置 | **不需要**（硬件寄存器直传信号） |
| UB 容量 | 192KB（单 buffer）/ 96KB（双） | 248KB（单）/ 124KB（双） |
| L0C 容量 | 128KB | 256KB |
| L0C→UB 通路 | 不支持 | 支持（fixpipe），改变了同步 Pipe 组合 |
| multibuffer 默认 | 开启 | **关闭**，需显式 `multibuffer=True` |
| SIMT 模式 | 不支持 | 支持 |

910_95 的 Reg-based 同步延迟更低，但同步语义与 FFTS 一致。

### 何时需要手动同步

需要：①Cube-Vector 协作（`al.scope`）；②多 Block 全局屏障；③Vector 内部流水线同步（debug_barrier）。
不需要：纯 Vector kernel；简单 load→compute→store；编译器可自动推断依赖的场景。

### 常见陷阱

| 陷阱 | 症状 | 解决 |
|------|------|------|
| Event ID 冲突 | 死锁/数据竞争 | 不相关的同步用不同 ID |
| set/wait 不配对 | barrier timeout | 每个 set 有对应 wait 且参数一致 |
| 循环中同步断裂 | 首次迭代正常后续异常 | UnitFlag 或 `assume-alive-loops` |
| sender == receiver | 编译错误 | 同核心内部用 `debug_barrier` |
| TRITON_ALL_BLOCKS_PARALLEL 与同步冲突 | 死锁 | 有同步操作时不能开该选项 |


## 跨核数据可见性（本案例未验证 barrier 对 DMA 的排序）

> 各类交接形态的通过率、取舍与归因方法见 [单 kernel 单 launch 的可行性体系](single_kernel_feasibility.md)；
> 本节只保留同步语义与可复核探针，避免两处重复维护。

本案例（Ascend950PR，A5 混合 `tl.dot` kernel，Triton-Ascend 3.6，28 核）中，生产者 `tl.store` 后用 `sync_block_all` 同步，消费者仍读到旧值：**该配置下不能把这一次同步当作 GM 交接保证**。

官方 `sync_block_all` 的语义见 [sync_block.md](https://gitcode.com/Ascend/triton-ascend/blob/865691e2e9b656bc58008170207b4108d92e8dd1/docs/zh/triton_api/Extension_Ops/sync_block.md)：它是指定核心类型的跨核同步，用于共享 GM 的 RAW/WAR/WAW；同系列 set/wait 也有各自的生产者/消费者语义。固定版本的上游 lowering 对参与单元传入的是 `PIPE_ALL`。因此本节只记录该探针的观测，不外推为整个 `sync_block_*` 系列不排 DMA。

该配置下的观测（A5，28 核，`P` 为参与 program 数；生产者 bf16 `tl.store` 后 `sync_block_all`，消费者在同步点后读同一段 GM）：
`P=1` 时逐 tile 精确；`P=28` 时消费者读到旧值/错乱。**该探针的原始脚本与逐次记录未归档**，
因此本节只保留验证方法与定性结论，不给通过率、误差幅度等量化数字。

- 试过且**无效**的手段：`sync_block_all("all"/"all_cube")`、生产者同址 read-back、sink store 防 DCE、`multibuffer=False`。
- **按参与单元同步（同一配置下的尝试）**：逐类使用 `all_cube`、`all_vector`、`all_sub_vector` 的方案比单个 `all` 更稳，
  但同属该配置下的观测，需按参与单元与交接形态复核。
- **验证工作区交接**：同一融合实现中，`gl` 与 residual 由 masked store 改为连续整 tile store，并给尾块补齐后，producer→consumer 交接不再稳定错几行。scatter 后同址读回、跨 chunk 累加器整块读回和调整两个消费者顺序也曾用于隔离特定交接问题。这些行为需在同一编译栈和多 chunk shape 下复验，不能视为通用 DMA fence。
- **区分到达与可见性**：见下面「134 MiB 交接探针（归档）」小节。归档探针在 28 program、bf16、134 MiB 工作区上
  两种写法都 10/10 通过（逐轮 28/28），说明"脏工作区复用"本身不足以复现错读；早前记录的 1/10 未能在该归档探针上复现，
  已按归档数据替换，不再保留无法复核的数字。`tl.dot` 与 `while` 共存的探针出现过 `read before first write`；有界 `for` 可绕过该编译问题。轮询耗尽须显式报告失败，不能继续读取。验证时分别记录到达计数和对端读值，并将 NaN 计为失败。
- **设计含义**：先做依赖图分解。保留跨 program 边时，用代表性 tile、尾块及多 chunk 测到达与可见性；交接仍不稳定时再调整数据归属或重算。

## 可复核探针（本卡）：dense 与 atomic 交接

下面两段探针都在 28 个 program、`sync_block_all("all", 0)` 下运行，代码可直接复制；用于判断给定写读形态的交接是否成立。
运行环境：Ascend950PR/957c；驱动 `npu-smi 25.7.rc1.7`；CANN toolkit **9.2.0-beta.2**；triton-ascend 3.6.0；torch_npu 2.14.0；bf16。

```python
import time

import torch
import torch_npu  # noqa: F401
import triton
import triton.language as tl
from triton.language.extra.cann.extension import sync_block_all


@triton.jit
def handoff(buf_ptr, out_ptr, NTILE, TILE: tl.constexpr, NPROG: tl.constexpr):
    pid = tl.program_id(0)
    for t in range(pid, NTILE, NPROG):
        off = t * TILE + tl.arange(0, TILE)
        tl.store(buf_ptr + off, tl.full((TILE,), 1.0, dtype=tl.bfloat16))
    sync_block_all("all", 0)
    src = ((pid + 1) % NPROG) * TILE + tl.arange(0, TILE)   # 读邻 program 的 tile
    v = tl.load(buf_ptr + src)
    tl.store(out_ptr + pid, tl.sum(v.to(tl.float32)))


@triton.jit
def atomic_handoff(buf_ptr, out_ptr, TILE: tl.constexpr, NPROG: tl.constexpr):
    pid = tl.program_id(0)
    off = tl.arange(0, TILE)                                 # 所有 program 同址 atomic 累加
    tl.atomic_add(buf_ptr + off, tl.full((TILE,), 1.0, dtype=tl.bfloat16))
    sync_block_all("all", 0)
    v = tl.load(buf_ptr + off)
    tl.store(out_ptr + pid, tl.sum(v.to(tl.float32)))
```

实测（Ascend950PR/957c、bf16、28 program、`sync_block_all("all", 0)`）：

| 探针 | 工作区 | tile | 结果 |
|---|---|---|---|
| dense 写→sync→邻 program 读回 | 32 MiB | 8192 | **28/28 program 正确** |
| dense 写→sync→邻 program 读回 | 512 MiB | 8192 | **28/28 正确** |
| dense 写→sync→邻 program 读回 | 2048 MiB | 8192 | **28/28 正确** |
| 同址 atomic_add→sync→读回（期望 28×TILE） | 32 MiB | 65536 | **28/28 正确**（值 = 1835008） |
| 同上 | 512 MiB | 65536 | **28/28 正确** |

读法：**dense 整 tile 交接与同址 atomic 累加在 2 GiB 以内都可复核地成立**，与"工作区越大越容易错"没有必然关系。
组内曾在真实 5-phase 工作区（约 10 GiB、多个消费者/多种写读形态并存）观测到消费者读到旧值（NaN/比例下降），
但**该失败未用上面两段探针复现**，因此只作为待复验记录，不写成通用结论；复验时应让探针与失败形态同构
（同写读形态、同消费者数量、同规模）。

交接形态的取舍与阶段门见 [单 kernel 单 launch 的可行性体系](single_kernel_feasibility.md)。

## 混合 `tl.dot` 探针中的跨 program 交接：单个 `all` 与三级屏障对照

在两台 Ascend950PR 上，用 **28 个 program、128×256 bf16 tile、2 个 chunk、整 tile store 加同址读回**后，
比较两种屏障写法。按"该轮全部 program 都对"统计，单个 `all` 在两台机器上各为 **0/10**，
`all_cube → all_vector → all_sub_vector` 在两台机器上各为 **10/10**。这个结果支持在相同配置下把三级链作为候选方案；
复用时请记录实际参与比较的核类型、grid、写读形态和编译栈，并按代表性输入复测数据交接。

| 环境 | 屏障形态 | 每轮正确的 program 数（10 轮） | 干净轮数 |
|---|---|---|---|
| 机器 A（Ascend950PR / A5），torch_npu 2.14.0，triton-ascend 3.6 | `sync_block_all("all")` | 23,23,21,24,17,22,21,19,23,24 | **0/10** |
| 同上 | `all_cube`→`all_vector`→`all_sub_vector` | 28×10 | **10/10** |
| 机器 B（Ascend950PR / A5），torch_npu 2.10.0.post7，triton-ascend 3.6 | `sync_block_all("all")` | 26,24,22,20,26,24,23,24,23,23 | **0/10** |
| 同上 | 三级链 | 28×10 | **10/10** |

**本次对照的固定配置**：`grid = 28`、**整 tile 写**、屏障前同址读回、`NCHUNK = 2`。
本探针**只切换屏障形态**，未单独比较"整 tile vs masked store"，也未开关同址读回（drain）；
因此"masked store 不被排序"和"屏障只保证到达、不保证排空 DMA"这两项**尚待单独验证**，不作为本节的结论。

可复核探针（两个 chunk、drain 常开，只改屏障形态）：

```python
import torch, torch_npu  # noqa: F401
import triton
import triton.language as tl
import triton.language.extra.cann.extension as ext

NPROG, BM, BK, NCHUNK = 28, 128, 256, 2
TILE = BM * BK


@triton.jit
def probe(gl_ptr, chk_ptr, out_ptr, MODE: tl.constexpr, BM: tl.constexpr, BK: tl.constexpr,
          NPROG: tl.constexpr, NCHUNK: tl.constexpr, TILE: tl.constexpr):
    pid = tl.program_id(0)
    rows = tl.arange(0, BM)
    cols = tl.arange(0, BK)
    bad = tl.zeros((1,), dtype=tl.int32)
    for ch in range(0, NCHUNK):
        base = (ch * NPROG + pid) * TILE
        tl.store(gl_ptr + base + rows[:, None] * BK + cols[None, :],
                 tl.full((BM, BK), 1.0, dtype=tl.bfloat16))          # 整 tile store
        tl.store(chk_ptr + pid * NCHUNK + ch,                        # drain：别名读回一列
                 tl.sum(tl.load(gl_ptr + base + rows * BK).to(tl.float32)))
        if MODE == 0:
            ext.sync_block_all("all", 0)
        else:
            ext.sync_block_all("all_cube", 0)
            ext.sync_block_all("all_vector", 0)
            ext.sync_block_all("all_sub_vector", 0)
        src = (ch * NPROG + ((pid + 1) % NPROG)) * TILE
        a = tl.load(gl_ptr + src + rows[:, None] * BK + cols[None, :])
        acc = tl.dot(a, tl.full((BK, BK), 1.0, dtype=tl.bfloat16))
        bad += (tl.sum((acc == float(BK)).to(tl.int32)) != BM * BK).to(tl.int32)
        if MODE == 0:
            ext.sync_block_all("all", 1)
        else:
            ext.sync_block_all("all_cube", 1)
            ext.sync_block_all("all_vector", 1)
            ext.sync_block_all("all_sub_vector", 1)
    tl.store(out_ptr + pid + tl.arange(0, 1), bad)
```

跑法：`ASCEND_RT_VISIBLE_DEVICES=<id> python3 barrier_hier2.py`，`MODE=0` 与 `MODE=1` 各 10 轮，比较"每轮 28 个 program 是否全部通过"。
事件 id 只能取 0–15；同一 id 可在循环中复用。

### 低复杂度案例 + 配置矩阵

案例保持**结构简单**：一个 program 写自己的一块 tile（整块 store）→ drain 读回一列 → 屏障 → 用 `tl.dot` 读邻居那块 tile，
循环 `NCHUNK` 次（覆盖写）；唯一变量是**屏障形态**。参数化版本（`NPROG / BM / BK / NCHUNK`，
`tile = BM×BK` bf16，grid=`(NPROG,)`）：

```python
NPROG, BM, BK, NCHUNK = 4, 16, 64, 2       # 示例；下表给多组配置
TILE = BM * BK


@triton.jit
def probe(gl_ptr, chk_ptr, out_ptr, MODE: tl.constexpr, BM: tl.constexpr, BK: tl.constexpr,
          NPROG: tl.constexpr, NCHUNK: tl.constexpr, TILE: tl.constexpr):
    pid = tl.program_id(0)
    rows, cols = tl.arange(0, BM), tl.arange(0, BK)
    bad = tl.zeros((1,), dtype=tl.int32)
    for ch in range(0, NCHUNK):
        base = (ch * NPROG + pid) * TILE
        tl.store(gl_ptr + base + rows[:, None] * BK + cols[None, :],
                 tl.full((BM, BK), 1.0, dtype=tl.bfloat16))                  # 整块 store
        tl.store(chk_ptr + pid * NCHUNK + ch,                               # drain
                 tl.sum(tl.load(gl_ptr + base + rows * BK).to(tl.float32)))
        if MODE == 0:
            ext.sync_block_all("all", 0)
        else:
            ext.sync_block_all("all_cube", 0)
            ext.sync_block_all("all_vector", 0)
            ext.sync_block_all("all_sub_vector", 0)
        src = (ch * NPROG + ((pid + 1) % NPROG)) * TILE
        a = tl.load(gl_ptr + src + rows[:, None] * BK + cols[None, :])
        bad += (tl.sum((tl.dot(a, tl.full((BK, BK), 1.0, dtype=tl.bfloat16)) == float(BK)).to(tl.int32))
                != BM * BK).to(tl.int32)
        if MODE == 0:
            ext.sync_block_all("all", 1)
        else:
            ext.sync_block_all("all_cube", 1)
            ext.sync_block_all("all_vector", 1)
            ext.sync_block_all("all_sub_vector", 1)
    tl.store(out_ptr + pid + tl.arange(0, 1), bad)
```

实测矩阵（机器 A：Ascend950PR / A5、CANN 9.2.0-beta.2、triton-ascend 3.6.0、torch_npu 2.14.0，每档 10 轮；
"干净"= 该轮全部 program 都对）：

| NPROG | tile (BM×BK) | NCHUNK | `all` 干净轮 | 三级链 干净轮 | 每轮正确数（`all` / 三级链） |
|---|---|---|---|---|---|
| 28 | 128×256 | 2 | **0/10** | **10/10** | 17–24 / 28 |
| 28 | 128×256 | 4 | **0/10** | **10/10** | 15–22 / 28 |
| 16 | 32×128 | 2 | **0/10** | 9/10 | 8–11 / 15–16 |
| 8 | 32×128 | 2 | **0/10** | 9/10 | 4–7 / 7–8 |
| 4 | 16×64 | 2 | **0/10** | **10/10** | 2–3 / 4 |
| 4 | 16×64 | 4 | 0/10 | 0/10 | 2–3 / 3（**都坏，不能判别**） |
| 8 | 32×128 | 1 | 0/10 | 0/10 | 5–7 / 6–7（**都坏**） |
| 4 | 16×64 | 1 | 4/10 | 4/10 | 2–4 / 3–4（**无区别**） |
| 2 | 8×32 | 2 | 6/10 | 0/10 | 1–2 / 1（**反转，勿用**） |

跨机复验（机器 B：Ascend950PR / A5、torch_npu 2.10.0.post7、同 triton-ascend 3.6）：`NPROG=28, tile 128×256, NCHUNK=2`
为 **`all` 0/10（20–26/28）vs 三级链 10/10（28/28）**。

结论与使用边界：
可写成：在已测的 28×128×256（2/4 chunk）、16 或 8 program × 32×128（2 chunk）、以及 4 program × 16×64（2 chunk）这些配置中，
三级链的干净轮数高于单个 `all`。其中 4 program 的 2-chunk 配置也通过了 10/10，**不能由本表要求 grid 满驻**；
同为 4 program 的 4-chunk 配置两种写法都为 0/10，2 program 的 2-chunk 配置则是 `all` 6/10、三级链 0/10。
请按目标配置复测；换栈后若 `all` 通过，只记录该栈和该配置下的结果。

## 同址读回（drain）：可复核对照与结论

**定位**：drain = 生产者 `store` 之后再读回刚写数据的一小部分（别名读，结果写到无人消费的缓冲），再进网格屏障。
本节用**可复核实验（含正对照）**回答两点：drain 是否改变跨 program 交接的正确性；在真实"写未达/未可见"时能否修复。

**实验环境**：单卡 Ascend950PR（A5）、CANN 9.2.0-beta.2、triton-ascend 3.6.0、bf16、28 program、
单 `all` 屏障（`sync_block_all("all", id)`）、每 program 整块 `store` NT 个 8192 元素（16 KiB）tile、
跨 program 读邻居段；每配置 3 轮（小工作区补 5 轮），统计坏元素数与坏 program 数。探针见本节末。

### 对照 1：探针灵敏度（正对照，16.2 MiB）

写者不均衡（偶 program 在写入前多跑一次带依赖的 400 次递推）+ **不加屏障**，每轮统计坏元素数
（探针把延时结果计入写入值；期望值由 **launch 前 host 侧独立参考**（fp32 逐位同构）算出并存入只读张量，读者不读生产者现场写出的结果；见本节末代码）：

| 配置 | 第 1 轮（首读 / 后读） | 第 2 轮 | 第 3 轮 |
|---|---|---|---|
| 无屏障 + 不均衡，drain 关 | **4,218,880 / 51,200** | **4,243,456 / 147,456** | **4,243,456 / 105,728** |
| 无屏障 + 不均衡，drain 开 | **1,941,504 / 0** | **2,048,000 / 0** | **2,068,736 / 0** |
| 同配置 + 单 `all` 屏障，drain 关 | 0 / 0 | 0 / 0 | 0 / 0 |
| 同配置 + 单 `all` 屏障，drain 开 | 0 / 0 | 0 / 0 | 0 / 0 |

读法：
- 无屏障时**首读者稳定读错**（每轮 1.8–4.2M 坏元素）→ 探针具备灵敏度；
- **drain 不修复首读错误**（开 drain 后首读仍 1.8–4.2M）；
- 无屏障且写者不均衡时，开启 drain 后首段仍观测到约 194–207 万坏元素、第二段三轮均为 0；关闭 drain 后两段计数见表；
- 加单 `all` 屏障后，首读/后读全为 0；
- 结论只覆盖"**所测 all 屏障矩阵开关无差异**"：无屏障时 drain 未消除首读错误，但后两轮计数会变化（组内观测）；
  不能据此断言"原子写/顺序本身错误"。

### 对照 2：16 / 128 / 512 MiB 的 drain 开关矩阵（有 `all` 屏障，无写者不均衡）

| 工作区（实际） | drain 关：3 轮坏元素（首读/后读） | drain 开：3 轮坏元素 |
|---|---|---|
| 16.2 MiB（NT=37） | 0 / 0 | 0 / 0 |
| 128.2 MiB（NT=293） | 0 / 0 | 0 / 0 |
| 511.9 MiB（NT=1170） | 0 / 0 | 0 / 0 |

### 对照 3：三级链在本结构下的可用性

同一探针改用 `all_cube → all_vector → all_sub_vector` 三级链：**npuSynchronizeDevice 报 RuntimeError（AI Core error 259）**，
无法取得正确性数据。该结论为**组内观测**（探针随卡给出，可按同一代码复测），不外推到其他结构。

### 结论（按上述实验）

1. **drain 不改变跨 program 交接的正确性**：16.2–511.9 MiB、drain 关/开、首读/后读均为 0 坏元素。
2. **在真实"写未达/未可见"场景（无屏障正对照）中，drain 同样不修复**：无屏障且写者不均衡时，
   开启 drain 后首段仍观测到约 194–207 万坏元素，第二段三轮均为 0；关闭 drain 后两段计数见表。
   因此"同址读回会把挂起的 store/DMA 推落地"在本卡没有可观测证据；不能把 drain 写成首个消费者读旧值的修复手段。
3. 本探针有正对照灵敏度（无屏障可稳定报错），故"0 坏元素"是实测结果而非探针失效。
4. **"错误随相位执行顺序转移"不能单独作为可见性判据**：先排查数据交叉（同一缓冲被多相位写）、索引/边界、
   别名竞争、缓冲生命周期（前一相位覆盖后一相位数据）；确要证明可见性，用本节"无屏障+写者不均衡 vs 有屏障"模板。
5. 三级链在本探针结构下不可用（AI Core error 259），使用前需按目标结构验证；同步语义以 Triton-Ascend API
   与编译栈为准。drain 仍可作**诊断变量**（非必要、非无必要），但"排空 DMA"需另补能观测到达/可见性的对照；
   更大规模（十万级 tile、混合 cube+vector 消费者）按同一模板复测后再下结论。

**可复核探针（本卡数据由它产出；改 `mib` 即改工作区大小）**：

探针要点（对应检视）：
- **延时结果参与实际写入**：递推结果参与写入值；每轮 launch 前，host 用 `_expected_ref` 独立计算
  每个 writer 的期望值并写入 `ref_ptr`，两个读循环使用同一份只读参考；
- 覆盖三种屏障分支（0=不加、1=单 `all`、2=三级链）与两个消费者（屏障后立即读 / 逆序再读一遍）；
- 无屏障 + 写者不均衡是**正对照**（应读出错误）；有屏障时应为 0。

```python
import torch, torch_npu  # noqa: F401
import triton
import triton.language as tl
from triton.language.extra.cann.extension import sync_block_all

NPROG = 28
CHUNK = 8192            # 16 KiB bf16 / tile
DELAY = tl.constexpr(400)      # @triton.jit 内只能引用 constexpr 全局


@triton.jit
def _delay(w):
    acc = w
    for _ in range(0, DELAY):
        acc = acc * 1.0001 + w          # 循环携带依赖，IR 不能折叠
    return acc


@triton.jit
def handoff(buf_ptr, out_ptr, sink_ptr, w_ptr, ref_ptr, SKEW: tl.constexpr, DRAIN: tl.constexpr,
            BARRIER: tl.constexpr, NPROG: tl.constexpr, CHUNK: tl.constexpr,
            NT: tl.constexpr, ROUND: tl.constexpr):
    pid = tl.program_id(0)
    off = tl.arange(0, CHUNK)
    w = tl.load(w_ptr + pid)                              # 运行时标量（非常量）
    expf = tl.full((CHUNK,), ROUND + 1.0, dtype=tl.float32) + tl.full((CHUNK,), w, dtype=tl.float32)
    total = _delay(w)                                     # 400 次带依赖迭代（非常量输入）
    if SKEW and (pid % 2 == 0):                           # 正对照：一半 program 再延迟一次
        total = total + _delay(w * (1.0 + pid.to(tl.float32) * 1e-9))
    tl.store(sink_ptr + pid, total)                       # 运行时结果落到 sink，供邻 program 校验
    val = (expf + tl.full((CHUNK,), total * 1e-3, dtype=tl.float32)).to(tl.bfloat16)
    for t in range(0, NT):
        tl.store(buf_ptr + (pid * NT + t) * CHUNK + off, val)
    if DRAIN:                                             # 同址读回 -> 独立 fp32 sink
        for t in range(0, NT):
            base = (pid * NT + t) * CHUNK
            tl.store(sink_ptr + NPROG + base + off,
                     tl.load(buf_ptr + base + off).to(tl.float32))
    if BARRIER == 1:
        sync_block_all("all", 0)
    elif BARRIER == 2:
        sync_block_all("all_cube", 0)
        sync_block_all("all_vector", 0)
        sync_block_all("all_sub_vector", 0)
    nbr = (pid + 1) % NPROG
    # 期望值来自 launch 前独立参考 kernel 写入的只读张量 ref_ptr，不用生产者现场写出的 sink
    expect = tl.load(ref_ptr + nbr)
    expect = tl.full((CHUNK,), expect, dtype=tl.bfloat16)
    bad1 = 0
    for t in range(0, NT):                                # 首个消费者（正序）
        v = tl.load(buf_ptr + (nbr * NT + t) * CHUNK + off)
        bad1 += tl.sum((v != expect).to(tl.int32))
    tl.store(out_ptr + pid * 2, bad1)
    bad2 = 0
    for t in range(NT - 1, -1, -1):                       # 后置消费者（逆序读）
        v = tl.load(buf_ptr + (nbr * NT + t) * CHUNK + off)
        bad2 += tl.sum((v != expect).to(tl.int32))
    tl.store(out_ptr + pid * 2 + 1, bad2)
    if BARRIER == 1:
        sync_block_all("all", 1)
    elif BARRIER == 2:
        sync_block_all("all_cube", 1)
        sync_block_all("all_vector", 1)
        sync_block_all("all_sub_vector", 1)


def _expected_ref(w_cpu, round_idx, skew):
    """launch 前的独立参考（host、fp32 逐位同构）：为每个 writer 计算其写入值。"""
    import torch
    w = w_cpu.detach().to(torch.float32).cpu()
    acc = w.clone()
    for _ in range(400):
        acc = acc * 1.0001 + w
    if skew:
        pid = torch.arange(w.numel(), dtype=torch.float32, device=w.device)
        w2 = w * (1.0 + pid * 1e-9)
        acc2 = w2.clone()
        for _ in range(400):
            acc2 = acc2 * 1.0001 + w2
        even = (torch.arange(w.numel()) % 2 == 0).to(w.dtype)   # 与 kernel 一致：只对偶 pid 加
        acc = acc + acc2 * even
    val = (round_idx + 1.0) + w + acc * 1e-3
    return val.to(torch.bfloat16)


def run(mib, drain=0, barrier=1, skew=0, rounds=3):
    nt = max(1, round(mib * 2**20 / (NPROG * CHUNK * 2)))
    n = NPROG * nt * CHUNK
    buf = torch.zeros(n, dtype=torch.bfloat16, device="npu")
    sink = torch.zeros(NPROG + n, dtype=torch.float32, device="npu")
    w = torch.full((NPROG,), 0.25, dtype=torch.float32, device="npu")
    out = torch.zeros(NPROG * 2, dtype=torch.int32, device="npu")
    ref = torch.zeros(NPROG, dtype=torch.bfloat16, device="npu")
    for r in range(rounds):
        out.zero_()
        ref.copy_(_expected_ref(w.cpu(), r, skew))
        handoff[(NPROG,)](buf, out, sink, w, ref, SKEW=skew, DRAIN=drain, BARRIER=barrier,
                          NPROG=NPROG, CHUNK=CHUNK, NT=nt, ROUND=r)
        torch.npu.synchronize()
        vals = out.cpu().tolist()
        print("mib=%d nt=%d drain=%d barrier=%d skew=%d round=%d bad_first=%d bad_later=%d"
              % (mib, nt, drain, barrier, skew, r, sum(vals[0::2]), sum(vals[1::2])), flush=True)


def sweep():
    print("== 正对照 / drain / 有屏障（16.2 MiB, 3 轮）==", flush=True)
    for drain in (0, 1):
        for barrier in (0, 1):
            run(16, drain=drain, barrier=barrier, skew=1, rounds=3)
    print("== 尺寸矩阵（有屏障, drain 0/1, 3 轮）==", flush=True)
    for mib in (16, 128, 512):
        for drain in (0, 1):
            run(mib, drain=drain, barrier=1, skew=0, rounds=3)
    print("== 三级链（单次；本结构下实测 AI Core error 259）==", flush=True)
    run(16, drain=0, barrier=2, skew=0, rounds=1)


if __name__ == "__main__":
    sweep()
```

**本节结论的边界**（按检视收窄）：
- 本卡数据只能说明"**所测 drain 开关在该结构下无差异**"；
- "无屏障 + 写者不均衡"可读出错误，说明**该对照能暴露未达/未可见**，但不能据此区分"消费者先到"与"写未落地"；
- 三级链在该结构下的 AI Core 错误属**组内观测**（探针已随卡给出，可按同一代码复测），不外推到其他结构。

## 首个消费者读旧值的判别（早期探针，1 chunk）

两 phase 稠密交接在最小形态下**测不出错读**，因此"消费者读到旧值"不能直接归因于 barrier 语义。
下面这段探针同时测"barrier 后立刻读（首个消费者）"与"延后再读（后置消费者）"，并带 4 个抑制 load 提升的变体：

```python
import torch, torch_npu  # noqa: F401
import triton
import triton.language as tl
from triton.language.extra.cann.extension import sync_block_all

NPROG = 28


@triton.jit
def handoff(buf_ptr, first_ptr, later_ptr, ROUND, TILE: tl.constexpr,
            NPROG: tl.constexpr, MODE: tl.constexpr):
    pid = tl.program_id(0)
    off = tl.arange(0, TILE)
    tl.store(buf_ptr + pid * TILE + off, tl.full((TILE,), ROUND + 1.0, dtype=tl.bfloat16))
    sync_block_all("all", 0)
    src = ((pid + 1) % NPROG) * TILE
    if MODE == 1:                                  # 用 atomic 返回值制造跨 barrier 依赖
        dep = tl.atomic_add(first_ptr + NPROG, 1)
        v = tl.load(buf_ptr + src + off + (dep - dep))
    elif MODE == 2:
        v = tl.load(buf_ptr + src + off, cache_modifier=".cg")
    elif MODE == 3:
        v = tl.load(buf_ptr + src + off, volatile=True)
    else:
        v = tl.load(buf_ptr + src + off)
    tl.store(first_ptr + pid, tl.sum((v == ROUND + 1.0).to(tl.int32)))
    acc = tl.zeros((1,), dtype=tl.float32)
    for _ in range(0, 64):
        acc += 1.0
    v2 = tl.load(buf_ptr + src + off + tl.sum(acc).to(tl.int32) * 0)
    tl.store(later_ptr + pid, tl.sum((v2 == ROUND + 1.0).to(tl.int32)))
```

实测（Ascend950PR/957c、CANN 9.2.0-beta.2、triton-ascend 3.6.0、bf16、tile=8192、28 program、每变体 4 轮）：

| 变体 | 首消费者正确 program 数（4 轮） | 后置消费者 |
|---|---|---|
| 纯 `sync_block_all("all",0)` | 28 / 28 / 28 / 28 | 28 / 28 / 28 / 28 |
| + atomic 返回值依赖 | 28 / 28 / 28 / 28 | 28 / 28 / 28 / 28 |
| + 载入 `.cg` | 28 / 28 / 28 / 28 | 28 / 28 / 28 / 28 |
| + 载入 `volatile=True` | 28 / 28 / 28 / 28 | 28 / 28 / 28 / 28 |

读法：**最小两 phase 稠密交接（含"首个消费者"位置）在本栈稳定通过**。若真实算子出现"首个消费者读旧值"，
说明触发条件不在"barrier + 一次读取"本身，需按同构矩阵（写读形态 × 消费者数 × 规模）逐轴定位；
这 4 个变体都可直接复跑，用来判断"是可见性问题"还是"别处（布局/索引/竞争）"的问题。

## 134 MiB 交接探针（归档）

工作区 = **134 MiB**（`134 * 1024 * 1024` B = 140,509,184 B；bf16 共 70,254,592 元素），
28 program 各写 `SEG = 70,254,592 // 28 = 2,509,092` 元素（按 `CH = 32,768` 分块；实际分配
`SEG * 28 = 70,254,576` 元素，余 16 个元素不参与）。两次 `sync_block_all("all", 0/1)` 后读邻 program 段，
检查是否全部为本轮新值；每组 10 轮。

```python
import torch
import torch_npu  # noqa: F401
import triton
import triton.language as tl
from triton.language.extra.cann.extension import sync_block_all

NPROG, ELEMS, SEG, CH = 28, 134 * 1024 * 1024 // 2, (134 * 1024 * 1024 // 2) // 28, 32768


@triton.jit
def handoff(buf_ptr, out_ptr, ROUND, SEG: tl.constexpr, NPROG: tl.constexpr,
            CH: tl.constexpr, RESET: tl.constexpr, DELAY: tl.constexpr):
    pid = tl.program_id(0)
    base = pid * SEG
    for c in range(0, SEG, CH):
        idx = c + tl.arange(0, CH)
        msk = idx < SEG
        if RESET:
            tl.store(buf_ptr + base + idx, tl.full((CH,), float("nan"), dtype=tl.bfloat16), mask=msk)
    sync_block_all("all", 0)
    for c in range(0, SEG, CH):
        idx = c + tl.arange(0, CH)
        msk = idx < SEG
        tl.store(buf_ptr + base + idx, tl.full((CH,), ROUND + 1.0, dtype=tl.bfloat16), mask=msk)
    sync_block_all("all", 1)
    if DELAY:
        acc = tl.zeros((1,), dtype=tl.float32)
        for _ in range(0, DELAY):
            acc += 1.0
        tl.store(out_ptr + NPROG + pid, tl.sum(acc).to(tl.int32))
    nbase = ((pid + 1) % NPROG) * SEG
    ok = 0
    for c in range(0, SEG, CH):
        idx = c + tl.arange(0, CH)
        msk = idx < SEG
        v = tl.load(buf_ptr + nbase + idx, mask=msk, other=float("nan"))
        ok += tl.sum((v == ROUND + 1.0).to(tl.int32))
    tl.store(out_ptr + pid, ok)


def run(reset, delay, rounds=10):
    buf = torch.zeros(SEG * NPROG, dtype=torch.bfloat16, device="npu")
    out = torch.zeros(2 * NPROG, dtype=torch.int32, device="npu")
    detail = []
    for r in range(rounds):
        handoff[(NPROG,)](buf, out, r, SEG=SEG, NPROG=NPROG, CH=CH, RESET=reset, DELAY=delay)
        torch.npu.synchronize()
        detail.append(int((out[:NPROG].cpu() == SEG).sum()))
    print("reset=%s delay=%s pass=%d/%d per_round=%s"
          % (reset, delay, sum(1 for x in detail if x == NPROG), rounds, detail))


run(reset=False, delay=False)   # A: 复用脏工作区，只靠屏障
run(reset=True, delay=4096)     # B: 每轮 NaN 重置 + 写后有限延时
```

实测（Ascend950PR/957c、驱动 `npu-smi 25.7.rc1.7`、CANN toolkit 9.2.0-beta.2、triton-ascend 3.6.0、
torch_npu 2.14.0、bf16、10 轮）：

| 写法 | 通过轮数 | 每轮正确 program 数 |
|---|---|---|
| A：复用脏工作区 + 两次 `sync_block_all` | **10/10** | 28, 28, 28, 28, 28, 28, 28, 28, 28, 28 |
| B：每轮 NaN 重置 + 写后 4096 次有界延时 | **10/10** | 28, 28, 28, 28, 28, 28, 28, 28, 28, 28 |

读法：**脏工作区复用本身不足以复现错读**——在 134 MiB、28 program、稠密整段写下，两种写法都 10/10。
要复现错读需要更接近真实算子的形态（多消费者、稀疏/atomic 写、多 phase 同时驻留），
见本卡前面的记录与 `multi_output_gemm_chain_fusion` 的取证表。

## 参考

官方源码参考（链接已锁定 2026-08-17 上游 HEAD；行号锚点继承自源文档，上游演进后可能漂移）：

- [HIVMSynchronizationOps.td](https://gitcode.com/Ascend/AscendNPU-IR/tree/d2a6661365ef65ca738cb66299449b2740c857eb/bishengir/include/bishengir/Dialect/HIVM/IR/HIVMSynchronizationOps.td)
- [core.py](https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/third_party/ascend/language/cann/extension/core.py)
