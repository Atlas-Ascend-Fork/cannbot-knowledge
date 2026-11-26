---
type: Optimization
title: 单 kernel 单 launch 的可行性体系（门、交接形态、归因、预算与取证）
description: 单 kernel/单 launch 的可行性判定、正确性收敛路径（跨 program 交接与原子写可见性）、性能预算与优化顺序（相位屏障开销、UB 预算与 tile、重复计算、稀疏项代价模型与行块归属折叠）。
  失败归因的同构矩阵、并行度下限估算、共 phase 的 UB 预算表、launch 计数测法、融合税分解与回退记录模板。
tags: [task.optimization, topic.implementation.pipeline, topic.memory, topic.implementation.synchronization]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/865691e2e9b656bc58008170207b4108d92e8dd1/docs/zh/triton_api/Extension_Ops/sync_block.md
  role: primary
- resource: https://gitcode.com/Ascend/triton-ascend/blob/865691e2e9b656bc58008170207b4108d92e8dd1/docs/zh/triton_api/Linear_Algebra_Ops/dot.md
  role: supporting
created_at: '2026-11-24T00:00:00Z'
updated_at: '2026-11-24T00:00:00Z'
platforms: ['950']
---

# 单 kernel 单 launch 的可行性体系

本卡把"这个算子能不能单 launch"从一句结论拆成**可执行的判定体系**：先过阶段门，再按交接形态取证，最后才允许回退。
交付判定本身仍用 [多输出 GEMM 链的融合与单 launch 化](multi_output_gemm_chain_fusion.md) 的三分支表；
回退多 kernel 只是"待确认的替代方案"，验收状态仍为未通过。

## 0. 实验环境

本卡所有数字都在同一台机器、同一编译栈上取得：

| 项 | 值 |
|---|---|
| 硬件 | Ascend950PR（Chip Version V100，`957c`），28 AI core / 56 vector core，UB 248 KB，HBM 86,016 MB |
| 驱动 / 固件 | `npu-smi 25.7.rc1.7`（Chip Version V100 / `957c`） |
| CANN toolkit | **9.2.0-beta.2**（`/usr/local/Ascend/cann-9.2.0-beta.2`） |
| Python / OS | 3.10.22 / Linux 6.8.0-149-generic x86_64 |
| PyTorch / torch_npu | 2.14.0+cpu / 2.14.0 |
| Triton | triton-ascend 3.6.0 |
| dtype / 并发 | bf16；28 program（`grid=(28,)`），`sync_block_all("all", 0/1)` |
| 复跑方式 | `ASCEND_RT_VISIBLE_DEVICES=<id> python3 <探针>.py`，每个测点 5–10 轮，逐轮记录"正确 program 数" |

**A2（910B）未验证**；换 SoC/编译栈时需按本卡探针重跑后再引用。

## 1. 分阶段可行性门

不要直接写全融合；按下列顺序逐阶段加，每阶段留证据，失败时**回退到上一阶段**而不是直接放弃单 launch：

| 阶段 | 结构 | 通过判据 | 失败时的动作 |
|---|---|---|---|
| 0 | 多 kernel 基线 | 精度全过 + 每 case launch 计数明确 | 先修正确性 |
| 1 | 2 phase 单 kernel（一个交接边） | 该边两侧逐 case 精度全过；交接探针同构通过 | 只调这一条边：形态或归属 |
| 2 | 3 phase（两条边） | 同上 + 中间量复用/尾块覆盖 | 定位是哪条边坏，不整体放弃 |
| 3 | 全 phase | 全部 case 精度 + launch 契约 | 记 `contract_conflict` 前必须完成第 2 节的形态清单 |

**门的关键**：阶段 1 的探针要**与真实交接同构**（同写读形态、同消费者数、同工作区规模），否则"小探针过、大全错"无法归因。

## 1.5 单 launch 正确性收敛路径（跨 program 交接）

**问题形态（通用）**：多相位单 kernel 中，某相位把稀疏/累加项以原子写或普通写写进跨 program 共享的中间量，
后续相位（首个消费者）可能读到旧值；把消费者顺序交换后，异常会迁移到另一个输出。
**注意**：顺序交换只说明"缺陷跟着消费者位置走"，**不能证明原子写本身不可用**；本卡只把"所测结构下观察到读旧值"作为现象。

**可复核的最小探针**：见 `sync_and_barrier.md` 的"跨 program 交接"探针（固定版本、可执行、逐轮输出；
读者以**独立参考张量**为期望值，不用生产者现场写出的结果做期望）。本节的后续表格为**组内观测**：
原始探针脚本未随知识卡归档，无法按同版本重建；引用时请按"组内观测"对待，不用于单因子归因。

**组内观测（环境：950PR 级单卡、CANN 9.2.0-beta.2、triton-ascend 3.6.0、torch_npu 2.14.0、bf16、28 program）**：

| 交接形态 | 观测（组内观测） |
|---|---|
| 中间量稠密整 tile store→load（对照） | 与独立参考一致（0 坏元素） |
| 中间量 atomic_add → 首个消费者读 | 本组结构下匹配率约 0.92（容差=1e-2 相对误差；分母=该输出全部元素；初始化为上一轮写入值；索引冲突=多个 program 对同一中间元素原子累加） |
| 交换两个消费者顺序 | 异常从一路输出迁移到另一路 |
| 加 drain（生产者同址读回） | 本组结构下无明显改善 |
| 读者延后（额外向量计算） | 本组结构下无明显改善 |
| 重复三级屏障 | 无变化 |

**结论与收敛顺序**（经验性，优先试结构对齐）：
1. **优先"写者与消费者按行块归属对齐"**：让稀疏/累加项只折叠进**写者自己拥有的中间量行块**（同 program 写→读），
   下游相位再稠密 `store`→`load` 消费；这是本组结构下最先奏效的改造方向。
2. 中间量保持稠密 `store`→`load`；尽量不做"跨 program 写中间量 → 立刻被首消费者读"的交接。
3. 稀疏/累加项也可以只 `atomic_add` 到**最终输出**（输出只被写、不被后续相位当输入读）。
4. drain / 延迟 / 交换顺序 / 重复屏障只作**诊断手段**，不计为结构改造，也不作为"原子写不可用"的判据。
5. 若上述结构都无法通过全量验收，回到"跨 program 交接形态谱"逐边定位，而不是整体放弃。

## 1.6 单 launch 性能预算与优化顺序

**问题形态（通用）**：正确性达标后，单 launch 版比同结构多 kernel 版慢一个数量级。

**可复核探针**：
1) 同一计算分别实现为「多 kernel + fused epilogue」与「单 launch（相位数≥4）」；
2) 每个验收 case 测单次耗时，分别测框架实现、多 kernel 版、单 launch 版；
3) 记录每 case 的毫秒数与相对框架加速比，汇总 geomean/min；
4) 对照变量：相位屏障数量（1 vs 4）、tile 尺寸（大/小）、消费者是否重复计算。

**组内观测（14 个验收用例；原始计时记录未随卡归档）**：

| 实现 | geomean（相对框架） | min | 说明 |
|---|---|---|---|
| 多 kernel + fused epilogue | **≈1.35×** | ≈0.99 | 每相位独立 kernel，可用大 tile |
| 单 launch（多相位 + 4 次三级屏障） | **≈0.030×** | ≈0.013× | 总耗时 119.7 s vs 框架 2.9 s（≈41× 慢；仅作案例背景，不作归因） |

**结构性原因（逐项可复测；与 §5、§7 对应）**：
- **tile 缩水**：多相位共享 UB（§5）→ 单 kernel 的 tile/流水深度下降（§7 的 "UB 降级" 项）；
- **相位屏障**：每次"全核屏障链"= 全核停顿，相位数 × 屏障数直接叠加，cube/vector 无法跨相位流水；
- **重复计算**：为绕开可见性问题让消费者各自计算中间量 → 工作量成倍（见 §1.5）；
- 编译参数（num_stages/num_warps）、CV 流水、padding、标量退化等未调时还会继续放大差距
  （按"性能优化"主题检索对应知识卡；若带平台过滤无命中，去掉平台过滤再检索一次并记录原因）。

**稀疏项放置的代价模型（先算再改；只做数量级判断，单因子归因需对照测量）**：

记号：`M`=行数，`K`=每行稀疏项数，`H`=被稀疏项更新的一路中间量列数，`V`=另一路中间量列数。
- `E = M·K`：稀疏更新总数（每个稀疏项次）。
- `R`：消费者对同一中间量元素的**重复消费次数**（由实现决定；例如按 `H` 分块消费时，一个项被每块各扫一次，
  `R ≈ H/BN` 或由消费者循环结构给出，需在实现里数出来）。
- `b_r`/`b_w`：单次读/写字节（bf16=2 B，fp32=4 B）。

两条路线的量级：
| 放置 | 访存/累加量级 | 额外工作 |
|---|---|---|
| 消费者里做（gather / 逐项 atomic 到输出） | `≈ E·R·(b_r + b_w)`（同一项被重复处理 R 次） | 无额外工作区 |
| 按行块归属折叠进中间量，再稠密消费 | `≈ E·(b_r + b_w)` + 中间量整体回写一次 `≈ M·H·b_w` | 多一次中间量写回/拷贝 |

判据：先数出 `R`（消费者分块数/循环次数），再比较 `E·R` 与 `E + M·H` 的量级差；`R ≫ 1` 时消费者侧随 `R` 线性放大，
行块归属折叠把重复消费变成一次。**不要用整算子总耗时直接归因**：整算子总时还含 tile 缩小、屏障、重复计算等，
只有在固定其他变量、**单独改变稀疏项放置策略**的对照测量里，差异才能归到放置策略上。
（本卡曾观察到某案例整算子总耗时约为框架实现的 41 倍，但那是整算子口径，**不作为**本模型的归因证据。）

**优化顺序（先结构、后参数）**：
1. **先保 tile**：按相位峰值重新分配 UB（跨相位复用同一块缓冲、把可延迟的转换/拷贝移出主相位），不要让 4 个相位平分预算；
2. **减少相位与屏障**：能在同一相位内完成的计算不要拆成两个相位；屏障只放在真正跨 program 交接处；
3. **消除重复计算**：中间量做一次、稠密交接，避免消费者自包含导致重复；
4. **再调参数**：tile/num_stages/num_warps autotune、CV 流水、尾块 padding、标量寻址（按性能主题检索对应知识卡）。

**判据**：单 launch 相对多 kernel 的耗时比 ≥10× 时，优先怀疑 1–3 三项结构问题，不要先调参数；
三项都成立仍不可接受时，记录"单 launch 性能不可行"的可复核数据（本表即模板）并交用户决策。

## 2. 跨 program 交接形态谱（全部可复核）

同一台机器上、28 program、`sync_block_all("all", 0)`，实测：

| 形态 | 机制 | 需要 barrier | 实测 | 探针位置 |
|---|---|---|---|---|
| 稠密整段写→读邻段 | 整段 `tl.store`，消费者整段读 | 是 | **10/10 轮**（32 / 512 / 2048 MiB） | [sync 卡](sync_and_barrier.md) |
| 脏工作区复用 | 不重置，直接覆盖写再读 | 是 | **10/10 轮**（134 MB） | [sync 卡](sync_and_barrier.md) |
| 同址 atomic 累加 | 多 program 对同一段 `atomic_add` | 是 | **10/10 轮**（32 / 512 MiB） | [sync 卡](sync_and_barrier.md) |
| masked 散列跨段 | `pos=(i*7+pid)%TILE` 写邻居段，各读自己段 | 是 | **5/5 轮**（16 KB tile） | 本卡下方 |
| 写者=消费者 | 同一 program 写自己的段并消费 | **否** | **5/5 轮**（16 KB tile） | 本卡下方 |
| **分核类型屏障链** | `all_cube`→`all_vector`→`all_sub_vector`（同址读回常开） | 是（三级） | 本次 28 program / 128×256 bf16 / 2 chunk / 整 tile store + 同址读回：两机各 **10/10**，单个 `all` 各 **0/10** | [sync 卡](sync_and_barrier.md) |

**计数口径**：`@triton.jit` 函数个数 ≠ launch 次数。被 kernel 内联调用的辅助函数（舍入、换算等）也带
`@triton.jit` 装饰，但不产生额外 launch。判别"单 launch"应以**每个验收 case 实际执行的目标路径与运行时设备
launch 次数**为准；**源码静态启动点只用于排查**——它可能多于实际 launch（`if/else` 各一个启动点，一次调用只命中一支），
也可能少于实际 launch（循环里同一启动点反复执行）。计数范围沿用交付契约的约定（含约定计入的独立清零/准备 kernel）。

> 参考手段：若上述形态在**真实规模化实现**（数百 MB 工作区、每 program 多次 store、多相位覆盖同一工作区）中
> 仍出现读到旧值，可先试「同址读回（drain）」——它是可选诊断变量（非必要、非无必要），
> 但本卡的**可复核对照**显示它在 0.9–56 MiB（含 224 MiB 复核）内**开/关都不改变正确性**，
> 因此不要把它当作"必然修复"的手段；顺序敏感时先排查数据交叉、索引/边界、别名竞争与缓冲生命周期，
> 见 [sync 卡](sync_and_barrier.md) 的正对照与结论。

读法：**各行结果限于各自的测试条件**；三级链可在同构场景下作为候选，跨配置以复测为准。
复用这些形态时请同时记录：参与比较的核类型、grid、写读形态、编译栈，并按代表性输入复测。

```python
import torch, torch_npu  # noqa: F401
import triton
import triton.language as tl
from triton.language.extra.cann.extension import sync_block_all

NPROG = 28


@triton.jit
def scatter_cross(buf_ptr, out_ptr, TILE: tl.constexpr, NPROG: tl.constexpr):
    pid = tl.program_id(0)
    dst = ((pid + 1) % NPROG) * TILE
    i = tl.arange(0, TILE)
    pos = (i * 7 + pid) % TILE
    tl.store(buf_ptr + dst + pos, tl.full((TILE,), 1.0, dtype=tl.bfloat16))
    sync_block_all("all", 0)
    v = tl.load(buf_ptr + pid * TILE + i)
    tl.store(out_ptr + pid, tl.sum(v.to(tl.float32)))


@triton.jit
def scatter_owner(buf_ptr, out_ptr, TILE: tl.constexpr, NPROG: tl.constexpr):
    pid = tl.program_id(0)
    i = tl.arange(0, TILE)
    pos = (i * 7 + pid) % TILE
    tl.store(buf_ptr + pid * TILE + pos, tl.full((TILE,), 1.0, dtype=tl.bfloat16))
    v = tl.load(buf_ptr + pid * TILE + i)      # 同 program 消费，无交接
    tl.store(out_ptr + pid, tl.sum(v.to(tl.float32)))


def run_scatter(TILE=16384, rounds=5):
    buf = torch.zeros(TILE * NPROG, dtype=torch.bfloat16, device="npu")
    out = torch.zeros(NPROG, dtype=torch.float32, device="npu")
    for name, kern in (("cross", scatter_cross), ("owner", scatter_owner)):
        passed = 0
        detail = []
        for _ in range(rounds):
            buf.zero_()                                  # 每轮清零，避免脏值掩盖错读
            kern[(NPROG,)](buf, out, TILE=TILE, NPROG=NPROG)
            torch.npu.synchronize()
            good = int((out.cpu() == float(TILE)).sum())
            detail.append(good)
            passed += 1 if good == NPROG else 0
        print("%s pass=%d/%d per_round=%s" % (name, passed, rounds, detail))


run_scatter()   # 本机：cross 5/5、owner 5/5
```

## 3. 失败归因：同构矩阵

失败出现时按三轴各取两档做小矩阵，每格 5–10 轮，记录"通过轮数 / 每轮正确 program 数"：

| 轴 | 低档 | 高档 | 作用 |
|---|---|---|---|
| 工作区规模 | 32 MiB | 2 GiB | 排除"规模"解释 |
| 写读形态 | 稠密整段 | masked 散列 / atomic | 定位写形态 |
| 消费者数 | 1 | 2+（不同 program 读同一段） | 定位多消费者顺序 |

**判定规则**：若同构探针在同等条件下通过，则不得把失败归因于规模或 barrier 语义，必须继续改结构（见第 2 节"写者=消费者"）。
本机实测：稠密 / 脏复用 / atomic / masked 散列四类在 32 MiB–2 GiB 均通过，"规模导致错读"在本配置不成立。

## 4. 并行度下限

单 kernel 里 phase 串行执行，可用并行度取各 phase 的 `min`：

`P_eff = min(phase 内 tile 数, 物理核数)`；行块独占（每个 program 一个行块）时 `P_eff = ceil(M / BM)`。

```python
@triton.jit
def read_panel(gl_ptr, out_ptr, M, V, P: tl.constexpr, BM: tl.constexpr, CH: tl.constexpr):
    pid = tl.program_id(0)
    NM = tl.cdiv(M, BM)
    NP = (V + P - 1) // P
    for t in range(pid, NM, tl.num_programs(0)):
        rm = t * BM + tl.arange(0, BM)
        acc = tl.zeros((BM,), dtype=tl.float32)
        for p in range(0, NP):
            base = p * (M * P)
            for k0 in range(0, P, CH):
                rk = k0 + tl.arange(0, CH)
                gv = p * P + rk
                msk = (rk[None, :] < P) & (gv[None, :] < V)
                v = tl.load(gl_ptr + base + rm[:, None] * P + rk[None, :], mask=msk, other=0.0)
                acc += tl.sum(v.to(tl.float32), axis=1)
        tl.store(out_ptr + rm, acc)


M, V, P, BM, CH = 1536, 20480, 4096, 64, 256
gl = torch.ones((triton.cdiv(V, P), M, P), dtype=torch.bfloat16, device="npu")
out = torch.empty((M,), dtype=torch.float32, device="npu")
for g in (7, 12, 28):
    read_panel[(g,)](gl, out, M, V, P=P, BM=BM, CH=CH)
    torch.npu.synchronize()
    t0 = time.perf_counter()
    for _ in range(5):
        read_panel[(g,)](gl, out, M, V, P=P, BM=BM, CH=CH)
    torch.npu.synchronize()
    ms = (time.perf_counter() - t0) / 5 * 1e3
    print("grid=%d time=%.3f ms BW=%.1f GB/s" % (g, ms, M * V * 2 / 1e9 / (ms / 1e3)))
```

实测（M=1536、V=20480、P=4096、BM=64，面板读取，5 次平均）：

| grid | 每 program 行数 | 时间 | 有效带宽 |
|---|---|---|---|
| 7 | 219.4 | 0.159 ms | **395 GB/s** |
| 12 | 128.0 | 0.080 ms | **789 GB/s** |
| 28 | 54.9 | 0.045 ms | **1411 GB/s** |

判据：`ceil(M/BM) < 28` 时单 kernel 行块所有权会直接损失吞吐；小 M 场景应保留 tile 级并行（多 kernel）或改用 tile 归属而非行块归属。

## 5. 多 phase 的 UB 预算

单 kernel 要把多个 phase 的 buffer 同时装进 UB（248 KB，实际可用约 216 KB）。做法是先列表再加总：

| phase | buffer | 字节 |
|---|---|---|
| 前段 GEMM | A `BM×BK`、B `BK×BN`（bf16） | 2·BM·BK + 2·BK·BN |
| epilogue | 输入/输出各 `BM×BN` bf16 + 中间 fp32 累加 | 4·BM·BN + 4·BM·BN |
| scatter | 索引 `BM×BN` int32 + 值 bf16 | 4·BM·BN + 2·BM·BN |
| dgrad/wgrad | 两路 GEMM 的 A/B + fp32 累加器 | 各 `4·BM·BN` |

```python
@triton.jit
def epilogue(src_ptr, dst_ptr, M, N, BM: tl.constexpr, BN: tl.constexpr):
    pid = tl.program_id(0)
    rm = (pid // tl.cdiv(N, BN)) * BM + tl.arange(0, BM)
    rn = (pid % tl.cdiv(N, BN)) * BN + tl.arange(0, BN)
    a = tl.load(src_ptr + rm[:, None] * N + rn[None, :]).to(tl.float32)
    b = a * 1.5 + 0.25
    c = b * 0.5
    tl.store(dst_ptr + rm[:, None] * N + rn[None, :], (a + b + c).to(tl.bfloat16))


def ub_check(M, N, BM, BN):
    src = torch.zeros((M, N), dtype=torch.bfloat16, device="npu")
    dst = torch.zeros((M, N), dtype=torch.bfloat16, device="npu")
    grid = (triton.cdiv(M, BM) * triton.cdiv(N, BN),)
    try:
        epilogue[grid](src, dst, M, N, BM=BM, BN=BN)
        torch.npu.synchronize()
        print("BM=%d BN=%d tmp=%d KB OK" % (BM, BN, 2 * BM * BN * 4 // 1024))
    except Exception as exc:
        print("BM=%d BN=%d FAIL: %s" % (BM, BN, str(exc).splitlines()[-1][:70]))


ub_check(1024, 1024, 128, 128)
ub_check(1024, 1024, 256, 128)
```

实测（单 phase epilogue，两个 fp32 中间块）：`BM=128, BN=128`（tmp 128 KB）编译并运行通过；`BM=256, BN=128`（tmp 256 KB）在本探针下**也能编译运行**，
说明这两块 tmp 会被编译器拆分/复用。但**单 buffer 过大同样溢出**：同一台机器上把读取探针的分块设成 `CH=262144`（bf16 512 KB）
即报 `ub overflow, requires 8389376 bits while 2031616 bits available`；改成 `CH=32768`（64 KB）后通过。
**writer=consumer 形态的定量判据（实测）**：把收缩轴交给生产 program 时，该 program 需要持一个完整的
`(BM, H)` fp32 累加器，UB 需求 = `BM × H × 4` 字节。可复核探针（物化 `(BM,H)` fp32 再写回）：

| H | BM | 需求 `BM·H·4` | 结果 |
|---|---|---|---|
| 2560 | 4 / 8 / 16 | 40 / 80 / 160 KiB | OK |
| 2560 | 32 | 320 KiB | **FAIL（ub overflow）** |
| 7168 | 4 / 8 | 112 / 224 KiB | OK |
| 7168 | 16 | 448 KiB | **FAIL** |

即 `BM ≤ 221 KiB / (H×4)`：H=2560 时 BM ≤ 20（实测 16 过、32 不过），H=7168 时 BM ≤ 7（实测 8 过、16 不过）。
这条判据可直接用来判断"写者=消费者"是否可行，不必先写完整实现。

因此溢出由"单个 buffer 尺寸"和"同时驻留的 buffer 数"共同决定，预算表要按最坏 phase 组合加总；
放不下时的优先级：**先保面板宽（行 stride）→ 再缩单 phase 的 tile/分块 → 最后减 buffer 或多 phase 合并**。

## 6. launch 计数

静态：数交付文件里 `@triton.jit` 的个数（`grep -c '@triton.jit'`），并确认每个 case 只调用一次。
运行时：包一层计数再断言，避免"函数里多次 `kernel[(grid,)](...)`"漏数：

```python
launches = []
orig = kernel.__getitem__

def counting(grid):
    launches.append(grid)
    return orig(grid)

kernel.__getitem__ = counting
run_one_case(...)
assert len(launches) == 1, f"expected 1 launch, got {len(launches)}"
```

要求：**同一 sha、同一 case** 下同时给出静态 jit 数与运行时 launch 数；两者都要等于 1 才算满足单 launch 契约。

## 7. 融合税分解与回退记录

阶段融合（4 kernel）与全融合（1 kernel）各跑一遍同一组 case，把差异拆成三项：

| 项 | 观测方式 | 期望方向 |
|---|---|---|
| 面板宽（行 stride） | 面板数 `ceil(V/P)`、profiler 的 B 面板读流量 | 面板变窄 → 流量上升 |
| 并行度 | `ceil(M/BM)` 与物理核数 | 行块数 < 核数 → 吞吐下降 |
| UB 降级 | 单 kernel 的 tile/流水深度 vs 阶段融合 | tile 变小 → 单点效率下降 |

UB 降级的实测幅度（同一 bf16 GEMM `M=4096, N=4096, K=2048`，只改 BM，28 program，3 次平均）：

| 配置 | 时间 | 算力 |
|---|---|---|
| BM=128, BN=256 | 0.300 ms | **228.7 TFLOPS** |
| BM=64, BN=256 | 0.445 ms | **154.6 TFLOPS** |

BM 减半带来 **−32%** 算力，可作为"单 kernel 被迫缩 tile"的税基；算子级还要叠加面板数与并行度两项。

回退记录（写进 `report.md` 与 `dev/`）五列：**形态 / 工作区规模 / 写读形态 / 正确性 / 是否可复核**；三项结构尝试都失败才允许 `--fallback`。

## 参考

- [同步与 barrier](sync_and_barrier.md)
- [多输出 GEMM 链的融合与单 launch 化](multi_output_gemm_chain_fusion.md)
- [算子融合](operator_fusion.md)
- [单 launch 融合模式](../patterns/single_launch_fusion.md)
