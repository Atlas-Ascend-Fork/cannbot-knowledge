---
type: Optimization
title: Ascend 950 SIMT-Only Discrete Access Pattern
description: Ascend 950 上以 force_simt_only=True 启动离散访存 UB staging kernel，并重调 num_warps 与 grid 分解。
tags: [task.optimization, topic.data_movement.memory_access, topic.programming_model]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/force-simt-only-discrete-access-950.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: ['950']
---
# Ascend 950 SIMT-Only Discrete Access Pattern

## Summary

Launch discrete-access-ub-staging Triton kernels on Ascend 950 with `force_simt_only=True`, then retune `num_warps` and grid decomposition. This profile-gated launch-mode experiment targets kernels whose hot path is primarily scalar/index-driven memory access.

## Use When

The Triton kernel runs on confirmed Ascend 950 hardware, and its hot path is
discrete, index-driven memory access — gather/scatter-style loads, index
arrays, or per-lane pointer arithmetic — with almost no arithmetic on the
loaded values:

```python
offs = row[:, None] * stride + idx[None, :]
vals = tl.load(base + offs, mask=mask)
```

Profiling shows `aiv_scalar_ratio` clearly above both `aiv_vec_ratio` and
`cube_utilization` for this kernel's row in `op_summary_*.csv`. The generic
flat-index-decode-to-layout-tiling repair has been ruled out or already
tried, so the remaining scalar load is architectural rather than a fixable
indexing structure.

## Avoid When

- The kernel is Cube-heavy, matmul-like, or already dominated by vector arithmetic.
- Profiling does not identify the target kernel row confidently by `opName`.
- The scalar ratio is only slightly higher or the bottleneck is host launch overhead, copy overhead, or another operator.
- The shape regime is not representative enough to justify architecture-specific launch-mode changes.
- Scalar overhead mainly comes from flat linear-index traversal with per-lane `//` / `%` coordinate recovery; repair that structure first when the mapping is affine.

## Signals

### Profile

- In `op_summary_*.csv`, `opName` equals or clearly contains the target kernel name.
- `aiv_scalar_ratio` is much larger than `aiv_vec_ratio`.
- `aiv_scalar_ratio` is much larger than `cube_utilization`.
- Low Cube utilization is expected from the kernel semantics, not an accidental symptom of a missed `tl.dot` rewrite.

### Code

- Index arrays, indirect offsets, gather/scatter addresses, masks, or per-lane pointer reconstruction dominate the hot path.
- The computation does almost no arithmetic on the loaded values.
- The kernel looks closer to sparse/discrete movement than SIMT-friendly dense vector math.

## Method

Confirm the fit first: Ascend 950 must be confirmed by the evidence rule
below, the profile row must match the target kernel by `opName`, and the
scalar-dominated hot path must survive the structural-repair check.

The optimization core is to relaunch the kernel with `force_simt_only=True`
and retune launch geometry for SIMT-only mode. Run correctness validation
first and never trust performance numbers from a build that fails precision
or functional comparison. Keep the change only if correctness passes and
measured performance improves across representative shapes, not only one
isolated shape.

### Rule: Confirm Ascend 950 by evidence, not by profiling alone

Accept any of these as Ascend 950 evidence:

- User explicitly states the target is Ascend 950.
- `msprof`/profile metadata, such as `PROF_*/device_*/sample.json` or `PROF_*/host/sample.json`, names an Ascend 950-class target.
- Runtime or compile logs name an Ascend 950-class target, for example `ascend950PR` or `ascend950DT`.
- Runtime device queries such as `torch.npu.get_device_name(0)` or `torch.npu.get_device_properties(0)` report an Ascend 950-class device.
- Environment/CANN target settings clearly name an Ascend 950-class SOC.

If Ascend 950 cannot be confirmed, record this pattern as a candidate only.
Do not apply `force_simt_only=True` solely because `aiv_scalar_ratio` is
high.

### Rule: Repair flat-index decode structure first

If the scalar/index-heavy hot path is mainly a flat `numel` traversal with
per-lane `//` / `%` coordinate recovery, first evaluate the
flat-index-decode-to-layout-tiling repair in the active optimize knowledge
tree. Apply `force_simt_only=True` only after that structural rewrite is not
applicable, is too risky for the guarded shape contract, or has been tried
and the kernel remains scalar/index dominated. This ordering keeps SIMT-only
as an architecture-specific launch-mode experiment instead of masking a
portable layout/indexing fix.

### Rule: Enable SIMT-only launch, then retune launch geometry

Add `force_simt_only=True` to the kernel launch:

```python
_kernel[grid](
    ...,
    BLOCK_SIZE=BLOCK_SIZE,
    num_warps=num_warps,
    force_simt_only=True,
)
```

Then retune the launch parameters, because the best configuration under
SIMT-only mode may differ from the previous best:

- `num_warps`
- grid decomposition
- per-program work size
- block size when it affects scalar/index work

### Rule: Repair compile error 507035 by raising the SIMT stack size

After adding `force_simt_only=True`, compilation may fail with only:

```text
error code is 507035
```

or with error code `507035` plus a more detailed message like:

```text
The Dcache access exceeds the maximum range of the Dcache stack MEM
```

In both cases, the SIMT stack size configured by the active
`torch_npu`/ACL environment may be too small for the generated SIMT kernel.
The repair:

1. Locate the `acl_default.json` used by the current Python/`torch_npu` environment.
2. Back up the original `acl_default.json` before editing it.
3. Add or merge this JSON entry:

   ```json
   {
     "StackSize": {
       "simt_stack_size": 65536
     }
   }
   ```

4. Re-run compilation and correctness validation.
5. If error `507035` remains, adjust `simt_stack_size` further for the environment and shape, then rerun correctness and benchmark checks. Try at most 3 `simt_stack_size` configurations; if compilation still fails, abandon the stack-size repair and switch back to code or launch-parameter changes, or drop the `force_simt_only=True` experiment.
6. If the repair fails or the experiment is abandoned, restore `acl_default.json` to its original backed-up contents before leaving the task.

Treat this as an environment-level repair. Record the original error, the
`acl_default.json` path, the backup/restore action, each stack size tried,
and whether each attempt changed compile, correctness, or performance
behavior. If a successful experiment keeps the modified `acl_default.json`,
make that explicit instead of leaving it implicit.

## What To Verify After Applying

- Correctness/precision remains within the operator's accepted tolerances for all tested dtypes and boundary shapes.
- The round record says whether flat-index decode tiling was absent, ruled out, repaired first, or tried before SIMT-only.
- The round record cites the Ascend 950 evidence source, such as profile metadata, log text, runtime query output, environment setting, or explicit user statement.
- If compile error `507035` was repaired through `acl_default.json`, record each `simt_stack_size` attempt, stop after 3 failed attempts, restore the original JSON on failure or abandoned experiments, and rerun correctness before benchmarking any successful compile.
- `force_simt_only=True` improves representative benchmark results, not only one isolated shape.
- `num_warps` and grid choices were rechecked after changing launch mode.
- A follow-up profile confirms reduced scalar-heavy bottleneck or improved elapsed time for the target kernel row.

## Risks

- `force_simt_only=True` is architecture- and backend-sensitive; it may regress non-Ascend 950 targets or dense vector/Cube kernels.
- The best `num_warps` or grid under SIMT-only mode may differ from the previous best configuration.
- A scalar-heavy profile can point to code-structure problems that should be fixed directly instead of hidden by launch mode.
- Changing `acl_default.json` affects the active runtime environment, so keep the change explicit, reversible, and tied to the measured experiment.

## Related Patterns

- [logical-layout-tiling](./logical_layout_tiling.md): Use layout-aware tiles instead of per-lane div/mod coordinate decoding.
- [simt-window-reduction-tuning](./simt_window_reduction_tuning.md) — Ascend 950 SIMT fixed-window reduction tuning (after SIMT is enabled): Use for Ascend 950 SIMT fixed-window reductions after enabling SIMT launch mode.
- [simt-window-divisor-formula](./simt_window_divisor_formula.md) — closed normalizer inner loop when clipped volume only: Use closed-form clipped bounds when full-window masked counting is costly.
- [现有知识：离散访存优化（gather_out_to_ub 接口）](../operator_optimization/discrete_memory_access.md)
