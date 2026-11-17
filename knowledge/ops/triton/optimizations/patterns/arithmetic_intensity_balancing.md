---
type: Optimization
title: 算术强度均衡
description: 比较每个 tile 的计算与搬运周期，选择匹配瓶颈资源的 tile 大小和工作分配。
tags:
- task.optimization
- topic.tiling
status: stable
sources:
- resource: https://gitcode.com/nitrocoldbrew20/triton-npu-patterns/blob/a31bf998b0998c4d49ed2729c197fb4d801ae7d1/patterns/arithmetic-intensity-balancing.md
  role: primary
- resource: https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf
  role: constraint
created_at: '2026-11-16T06:13:12Z'
platforms:
- a2
- a3
- '950'
updated_at: '2026-11-17T03:37:03Z'
---

# Arithmetic-Intensity Balancing

## Summary

Choose tile sizes and work assignment by comparing estimated per-tile compute
cycles against per-tile memory-transfer cycles, so the bottleneck lands on the
resource whose consumption has a hard floor (FLOPs for matmul-like kernels,
bytes for movement-bound kernels).

## Use When

The hot loop is a `tl.dot`-style contraction or reduction over tiles loaded
from GM, where each loaded operand tile is reused many times within the
iteration (so arithmetic intensity grows with tile size), block sizes,
heads-per-program, or grid mapping are still free parameters, and a profile
or quick estimate shows per-tile compute and per-tile transfer within the
same order of magnitude, so tile choice can actually move which resource is
the bottleneck.

## Avoid When

- Per-byte work is fixed (pure elementwise, no operand reuse scales with
  tile): intensity cannot be tuned by tile size; reduce bytes instead
  (fusion, narrower dtype, materialization elision).
- The measured path is overwhelmingly one-sided (an estimate ratio of
  several times or more): tile changes will not flip the regime.
- Per-block fixed costs (synchronization, launch, prologue/epilogue) or
  program-batch quantization dominate: the per-tile cycle model does not hold.

## Method

### General principle

With good overlap, per-tile time approximates
`max(compute cycles, transfer cycles)`. Every kernel has one resource whose
consumption has a hard floor: matmul-like kernels must perform a fixed number
of MACs, movement-bound kernels must move a fixed number of bytes. The goal
is to make the bottleneck sit exactly on that floor resource: saturate the
cube for GEMM-shaped work, saturate bandwidth for movement-shaped work. Any
other resource being the limiter means performance is being lost to something
compressible.

### Counting cycles

- Compute cycles: per-tile MACs (sum over `tl.dot` calls of `M*N*K`), divided
  by the engine's per-core per-cycle throughput.
- Transfer cycles: count bytes crossing each modeled boundary separately.
  Divide `l2_bytes` by the effective per-core L2 rate and `gm_bytes` by the
  effective per-core GM rate, in bytes/cycle. A cache miss can contribute to
  both counts; an L2 hit does not contribute to GM traffic. Charge invariant
  operands at the frequency they actually cross each boundary.
- Hardware constants (engine throughput, L2/GM bandwidth, core count,
  frequency) differ per chip generation; take them from chip documentation
  or profiler metadata, not from another kernel's measurements.

### Selection rule for dot loops

Evaluate both cycle estimates for each candidate tile shape. When transfer
exceeds compute, the compute engine idles — enlarging the tile raises
arithmetic intensity because reused operands (for example the stationary
operand of the reduction loop) are loaded once but consumed more times.
Under the overlap assumption, prioritize the smallest tested candidate whose
compute estimate covers its transfer estimate. This is a model prediction,
not proof of engine saturation or that larger candidates cannot improve
measured latency; verify allocation and benchmark the candidate.

### Engine branch

- Cube/dot loops: reuse grows with tile size, so intensity is tunable and
  the selection rule above applies.
- Vector/elementwise kernels: per-byte work is fixed, intensity is flat in
  tile size, and no tile choice reaches compute-bound. The actionable
  directions are traffic reduction — see Related Patterns.

### Triton specialization

Source loads alone do not establish L2 residency or actual GM traffic. Use
profiler counters or explicit hit/miss scenarios to estimate L2 and GM bytes
separately; do not infer cache hits merely because a tile fits L2. L1/UB
staging is compiler-controlled and not directly observable from source.
The available knobs are block sizes,
axis ownership and grid mapping, `num_stages`/pipelining depth, and compile
hints. Treat the model as a first approximation: backend scheduling can fail
to overlap, in which case measured time tracks the sum, not the max, of the
two estimates.

## Signals

### Code

- A `tl.dot` reduction loop with `tl.load` of operand tiles whose block
  sizes are free constants.
- An elementwise kernel being repeatedly retiled with no speed change —
  intensity is flat; stop tuning tiles.

### Profile

- GM read traffic dominates the measured path, or the compute pipe shows low
  utilization while the memory pipe is busy.
- The cycle estimate shows transfer cycles exceeding compute cycles at the
  current tile size, with room to grow the tile.

## Related Patterns

- [`tile-footprint-fitting`](tile_footprint_fitting.md): the opposite-direction selection — shrink tiles to fit UB. Use
  this card for the speed direction; combine when both constraints bind.
- [`dot-matmul-rewrite`](dot_matmul_rewrite.md): apply first when the loop is not yet a regular tiled
  `tl.dot`.
- [`software-pipeline`](software_pipeline.md): when measured time tracks the sum rather than the max
  of compute and transfer estimates, overlap is missing.
- [`engine-aware-grid-scheduling`](engine_aware_grid_scheduling.md): grid mapping and program-batch effects, which
  this card's per-tile model does not capture.
- [`dot-operand-precision-ablation`](dot_operand_precision_ablation.md): operand precision moves both the compute
  rate and the byte count, shifting the balance point.
- [`autotune`](autotune.md): use the model to prioritize candidate tiles, then
  confirm their ordering with measurements before narrowing the search.

## What To Verify After Applying

- Benchmark the chosen tile against the parent; the measured ordering should
  track the predicted one.
- If the measured optimum sits far from the predicted balance point, treat
  the gap as new evidence: suspect missing overlap
  (`cube-vector-sync-stall`), program-batch quantization, or unmodeled per-block
  fixed cost, and route back to diagnosis.
- Confirm compiler-reported buffer allocation still fits at the chosen tile.

## Appendix: Ascend 950 Balance Constants

The [official Ascend 950 NPU architecture whitepaper](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) provides
product configurations in Table 3-1 (PDF pages 13–15) and the core/SRAM
layout in Figure 4-1 (PDF page 17). The checked PDF has SHA-256
`ece3405e6a17fabdd462338fb94266558649a6407a2f28008403211387b3a927`.
The table below uses those locations; slash-separated values are distinct
product configurations, not interchangeable inputs for one device.

### Structure

| Quantity | 950PR | 950DT |
| --- | --- | --- |
| AI Core count (1 Cube + 2 Vector cores each) | 32 / 28 | 36 / 32 / 28 |
| L1 per AI Core | 512 KB | same |
| L0A / L0B per AI Core | 64 KB / 64 KB | same |
| L0C per AI Core | 256 KB | same |
| UB per Vector Core | 256 KB each (UB0 and UB1); not one shared 512 KB allocation | same |
| L2 capacity | 128 / 112 MB | 128 MB |
| GM (on-package memory) bandwidth | 1.6 / 1.4 TB/s | 4 TB/s |

### Engine throughput (dense, TFLOPS)

| Engine | Dtype | 950PR | 950DT |
| --- | --- | --- | --- |
| Cube | BF16/FP16 | 432 / 378 | 486 / 432 / 378 |
| Cube | TF32 | 216 / 189 | 243 / 216 / 189 |
| Cube | FP8/HiF8 | 865 / 756 | 973 / 865 / 756 |
| Vector | BF16/FP16 | 54 / 47 | 60 / 54 / 47 |
| Vector | FP32 | 27 / 23 | 30 / 27 / 23 |

### Evidence gaps and per-core conversion

The cited whitepaper does not establish the previously listed L2 bandwidth
(~5 TB/s), operating frequency (~1.65 GHz), HF32-dependent MAC rates
(4096/256), Vector MAC rate (256), outstanding MTE2 count (16), FixPipe rate
(128 B/cycle), instruction-cache sizes, or L1 bank split. No independently
readable engineering-note location is supplied for these claims. Do not use
them as verified device constants or derive ~95/~30 B/cycle from them for
production tile selection. Obtain configuration-specific documentation or
measured rates first. In particular, an illustrated engine shape alone does
not establish an instruction's sustained throughput in every precision mode.

For a known configuration, `total_bytes_per_second / active_core_count /
frequency_hz` is an equal-share estimate, not a guaranteed per-core rate.
Use the same core basis for compute and memory rates and distinguish peak
from sustained bandwidth. Figure 4-1 has one Cube and two Vector cores,
with separate 256 KB UB0/UB1; do not treat their sum as one allocatable buffer.
Model the actual vector work split instead of assuming ideal two-core balance.

Choose bandwidth according to the traffic path: L2-resident reads avoid GM
traffic, while streaming misses consume GM bandwidth and may also consume
L2 bandwidth. Capacity alone does not prove cache residency. The actual
hit rate, concurrency and scheduling determine which boundary limits time.

## Appendix: Worked Estimation Template

Generic per-tile cycle estimate for a `tl.dot` reduction loop. Supply actual
or explicitly hypothesized `l2_bytes` and `gm_bytes`, including reads and
writes at each boundary. The same byte may cross both boundaries. Charge
loop-invariant operands once per program only if that matches the traffic.

This steady-state model assumes L2 and GM service overlap, giving
`mem = max(l2_cycles, gm_cycles)`, and compute overlaps with transfers,
giving `tile = max(cube_cycles, mem)`. For serialized service use the sum
of the two transfer estimates; without compute/transfer overlap add compute
cycles too. Neither model captures launch cost, dependent miss latency,
contention or pipeline fill/drain; validate against measured execution.

```python
def cycles_per_tile(m, n, k, *, dots, l2_bytes, gm_bytes, hw):
    """Steady-state estimate with overlapping L2 and GM service."""
    cube = dots * m * n * k / hw["cube_mac_per_cycle"]
    l2 = l2_bytes / hw["l2_bytes_per_cycle_per_core"]
    gm = gm_bytes / hw["gm_bytes_per_cycle_per_core"]
    return cube, max(l2, gm)

# Illustrative inputs only: not verified constants for any 950 product.
EXAMPLE_HW = {
    "cube_mac_per_cycle": 4096,
    "l2_bytes_per_cycle_per_core": 95,
    "gm_bytes_per_cycle_per_core": 30,
}
for label, gm_bytes in (("L2 hit", 0), ("GM miss", 3000)):
    cube, mem = cycles_per_tile(20, 20, 512, dots=1,
                                l2_bytes=3000, gm_bytes=gm_bytes,
                                hw=EXAMPLE_HW)
    bound = "compute" if cube >= mem else "memory"
    print(f"{label}: cube={cube:.0f} mem={mem:.0f} -> {bound}")
# L2 hit: cube=50 mem=32 -> compute
# GM miss: cube=50 mem=100 -> memory
```

The examples hold compute work and L2 traffic fixed to isolate the effect
of a miss. With serialized L2/GM service the miss transfer estimate would
instead be `3000/95 + 3000/30`, about 132 cycles.

Among the evaluated candidates and under the stated model, prioritize the
smallest candidate estimated as compute-bound, then verify correctness,
resource use and measured latency. If all evaluated candidates are estimated
as memory-bound, investigate traffic reduction or other candidates. This
result does not prove that every possible tile is memory-bound and does not,
by itself, justify canceling all tile-size autotuning.
