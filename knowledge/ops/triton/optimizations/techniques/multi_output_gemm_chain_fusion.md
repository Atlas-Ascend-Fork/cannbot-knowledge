---
type: Optimization
title: 多输出 GEMM 链的融合与单 launch 化
description: 多输出 GEMM 链（两路输出归约轴不同）的融合方法：中间量按片上分块/重算/GM 物化三种方式取舍、
  面板宽与 K tile 解耦、按该维因数与 UB 预算取较大值（本案例 16K 量级；合并单 kernel 时先保面板宽）、单 launch 时固定
  phase 顺序与成对屏障、UB 按最坏 epilogue 估；含 fused epilogue 与单 launch 的 fusion tax 取舍、
  交付判定（精度 + 运行时 launch 计数）与常见错误速查。
tags: [task.optimization, topic.implementation.pipeline, topic.memory, topic.implementation.synchronization]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/865691e2e9b656bc58008170207b4108d92e8dd1/docs/zh/triton_api/Linear_Algebra_Ops/dot.md
  role: primary
created_at: '2026-11-23T00:00:00Z'
updated_at: '2026-11-23T00:00:00Z'
platforms: ['950']
---
# 多输出 GEMM 链的融合与单 launch 化

## 触发条件

- 一条计算链上有多个 GEMM，且不同输出的归约轴不一致（一个沿特征维归约、另一个沿批量维归约）；
- 链上还有逐元素 epilogue（指数、索引累加、掩码），中间量需要落工作区；
- 需要决定停在 fused epilogue，还是继续压到「1 个 `@triton.jit` / 每次调用 1 次 launch」。

## 结构条件

- **两路归约轴不同 ⇒ 单 program 一次算不出两路输出**：两路输出沿不同维度归约，依赖关系不一致。中间量落地有三种
  方式：① 小 shape 时让同一 program 在片上产生并消费共享中间量；② 按 tile / 条带重算并逐块累加，用额外计算换
  片上容量；③ 在 GM 物化中间量工作区，再由两个 GEMM 分别消费。GM 物化是"片上放不下、且中间量被两路消费者共享"
  时的选择，不是归约轴不同本身的要求；用同一 tile 硬出两路输出会退化成重复计算或错误累加。中间量保持 bf16
  才能走 Cube 高吞吐路径。
- **面板宽与 K tile 解耦，并按 UB 预算尽量取大**：面板宽只决定工作区的行 stride（`P × dtype_bytes`），与 GEMM 的 K tile 是两个量。
  面板数 = `ceil(V/P)`：`P=128` 时约 970 个、`P=16K` 时约 8 个；权重（B 面板）会按面板重复读取，面板越窄读得越多。
  **两个因素必须分开记账**（不可打包归因）：
  1. **面板宽**：只决定工作区行 stride 与面板数 `ceil(V/P)`。在**按行读**（`addr = p·M·P + m·P + k`）的式样下，
     旧探针（内层遍历完整 P、含 padding 工作量）观察到 **P≈1024 比 P=256 快约 5%，P=4096 明显劣化**，
     但该探针在 P=4096 档多执行 dot（K=1024/2048 时为 64 次，P=256/1024 为 16/32 次），
     **0.29–0.54× 不能单独归因于行 stride 或 DMA 分片**；已改有效-K + 参考 GEMM 校验版探针待复测，
     "沿列连续读"的式样本卡未测，**不能笼统写"面板越宽越好"**，
     见 [core mapping 的面板宽趋势](core_mapping.md#面板宽按行读式样的实测趋势旧探针结果待用有效-k-版复测)；
  2. **L2 分组（`GROUP_M`）**：严格协议在 **34 MB / 134 MB** 档测得 **1.29–1.34×**（轮间波动 ≤2%）；
     历史档（朴素协议，17/34 MB）观察到 **0.62–1.33×**，与严格档是不同尺寸/协议下的各自观测；
     **协议独立影响待同配置前后对照**，两套数据不得配对，也不把差异归为单一"测量问题"，
     见 [core mapping 的测量协议](core_mapping.md#性能探针的测量协议结论能否复现的前提)。
  结论：**不要把"面板宽 + L2 分组"写成一个整体观察**；两者各自有独立探针与协议，按目标 shape 分别复测。
  **卡内记录（组内观测；实现未随卡归档）**：同一组必测输入（14 个 shape，来自任务标杆）、Ascend950PR/957c、bf16、
  triton-ascend 3.6.0、CANN 25.7.rc1.7，`benchmark.py --warmup 3 --repeats 5 --no-lock-frequency`：

  | 配置 | launch 数 | geomean | 单 case 区间 |
  |---|---|---|---|
  | 多 kernel 基线（P=256，无分组） | 4 | **0.35** | 0.11 – 0.78 |
  | fused epilogue（P=256 + `GROUP_M=8`） | 4 | **1.42** | 1.05 – 1.70 |
  | 单 kernel（P=128，行块独占） | 1 | **0.90** | 0.52 – 1.30 |

  **最小探针（可执行，卡内）**：下面这段只做面板读取、不含 `tl.dot`，用与具体任务无关的 shape
  （`M=1536, V=20480`，不属于任何必测用例）验证"面板宽（行 stride）"与"行块并行度"：

```python
import time
import torch, torch_npu  # noqa: F401
import triton
import triton.language as tl


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
                gv = p * P + rk                      # 面板内局部列 + 面板偏移
                v = tl.load(gl_ptr + base + rm[:, None] * P + rk[None, :],
                            mask=(rk[None, :] < P) & (gv[None, :] < V), other=0.0)
                acc += tl.sum(v.to(tl.float32), axis=1)
        tl.store(out_ptr + rm, acc)


def bench(M, V, P, nprog, BM=64, CH=256, repeat=5):
    NP = triton.cdiv(V, P)
    gl = torch.ones((NP, M, P), dtype=torch.bfloat16, device="npu")
    out = torch.empty((M,), dtype=torch.float32, device="npu")
    read_panel[(nprog,)](gl, out, M, V, P=P, BM=BM, CH=CH)
    torch.npu.synchronize()
    t0 = time.perf_counter()
    for _ in range(repeat):
        read_panel[(nprog,)](gl, out, M, V, P=P, BM=BM, CH=CH)
    torch.npu.synchronize()
    ms = (time.perf_counter() - t0) / repeat * 1e3
    eff = M * V * 2 / 1e9              # 有效字节（只统计 V 内元素）
    print("P=%6d panels=%4d grid=%3d time=%7.3f ms BW_eff=%6.1f GB/s sum_ok=%d/%d"
          % (P, NP, nprog, ms, eff / (ms / 1e3), int((out.cpu() == float(V)).sum()), M))


M, V = 1536, 20480
for P in (128, 256, 4096, 16384):
    bench(M, V, P, nprog=28)
for g in (7, 12, 28):
    bench(M, V, 16384, nprog=g)
```

  实测（Ascend950PR/957c、bf16、M=1536、V=20480、同一份代码 5 次平均；`sum_ok` 为逐行求和是否等于 V）：

  | 配置 | 面板数 | grid | 时间 | 有效带宽 | sum_ok |
  |---|---|---|---|---|---|
  | P=128 | 160 | 28 | 0.145 ms | **433 GB/s** | 1536/1536 |
  | P=256 | 80 | 28 | 0.054 ms | **1174 GB/s** | 1536/1536 |
  | P=4096 | 5 | 28 | 0.054 ms | **1169 GB/s** | 1536/1536 |
  | P=16384（尾面板 4096） | 2 | 28 | 0.065 ms | **975 GB/s** | 1536/1536 |
  | P=16384 | 2 | 7 | 0.404 ms | **156 GB/s** | 1536/1536 |
  | P=16384 | 2 | 12 | 0.120 ms | **525 GB/s** | 1536/1536 |

  读法（只报有效吞吐；不推断物理 HBM 流量，也不做单因素归因）：
  - 本探针中 `P=128` 的有效吞吐（433 GB/s）明显低于 `P=256`（1174）与 `P=4096`（1169）；
  - `P=16384` 档（975 GB/s）低于 `P=4096`（1169 GB/s）。注意这一档同时改变了 P、stride 与面板数，
    且 V=20480 下第二面板只有 4096 有效列，**不能单独归因于"尾面板"**；
  - 同一 `P=16384` 下把 grid 由 7 提到 12、28，本次有效吞吐 156 → 525 → 975 GB/s 上升；
    该曲线不支持"接近按核数线性"的定量结论。
  - 掩码下尾面板仍可能发出被掩掉的 load，本表只按有效字节计吞吐；该探针只验证趋势，不等于算子级 geomean。

  **机制拆解（基于逐 case 差异的观察，不是精确分解）**：
  - **V 大、M 中等的形状组**：fused 明显优于单 kernel，差距主要来自面板宽 256→128（`ceil(V/P)` 面板数翻倍，
    weight 面板重复读取跟着翻倍）；
  - **M 较小、形状组较多**：fused 同样优于单 kernel，差距主要来自并行度——单 kernel 为规避跨 program 交接
    让每个 program 独占一个行块，M=1024 时行块数 8 < 28 核，多数核空闲；fused 版仍是多 kernel，可以按 tile 铺满核。
  - 因此合并单 kernel 的代价要分两笔记账：**面板宽（访存流量）** 与 **行块所有权（并行度）**，不能只记一笔。
  **复核方式**：固定其余参数（tile、分组、buffer 数、编译栈），只改面板宽（如 128 / 256 / 16K 三档），在同一组输入上
  各跑一次 `benchmark.py`，记录 geomean 与 profiler 里 B 面板的读流量；同时记录 SoC、dtype、布局与 UB 预算。
  结论：**合并单 kernel 时应先保面板宽、再缩 K tile 或减 buffer**；`P` 的上限由 UB 预算与 dtype 决定，需按实现实测，不作通用阈值。
- **面板切分是候选优化，不是硬上限**：本案例实测面板化后同一 GEMM 的 2D load 吞吐从 21 TF/s 提升到 230–250 TF/s；
  原测点只比较 stride 64KB 与 242KB 两条路径（242KB 仍能正确执行），不能推 64KB 硬上限，也不能把逻辑宽度等同于
  带 padding/转置后的实际 stride；落地按该 shape 的实际 stride、dtype 与布局实测取舍（见 [tiling 与 grid](tiling_and_grid_910_95.md)）。
- **复核方式**：固定其余参数（tile、分组、buffer 数），只改面板宽（如 128 / 256 / 16K 三档），记录 geomean 与 profiler 里
  B 面板的读流量/带宽；三档都应在同一 SoC、同一编译栈与同一布局下测，避免混入其他改动。
- **单 kernel 多 phase 时 UB 按最坏 epilogue 估**：fp32→bf16 的舍入 epilogue 需 2 个 `BM×BN` fp32 中间块；
  `BM=BN=128` 可行，`BM=256/BN=128` 在多 phase 单 kernel 下会 ub overflow。GEMM tile 与 epilogue tile 必须分开参数化。
- **本案例未验证某些写读形态的 GM 交接**：在 Ascend950PR、28 核、Triton-Ascend 3.6、该写读形态与同步 mode 下，
  稀疏（masked / atomic）写后经 `sync_block_all` 直接消费仍未取到新值；这是该配置的观测，**不是 `sync_block_*` 的
  API 契约**。可靠做法是把稀疏写放到真正的 kernel 边界，或让「写者 = 消费者」，或让后续稠密 phase 以 RMW 吸收它；
  其他同步路径按 API 契约与实测确认（见 [同步与 barrier](sync_and_barrier.md)）。
- **中间量舍入点必须与参考一致**：参考若把 GEMM 输出先舍到 bf16 再参与后续计算，融合实现必须复刻该舍入点，
  不能依赖 `.to(bf16).to(fp32)`（会被编译期折叠），见 [bf16 参考舍入](bf16_reference_rounding.md)。

## 融合步骤

1. **先降级到 fused epilogue**：把逐元素 epilogue 融进消费该中间量的 GEMM，消掉中间量的 GM 往返；
   保留多 kernel 边界，验证精度与性能后再考虑单 launch。
2. **规划单 launch 的 phase 顺序**：清零/初始化（dense store）→ 屏障 → 稀疏写（只 store，重复目标按行去重求和）
   → 屏障 → 稠密 GEMM + epilogue（对工作区做 RMW，吸收上一步的稀疏写）→ 屏障 → 两路 GEMM 输出。
3. **屏障成对**：`all_cube` / `all_vector` / `all_sub_vector` 按参与该相位的执行单元成对使用；每个相位都写全。
4. **grid 与重排**：`grid = min(总 tile 数, 物理核数)`、每核常驻一个 program；分组映射必须与 host 侧的 tile
   枚举一致——固定组宽且不处理尾组的解码器要求组宽整除 tile 数；支持按实际尾组宽度解码的实现可以不整除，
   但必须验证 host 枚举恰好覆盖每个 tile 一次。
5. **分别留证**：多 kernel 基线、fused epilogue、单 kernel 三份产物各自保留源码哈希与精度/性能结果，三者互不相同。

## 单 launch 的收益与代价

- 收益：省掉阶段间 GM 往返与重复启动，工作区可跨 phase 复用。
- 代价（fusion tax）：所有 phase 共用一套 tile / 多缓冲配置，大 tile 的 fp32 累加器与 producer 流水深度被迫降级，
  Cube 吞吐相比多 kernel 版本下一个档位；小 shape 更容易被固定开销吃掉。
- 实测方向（单一 A5 案例，仅作量级参考）：单 launch 相对 fused epilogue 的端到端退化落在 **+7%~+23%**，
  最小的 case 可能跌破 1.0×；数值随 shape、tile 与工作区布局变化，不能当通用阈值。
- 因此顺序是「先消中间量搬运，再谈单 launch」；两者混在一起调，"省下的搬运"和"流水降级"会互相掩盖。

## 交付判定

先看任务把什么定为硬约束，再按同一张表判定（与 [算子融合](operator_fusion.md) 的口径一致）：

| 约束组合 | 判定 |
|---|---|
| 单 launch 仅是优化目标 | 按收益选：单 launch 有净收益才采用，否则保留 fused epilogue / 多 kernel 为交付候选 |
| 单 launch 是硬约束、性能仅观测 | **全部必测用例精度通过 + 运行时每 case 恰好 1 次 device launch**（独立清零 kernel 计入）即可交付；性能单列，未达标如实记录 |
| 单 launch 与性能同时是硬约束 | 任一项未满足即**验收未通过**；多 kernel 可作为待确认的替代方案，须显式记录契约冲突并说明未达项 |

- 源码里的 `@triton.jit` 定义数不能代替运行时 launch 计数。
- 只有不存在合规候选（精度或 launch 契约不满足）时才回退多 kernel，并显式记录契约冲突。

## 常见错误速查

| 现象 | 原因 | 处理 |
|---|---|---|
| 中间量对不上、个别行错乱 | 两路归约轴混用同一 tile | 按片上 / 重算 / GM 物化三种方案选一种，两个 GEMM 分别消费 |
| 单 kernel 编译 ub overflow | epilogue 与 GEMM 共用大 tile | 分开参数化 tile；BM/BN 取 128 起步 |
| 稀疏写后读到旧值 | 同一 launch 内依赖 barrier 交接 | 放到 kernel 边界、让写者=消费者，或稠密 phase RMW 吸收 |
| 小 case 跌破 1.0× | fusion tax 被固定开销放大 | 按上面三条分支判定：单 launch 仅优化目标时按收益取舍；硬约束时记录未达项 |
| 合并成单 kernel 后性能骤降 | 面板宽随 K tile 一起被缩小，权重按面板重复读 | 面板宽与 K tile 解耦，先保面板宽、缩 K tile 或减 buffer |
| 分组解码错位 | 固定组宽且不处理尾组时，组宽不整除 tile 数 | 取 tile 数的因数，或按实际尾组宽度解码并验证恰好覆盖一次 |

单 launch 的阶段门、交接形态与预算表见 [单 kernel 单 launch 的可行性体系](single_kernel_feasibility.md)。

## 参考

- [同步与 Barrier](sync_and_barrier.md)
- [bf16 参考 GEMM 的舍入与 golden 容差](bf16_reference_rounding.md)
- [可融合重构](fusion_friendly_restructure.md)
- [tiling 与 grid](tiling_and_grid_910_95.md)
