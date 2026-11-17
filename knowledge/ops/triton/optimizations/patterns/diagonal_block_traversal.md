---
type: Optimization
title: 对角块遍历
description: 用对角线块遍历改变 program 执行顺序，在保持覆盖的前提下检验缓存复用。
tags:
- task.optimization
- topic.tiling
status: stable
sources:
- resource: https://gitcode.com/nitrocoldbrew20/triton-npu-patterns/blob/a31bf998b0998c4d49ed2729c197fb4d801ae7d1/patterns/diagonal-block-traversal.md
  role: primary
created_at: '2026-11-16T06:13:12Z'
platforms:
- a2
- a3
- '950'
updated_at: '2026-11-17T03:37:03Z'
---

# Diagonal Block Traversal Pattern

## Summary

This pattern changes which program owns each output tile within one existing launch. It may improve cache locality when neighboring programs repeatedly touch the same regions, but the cause and benefit are target-dependent; compare it with the existing traversal and do not treat it as a host launch-count change.

## Use When

A large tiled matrix-style kernel is tiled reasonably, but profiling shows
poor cache locality: the programs running concurrently on the cores (a program
batch) touch many distinct operand regions at once, so L2 reuse is
lost. The grid spans many blocks along both M and N, so traversal order is a
real lever. Reordering which program computes which tile lets programs that
read the same data run at the same time, so shared data is fetched from
memory once per program batch instead of many times.

## Signals

### Code

- Traditional row-major or horizontal block assignment makes many cores touch the same left-matrix cache region at once.
- The matrix already spans many blocks along both `M` and `N`, so traversal order is a plausible performance lever rather than a cosmetic rewrite.
- The right-hand matrix is large enough that ordinary block traversal can churn L2 and lower reuse.

## Detail

Diagonal traversal changes the *order* of output tiles, not the tile compute body itself.
With ordinary row-major traversal, a `4 x 4` tile grid is visited like this:

```text
0  1  2  3
4  5  6  7
8  9 10 11
12 13 14 15
```

Inside a diagonal group, the same region is visited one diagonal stripe at a time instead:

```text
0  4  8 12
13  1  5  9
10 14  2  6
7 11 15  3
```

That small traversal change can reduce cases where many programs hammer the same cache region at once.
The example below keeps only the traversal logic and leaves the usual load / `tl.dot` / store body implied.

```python
@triton.jit
def matmul_kernel(
    mat_a,
    mat_b,
    mat_c,
    M,
    N,
    K,
    num_cores: tl.constexpr,
    BLOCK_M: tl.constexpr,
    BLOCK_N: tl.constexpr,
    BLOCK_K: tl.constexpr,
    DIAGONAL_GROUP: tl.constexpr,
):
    pid = tl.program_id(0)
    num_blocks_m = triton.cdiv(M, BLOCK_M)
    num_blocks_n = triton.cdiv(N, BLOCK_N)
    num_blocks = num_blocks_m * num_blocks_n

    use_diagonal = (
        num_blocks_m >= DIAGONAL_GROUP
        and num_blocks_n >= DIAGONAL_GROUP
        and num_blocks_m % DIAGONAL_GROUP == 0
        and num_blocks_n % DIAGONAL_GROUP == 0
    )

    # Launch exactly num_cores programs, or use tl.num_programs(0) here.
    for block_idx in range(pid, num_blocks, num_cores):
        if use_diagonal:
            group_blocks = DIAGONAL_GROUP * DIAGONAL_GROUP
            groups_per_row = num_blocks_n // DIAGONAL_GROUP

            group_idx = block_idx // group_blocks
            local_idx = block_idx % group_blocks

            group_m0 = (group_idx // groups_per_row) * DIAGONAL_GROUP
            group_n0 = (group_idx % groups_per_row) * DIAGONAL_GROUP

            local_m = local_idx % DIAGONAL_GROUP
            diagonal_step = local_idx // DIAGONAL_GROUP
            local_n = (local_m + diagonal_step) % DIAGONAL_GROUP

            task_m_idx = group_m0 + local_m
            task_n_idx = group_n0 + local_n
        else:
            task_m_idx = block_idx // num_blocks_n
            task_n_idx = block_idx % num_blocks_n

        m_start = task_m_idx * BLOCK_M
        n_start = task_n_idx * BLOCK_N

        # Use (m_start, n_start) with the usual tiled matmul body here.
        # The optimization is the traversal order, not a different dot kernel.
```

This compact example assumes diagonal traversal only for full `DIAGONAL_GROUP x DIAGONAL_GROUP`
regions. Tail groups can fall back to ordinary traversal if partial-edge handling would make the
mapping harder to reason about than the expected cache benefit justifies.

## Related Patterns

- [`l2-stripe-capacity-tile-widening`](l2_stripe_capacity_tile_widening.md): the tile-shape half of the L2 problem — widen the reused-side tile when the streamed operand's re-read count, not the traversal order, is what exceeds L2.
- [`engine-aware-grid-scheduling`](engine_aware_grid_scheduling.md): program-to-batch mapping and persistent stride loops; diagonal traversal is one ordering candidate inside that mapping.
