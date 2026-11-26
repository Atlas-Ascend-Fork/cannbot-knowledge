---
type: Optimization
title: bf16 参考 GEMM 的舍入与 golden 容差
description: 参考 torch.mm(bf16, bf16) 输出 bf16 时，本探针观测 `p` 的最大相对误差为 **171.8%（1.7183）**，该值同时含 logit 差与两条路径各自的 lse 差；独立 fp32 累加无法逐位复现，需用 reference-g 对照定位或 ulp 级容差，而不是盲目调 kernel。
tags: [task.optimization, topic.precision, task.testing]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/865691e2e9b656bc58008170207b4108d92e8dd1/docs/zh/triton_api/Linear_Algebra_Ops/dot.md
  role: primary
created_at: '2026-11-21T00:00:00Z'
updated_at: '2026-11-21T00:00:00Z'
platforms: ['950']
---
# bf16 参考 GEMM 的舍入与 golden 容差

## 现象
- 参考 `torch.mm(bf16, bf16)` 输出 bf16；|logit|≈25–40 时 bf16 ulp = 0.125–0.25。
- `p=exp(z-lse)` 的相对误差由 logit 差决定：固定 lse 时为 `|expm1(Δz)|`，两条路径 lse 也不同时为
  `|expm1(Δz-Δlse)|`，不额外依赖 `|z|` 的绝对值；bf16 的 1 ulp 本身随 `|z|` 增大（z≈32 → 0.25 对应约 28%，
  z≈64 → 0.5 对应约 65%）。
- 本案例实测（|z| 覆盖到约 64 binade）：`p` 相对误差 **max 1.7183（171.8%）**、mean 1.06e-05、任一行内 >1e-2 的行数 13/5120。
  该 171.8% 是**全表最大 p 相对误差**，不是"1 ulp 的上限"：它对应的样本可能落在 `diff > 1 ulp` 桶，
  且 `p` 用两条路径各自的 lse（同时含 logit 与 lse 差异）。1 ulp 单独造成的放大见原始推导（z≈64 时约 65%）。
  该数值只作为该实验的观测，不外推（本卡早期记录的 64.9% 来自另一组输入，已按同一口径重跑后替换）。
- 独立实现用 fp32 累加仍与 torch 的累加顺序不同，会有少量元素发生 1-ulp 翻转（实测 **0.0170%**，下表）；每个翻转污染该行的一个输出。

## 实验环境与实测数据

**软硬件范围（本节全部数据均来自这一环境）**

| 项 | 值 |
|---|---|
| SoC / 板 | Ascend950PR（Chip 957c，Chip Version V100），单片 HBM 约 84 GiB |
| 设备 | 单卡运行，`ASCEND_RT_VISIBLE_DEVICES=2` |
| CANN | 25.7.rc1.7 |
| PyTorch / torch_npu | 2.14.0+cpu / 2.14.0 |
| Triton | triton-ascend 3.6.0 |
| Python / OS | 3.10.22 / Linux 6.8.0-149-generic x86_64 |

**实测（shape：`M=5120, K=3072, N=12288`，取前 512 列，共 2,621,440 个元素；输入由 CPU `torch.randn(generator=seed0)` 生成后转 bf16 搬到 NPU）**

| 指标 | 实测值 |
|---|---|
| 与参考完全相等 | 2,620,965 / 2,621,440 = **99.9819%** |
| `0 < diff < 1 ulp` | 1 / 2,621,440 = **0.00004%** |
| `diff == 1 ulp` | 445 / 2,621,440 = **0.0170%** |
| `diff > 1 ulp` | 29 / 2,621,440 = **0.0011%** |
| `max |diff|`（绝对值） | 1 |
| `|z|` 范围 | 7.25e-05 – 296（无 0 / subnormal / 非有限值） |
| `p` 相对误差 max / mean | **1.7183** / 1.06e-05 |
| 任一行内 `p` 误差 >1e-2 的行数 | 13 / 5120 |

四桶只对"正常有限非零值"统计（掩码与分母相同），合计 2,621,440 = 元素总数，排除 0。

**泛化验证（第二组 shape，非必测用例）：`M=2048, K=1536, N=8192`，取前 512 列，共 1,048,576 个元素**

| 指标 | 实测值 |
|---|---|
| 与参考完全相等 | 1,048,434 / 1,048,576 = **99.9865%** |
| `0 < diff < 1 ulp` | 2 / 1,048,576 = **0.0002%** |
| `diff == 1 ulp` | 133 / 1,048,576 = **0.0127%** |
| `diff > 1 ulp` | 7 / 1,048,576 = **0.0007%** |
| `max |diff|`（绝对值） | 0.5 |
| `|z|` 范围 | 1.0e-04 – 184 |
| `p` 相对误差 max / mean | **0.3935** / 1.82e-06 |
| 任一行内 `p` 误差 >1e-2 的行数 | 9 / 2048 |

四桶合计 1,048,576 = 元素总数，排除 0（与第一组同口径，同一段代码逐组重跑）。

- 第二组与第一组（99.9819% / 0.0170% / 0.0011%）量级一致：**1-ulp 翻转比例在 1e-2% 量级，>1 ulp 在 1e-3% 量级**，
  与 shape 的具体取值无关；`p` 的相对误差上限随 `|z|` 覆盖范围变化（第一组到 296、第二组到 184）。

- ulp 口径：bf16 为 7 位尾数，`ulp(x) = 2^(floor(log2|x|) - 7)`；只对正常有限非零值分类。
- 注意：`|z|` 很小时 ulp 本身极小（本测最小 `|z|=7.25e-05`，其 ulp 约 2.8e-08），单个绝对差 1 对应上千 ulp；
  因此按 ulp 比例看误差要按 logit 所在 binade 分段，不能只看全局 max。

### 可执行复现（最小探针）

- 输入：CPU 侧 `torch.randn(M,K,generator=g)` / `torch.randn(K,N,generator=g)`（`g` 由 `seed=0` 初始化），
  再 `.bfloat16().npu()`；`M=5120,K=3072,N=12288`，取前 `S=512` 列。与上表同一输入口径。
- 参考：CPU fp64 累加后转 bf16（`(a.double() @ b.double()).to(torch.bfloat16)`），不引入 device 侧额外舍入。
- lse：**两条路径各按自身 logits 逐行 logsumexp**（不是固定同一个 lse），因此 `p` 的相对差同时含 logit 差与 lse 差；
  只看固定 lse 的放大时应改用 `abs(expm1(Δz))`。
- 统计口径：分 `equal` / `0 < diff < 1 ulp` / `diff == 1 ulp` / `diff > 1 ulp` 四桶；两侧（参考与实测）都要求
  "有限、非零、非 subnormal"，被排除的元素单独计数（本测两组各排除 0）。四桶之和 + 排除数 = 元素总数。

```python
import torch
import torch_npu  # noqa: F401

torch.npu.set_device(0)
M, K, N, S = 5120, 3072, 12288, 512
g = torch.Generator().manual_seed(0)
a = torch.randn(M, K, generator=g).bfloat16().npu()
b = torch.randn(K, N, generator=g).bfloat16().npu()
z_npu = torch.mm(a, b)[:, :S].float().cpu()
z_ref = (a.float().cpu().double() @ b[:, :S].float().cpu().double()).to(torch.bfloat16).float()

diff = (z_npu - z_ref).abs()
# 双侧有效值：参考与实测都要有限、非零、非 subnormal
normal = (torch.isfinite(z_ref) & torch.isfinite(z_npu)
          & (z_ref != 0) & (z_npu != 0)
          & (z_ref.abs() >= 2.0 ** -126) & (z_npu.abs() >= 2.0 ** -126))
exp = torch.floor(torch.log2(z_ref.abs().clamp_min(2.0 ** -126)))
ulp = torch.pow(torch.tensor(2.0), exp - 7)

# 先分桶，再求和（顺序不能反，否则 NameError）
eq = (diff == 0) & normal
sub1 = (diff > 0) & (diff < ulp) & normal
one = (diff == ulp) & normal
gt1 = (diff > ulp) & normal
buckets = int(eq.sum()) + int(sub1.sum()) + int(one.sum()) + int(gt1.sum())
excluded = z_ref.numel() - int(normal.sum())
print(f"total={z_ref.numel()} valid={int(normal.sum())} excluded={excluded}")
print(f"equal={int(eq.sum())} sub1={int(sub1.sum())} 1ulp={int(one.sum())} gt1ulp={int(gt1.sum())}")
print(f"buckets+excluded={buckets + excluded} == total: {buckets + excluded == z_ref.numel()}")
p_npu = torch.exp(z_npu - torch.logsumexp(z_npu, dim=1, keepdim=True))
p_ref = torch.exp(z_ref - torch.logsumexp(z_ref, dim=1, keepdim=True))
rel = (p_npu - p_ref).abs() / p_ref.clamp_min(1e-38)
print(f"p rel err max={rel.max():.4f} mean={rel.mean():.2e} rows_gt_1e-2={(rel > 1e-2).any(1).sum().item()}/{rel.shape[0]}")
```

适用范围：本节数据仅来自 Ascend950PR（957c/V100、CANN 25.7.rc1.7、triton-ascend 3.6.0、torch 2.14.0）；**A2 未验证**。

## 显式 RNE 复刻（当舍入值继续参与 fp32 数学时必需）

参考路径若把 GEMM 输出先舍到 bf16，再参与 fp32 数学（如 `exp`），实现里**不能写 `.to(tl.bfloat16).to(tl.float32)`**：
编译器会把该往返折叠掉。可复核判别（M=4096、N=4096、K=2048、tile 128×256×64，bf16 输入，比较 `exp(舍入后 logits)` 与
`exp(torch.mm(...).bf16())`）：

| 写法 | 与参考逐位相等的元素 | 说明 |
|---|---|---|
| `.to(tl.bfloat16).to(tl.float32)` 后 `exp` | **868,891 / 16,777,216（5.18%）** | 舍入被折叠，约 95% 元素与参考不同 |
| 显式整数 RNE 后 `exp` | **16,777,216 / 16,777,216（100%）** | 与参考逐位一致 |

显式 RNE（round-half-to-even，bf16 7 位尾数）：

```python
u = acc.to(tl.uint32, bitcast=True)
u = (u + (0x7FFF + ((u >> 16) & 1))) & 0xFFFF0000
rounded = u.to(tl.float32, bitcast=True)
```

复跑：上面这张表由 `r34_gap_probes.py` 的 P1 产生（同一 kernel，只切 `MODE`：0=折叠写、1=显式 RNE）。
环境：Ascend950PR（A5）、CANN 9.2.0-beta.2、triton-ascend 3.6、bf16；换 dtype/编译栈需重跑。

## 判定方法
- 对照定位（不是验收）：把参考自身的中间量喂入本实现，只能说明差异发生在替换点或其上游；上游地址、累加顺序或舍入错误同样会被这次替换掩盖。需分项验证 producer 的读取与 bf16 cast，再按原任务口径判定。
- 逐输出看：一个输出可能通过（例如其中一个输出），另一个输出（另一个输出）被 1-ulp 行污染。
- 容差变更需要独立误差依据并经原任务口径确认；不能用 reference-g 对照结果替代验收，也不要在无依据时更换 golden 设备。

## 规则
- 先判断 reference bf16 GEMM 的舍入，再调 kernel；不要盲目改 tile/barrier。
- 在 sketch/precheck 记录 reference 的 bf16 舍入点。
- 任务/判据层无法复现时，记录 `contract_conflict`；容差变更须有独立误差依据并经任务口径确认。

## 同一代码、CPU/NPU 不同结果

- 同一份 `torch.mm(bf16, bf16)` 参考代码，CPU 与 NPU 的 bf16 累加/舍入不同，结果可差 1 ulp。
- 默认 golden device 应为 NPU（Ascend 算子）；用户明确 CPU 时再用 CPU。
- precheck/sketch 记录 `golden_device`（npu/cpu）与 `golden_source`（user/auto）。
- CPU golden 失败时，先用 NPU golden 复验，再判断 kernel。
