---
type: Optimization
title: Core Mapping 策略
description: Triton Ascend Core Mapping 三种策略（列优先/行优先/对角线）的选择决策、GROUP_SIZE 调参与 L2 局部性原理。
tags: [task.optimization, topic.tiling, topic.memory, topic.parallelism]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Programming_Model/program_id.md
  role: primary
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-09-08T09:05:00Z'
platforms: [a2, a3]
---
# Core Mapping 策略

Core Mapping 决定每个 AI Core 处理哪个 (M,N) 输出 tile。策略选择直接影响 L2 缓存复用、负载均衡和 bank conflict 模式。选择不当可损失 20-40% 性能。

## 三种策略

| 策略 | Block ID 模式 | 最适合 | GROUP_SIZE |
|------|-------------|--------|------------|
| **列优先** | 相邻 ID 访问同 N 列 | N-dominant (N>>M) | 8/16/32 |
| **行优先** | 相邻 ID 访问同 M 行 | M-dominant (M>>N) | 8/16/32 |
| **对角线** | 相邻 ID 访问不同 (M,N) | M,N≥512（正方形） | 8/16/32 |

## 决策规则

- M≥512 且 N≥512 → 对角映射（`dl.grouped_launch_diagonal`）
- N>>M → 列优先
- M>>N → 行优先

## 性能探针的测量协议（结论能否复现的前提）

下表按 B 足迹和计时协议记录各自观测；**测量协议的独立影响待同配置前后对照**（与下文第 72 行一致）：

| 协议 | B 足迹档 | 分组倍数（原始值） | 结论 |
|---|---|---|---|
| 朴素：1 次 warmup + 3 次平均、只在末尾 sync、不交错、不预热时钟 | **17 MB** | **0.62× / 1.21×**（两遍） | 看起来"收益不可复现" |
| 同上 | **34 MB** | **1.33× / 0.70×**（两遍） | 同上 |
| 严格：warmup 5；计时 10 次且每次前后 sync；A/B 交错；每轮前 800 ms 烧机；取中位数；≥3 轮 | **34 MB** | **1.34×**（1.36/1.34/1.34） | 稳定可复现，轮间 ≤2% |
| 同上 | **134 MB** | **1.29×**（1.28/1.29/1.30） | 同上 |
| 历史协议（原表每档 3 次均值） | **134 MB** | **1.27× / 1.28×** | 历史档观测，与上行严格协议分列 |

> 数据配对规则：**不同尺寸/不同协议的数字不得混用**。上表按"协议 + B 足迹档"分列；
> 若未在相同配置用现行脚本复跑，只报告各自条件下的观测（不得把 17/34 MB 的朴素数字与 34/134 MB 的严格数字配对比较）。

**协议要求（性能类结论的最低门槛）**：
1. warmup ≥5 次；计时 ≥10 次，**每次单独 `torch.npu.synchronize()` 前后包裹**，不用"循环 N 次再除"的均值；
2. 被测的多个配置**交错**测量（A/B/A/B…），不要先测完 A 再测 B（频率/温度漂移会偏袒后者）；
3. 每轮前用一段固定负载（如 800 ms 逐元素运算）**烧机**，让频率落到稳态；
4. 每轮取**中位数**，≥3 轮；**同时记录每轮比值与 min/max 区间**——只给一个平均数不算可复核；
5. 记录卡上是否有其它进程（`npu-smi info`），共享卡必须显式说明；
6. 单轮、单次、3 次平均的数值**不作为结论**，只能作为"待复测"的线索。

**GROUP_M 一节**的数字按严格协议测得（Ascend950PR / A5、CANN 9.2.0-beta.2、triton-ascend 3.6.0、bf16、`num_aicore=28`）；
**面板宽一节**为旧探针（内层遍历完整 P，含 padding 工作量），见该节限定，两节数据不可混用。

## L2 分组（GROUP_M）的实测收益

同 kernel 只切 `GM`，`M=8192, K=2048`，tile 128×256×64，常驻网格 28 program（1/core），严格协议：

| B 足迹（N×K, bf16） | `GM=0` | `GM=8` | 倍数（每轮） |
|---|---|---|---|
| 34 MB（N=8192） | 1.179 ms（233.2 TFLOPS） | 0.882 ms（311.6 TFLOPS） | **1.34×**（1.36 / 1.34 / 1.34） |
| 134 MB（N=32768） | 6.434 ms（170.9 TFLOPS） | 4.994 ms（220.1 TFLOPS） | **1.29×**（1.28 / 1.29 / 1.30） |

读法：
- 两档都稳定在 **1.29–1.34×**，轮间波动 ≤2%；`GM=0`/`GM=8` 的时间区间也各只有 1–2% 宽度；
- 收益来源：同组并发 program 共享同一 B 面板，减少 HBM 重复流量；B 足迹越大、并发 program 越多，收益越明显（本探针 34 MB 已起效）；
- 仍**不能当固定倍数**：换 shape/tile/网格要按本协议复测；但"**它能带来 1.3× 量级**"是可复现的结论；
- 历史档（朴素协议，17/34 MB）观察到 **0.62–1.33×** 的宽区间；当前严格档（34/134 MB）观察到 **1.29–1.34×**。
  两者是**不同尺寸/不同协议下的各自观测**，**协议的独立影响待同配置前后对照**；不据此扩大重测范围，
  也不把差异归为"测量问题"这一单一结论。

可复核探针（改 `N` 即可复现上表；`timed`/`burn` 即上文协议）：

```python
import statistics, time
import torch, torch_npu  # noqa: F401
import triton
import triton.language as tl

BM, BN, BK = 128, 256, 64


@triton.jit
def gemm(a_ptr, b_ptr, c_ptr, M, N, K, BM: tl.constexpr, BN: tl.constexpr,
         BK: tl.constexpr, GM: tl.constexpr):
    pid = tl.program_id(0); npg = tl.num_programs(0)
    nt_n = tl.cdiv(N, BN); nt_m = tl.cdiv(M, BM); total = nt_m * nt_n
    for t in range(pid, total, npg):
        if GM > 0:                                        # L2 分组
            tpg = GM * nt_n; gid = t // tpg
            first = gid * GM; gsz = tl.minimum(nt_m - first, GM)
            rem = t - gid * tpg
            tm = first + (rem % gsz); tn = rem // gsz
        else:                                             # 行优先
            tm = t // nt_n; tn = t % nt_n
        rm = tm * BM + tl.arange(0, BM)
        rn = tn * BN + tl.arange(0, BN)
        acc = tl.zeros((BM, BN), dtype=tl.float32)
        for k0 in range(0, K, BK):
            rk = k0 + tl.arange(0, BK)
            av = tl.load(a_ptr + rm[:, None] * K + rk[None, :])
            bv = tl.load(b_ptr + rn[:, None] * K + rk[None, :])
            acc += tl.dot(av, bv.T)
        tl.store(c_ptr + rm[:, None] * N + rn[None, :], acc.to(tl.bfloat16))


def once(fn):                                             # 单次耗时：前后各 sync
    torch.npu.synchronize(); t0 = time.perf_counter()
    fn(); torch.npu.synchronize()
    return (time.perf_counter() - t0) * 1e3


def burn(ms=800):                                         # 烧机稳定频率
    x = torch.randn(4096, dtype=torch.float32, device="npu")
    end = time.time() + ms / 1e3
    while time.time() < end:
        torch.mul(x, 1.0001, out=x)
    torch.npu.synchronize()


M, K = 8192, 2048
a = torch.randn((M, K), dtype=torch.bfloat16, device="npu")
for N in (8192, 32768):                                   # 34 MB / 134 MB 两档
    b = torch.randn((N, K), dtype=torch.bfloat16, device="npu")
    c = torch.empty((M, N), dtype=torch.bfloat16, device="npu")
    fns = {gm: (lambda gm=gm: gemm[(28,)](a, b, c, M, N, K, BM=BM, BN=BN, BK=BK, GM=gm))
           for gm in (0, 8)}
    for f in fns.values():
        f(); [once(f) for _ in range(5)]                  # warmup 5
    med = {gm: [] for gm in fns}
    for r in range(3):
        burn()
        per = {gm: [] for gm in fns}
        seq = (0, 8) if r % 2 == 0 else (8, 0)            # 每轮轮换先后
        for _ in range(10):
            for gm in seq:                                # A/B 逐次交错采样
                per[gm].append(once(fns[gm]))
        for gm in fns:
            med[gm].append(statistics.median(per[gm]))
    m0, m8 = statistics.median(med[0]), statistics.median(med[8])
    print("B=%6.0f MB  GM0 %.3f ms  GM8 %.3f ms  ratio %.2f  per-round %s"
          % (N * K * 2 / 1e6, m0, m8, m0 / m8,
             [round(x / y, 2) for x, y in zip(med[0], med[8])]))
    del b, c
```

## 面板宽（按行读式样）的实测趋势（旧探针结果，待用有效-K 版复测）

**旧探针（下表）内层遍历完整 `P`**：B 侧 mask 只把越过 K 的输入置零，循环仍读 A 并执行 `tl.dot`。
据此 B/K 关系，`P=4096` 档在 K=1024/2048 时分别执行 **64 / 64 次** dot（`P=256`、`P=1024` 为 16/32 与 32/32 次），
而 TFLOPS 仍按 `2MNK` 计算。因此下表中的 0.29–0.54× **不能单独归因于行 stride 或 DMA 分片**，
只能作为"含 padding 工作量"的方案对比与待复测线索。修正后的探针见本节末（有效 K + 参考 GEMM 校验），
重测后才能把差异归因于行 stride。

| shape | P=256（旧） | P=1024（旧） | P=4096（旧） |
|---|---|---|---|
| M=8192, K=2048, N=8192 | 1.232 ms（223.2 TF） | **1.168 ms（235.4 TF，1.05×）** | 2.267 ms（121.2 TF，**0.54×**） |
| M=4096, K=1024, N=8192 | 0.263 ms（260.9 TF） | **0.251 ms（274.1 TF，1.05×）** | 0.919 ms（74.7 TF，**0.29×**） |

读法（限定条件）：
- 两个形状里 **P≈1024 比 P=256 快约 5%**；P=4096 的劣化幅度两遍一致、轮间稳定，但**含 padding 工作量**；
- 旧探针的 TFLOPS 按 `2MNK` 计，P=4096 档多算的 dot 次数已如上标注，不能当作纯带宽/stride 结论；
- 拐点位置随 shape 变化（第二形状 P=1024 有一轮 1.85× 离群，方向不变），必须按目标 shape 用同一协议复测。

可复核探针（修正版：内层上界取当前面板有效 K、固定 dot 次数、逐轮轮换 P 顺序、逐轮成对比值；
`once()`/`burn()` 复用上一节）：

```python
@triton.jit
def gemm_panel_row(gl_ptr, b_ptr, c_ptr, M, N, K, P: tl.constexpr, BM: tl.constexpr,
                   BN: tl.constexpr, BK: tl.constexpr):
    """A 为 panel-major，按行读；内层只跑到当前面板的有效 K（尾部 mask 置零）。"""
    pid = tl.program_id(0); npg = tl.num_programs(0)
    nt_n = tl.cdiv(N, BN); total = tl.cdiv(M, BM) * nt_n
    npanel = tl.cdiv(K, P)
    for t in range(pid, total, npg):
        tm = t // nt_n; tn = t % nt_n
        rm = tm * BM + tl.arange(0, BM)
        rn = tn * BN + tl.arange(0, BN)
        acc = tl.zeros((BM, BN), dtype=tl.float32)
        for p in range(0, npanel):
            kbeg = p * P
            kend = tl.minimum(P, K - kbeg)                # 当前面板有效 K
            base = p * (M * P) + rm[:, None] * P
            for k0 in range(0, kend, BK):
                rk = k0 + tl.arange(0, BK)
                inb = rk < kend
                av = tl.load(gl_ptr + base + rk[None, :], mask=inb[None, :], other=0.0)
                vk = kbeg + rk
                bv = tl.load(b_ptr + rn[:, None] * K + vk[None, :],
                             mask=vk[None, :] < K, other=0.0)
                acc += tl.dot(av, bv.T)
        tl.store(c_ptr + rm[:, None] * N + rn[None, :], acc.to(tl.bfloat16))


# 复用 once()/burn()；选 K 与各 P 对齐（如 K=4096、P∈{256,1024,4096}）
for (MM, KK, NN) in ((8192, 4096, 8192), (4096, 4096, 8192)):
    b = torch.randn((NN, KK), dtype=torch.bfloat16, device="npu")
    A = torch.randn((MM, KK), dtype=torch.bfloat16, device="npu")     # 每 shape 只生成一次逻辑 A
    ref = (A.float() @ b.float().T).to(torch.bfloat16)                # 一次参考 GEMM（P 无关）
    c = torch.empty((MM, NN), dtype=torch.bfloat16, device="npu")
    fns = {}
    for P in (256, 1024, 4096):
        assert KK % P == 0                                # 对齐，dot 次数相同
        gl = A.reshape(MM, KK // P, P).permute(1, 0, 2).contiguous().view(-1)  # 同一逻辑 A 的 panel-major 重排
        fns[P] = (lambda P=P, gl=gl: gemm_panel_row[(28,)](gl, b, c, MM, NN, KK,
                                                           P=P, BM=BM, BN=BN, BK=BK))
    for P in fns:
        fns[P]()
        torch.npu.synchronize()
        try:                                              # 任一 P 校验失败即停止计时；容差按 BF16 累加误差显式写出
            torch.testing.assert_close(c, ref, atol=5e-2, rtol=2e-2)
        except AssertionError as exc:
            raise RuntimeError("P=%d 参考校验失败，停止计时" % P) from exc
        print("P=%-5d ref-check PASS (atol=5e-2, rtol=2e-2)" % P)
    for f in fns.values():
        [once(f) for _ in range(5)]
    med = {P: [] for P in fns}
    for r in range(3):
        burn()
        per = {P: [] for P in fns}
        seq = (256, 1024, 4096) if r % 2 == 0 else (4096, 1024, 256)   # 逐轮轮换
        for _ in range(10):
            for P in seq:
                per[P].append(once(fns[P]))
        for P in fns:
            med[P].append(statistics.median(per[P]))
    base = statistics.median(med[256])
    for P in fns:
        m = statistics.median(med[P])
        print("M=%d K=%d  P=%-5d %.3f ms  x%.2f  per-round %s"
              % (MM, KK, P, m, base / m,
                 [round(a / b, 2) for a, b in zip(med[256], med[P])]))
```

## OPT-triton-core-mapping-001: GROUP_SIZE 配置

- GROUP_SIZE ∈ {8, 16, 32}，通过 autotune 选取
- GROUP_SIZE > 核心数 → L2 局部性变差
- 至少提供 3 个不同 GROUP_SIZE

