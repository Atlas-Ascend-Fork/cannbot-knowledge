---
type: Optimization
title: "Software MXFP8 dequant on the VEC pipe for reduction-class ops"
description: "LoadDataWithMxScaling (hardware MX) is CUBE-only; VEC reduction ops reading MXFP8 must software-dequant: Cast<float,fp8_e4m3fn_t> then per-32-block E8M0 scalar Muls before the reduction."
tags: [task.optimization, topic.implementation.synchronization, topic.implementation.pipeline, topic.programming_model.execution_unit.cube, topic.programming_model.execution_unit.vector, topic.data_movement.data_copy]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/bb96c9c595c7a8e96745d365291769dc48319c22/plugins-community/ascendc-port-orchestrator/kb/okf/runbooks/operator-optimization/ol-170-software-mxfp8-dequant-vec-pipe.md
    role: primary
  - resource: https://www.opencompute.org/documents/ocp-microscaling-formats-mx-v1-0-spec-final-pdf
    role: primary
created_at: "2026-07-12T16:00:00Z"
updated_at: "2026-10-20T04:40:45Z"
platforms: ["950"]
---

# Software MXFP8 dequant on the VEC pipe for reduction-class ops

> 原 OKF v1 卡号：**OL-170**。

## 优化点 / 选型

Applies to `soc=Ascend950PR, cann=9.1.0, bisheng=15.0.5+2026-04-13,
op_class=mx-format-vec-only` (LayerNorm, RMSNorm, Softmax, any reduction-class op reading MXFP8).
Verified on `soc=Ascend950PR_957c, cann=9.1.0.B010, benchmark=MxFp8LayerNorm`. Unverified on
Ascend910_V220 (A3 has `fp8_e4m3fn_t` but ToFloat constraints differ).

**Principle**: The hardware MX path (OL-145, `LoadDataWithMxScaling`) is **CUBE-only** — it ships
`(data, e8m0_scale)` from L1 → L0A/L0B → Mmad for matmul-class ops. For pure-VEC
reduction/normalization ops (LayerNorm, RMSNorm, Softmax) that consume MXFP8 inputs, the kernel must
do **software dequant in the vector pipe** before the reduction:

1. Load `D` uint8 bytes of E4M3 data + `D/32` uint8 bytes of E8M0 scale per row into UB.
2. Reinterpret the data uint8 buffer as `fp8_e4m3fn_t` (zero-cost view cast) and call
   `Cast<float, fp8_e4m3fn_t>(dst_fp32, src_fp8, RoundMode::CAST_NONE, D)` — the native AscendC
   dequant of the E4M3 mantissa to fp32 (V351-supported fp8 types per OL-145).
3. Per 32-element block, decode the E8M0 byte and broadcast-multiply the block via
   `Muls(xF32[b*32], xF32[b*32], scale, BLOCK_SIZE)`. For bytes `0..254`,
   `scale = 2^(byte - 127)`; byte `255` denotes NaN, not infinity. A direct fp32 exponent-field
   construction `uint32_t(byte) << 23` is correct only for bytes `1..254`: byte `0` needs
   fp32 bits `0x00400000` (the subnormal `2^-127`), while byte `255` needs a NaN encoding
   (for example `0x7fc00000`). Use the guarded decoder and exhaustive CPU check in
   [CAND-PP96](../runbooks/runtime/e8m0_shared_exponent_to_fp32_union_bit_reinterpret.md).
4. From here the kernel sees standard fp32 — apply the normal reduction tree (OL-115 / P-P45) and
   affine math.

**Why software, not hardware MX**: `LoadDataWithMxScaling` is wired to the Cube fixed-point pipeline
(L0A/L0B → Mmad), not to VEC. The VEC pipe has no native "load fp8 with per-block scale and dequant
on read" intrinsic on Ascend950PR. The two-step software dequant (E4M3 native cast + E8M0
scalar-broadcast Muls) costs about 1 VEC instr per 32-element block on top of the standard fp32
reduction — negligible vs the MTE2/HBM cost in the bandwidth-bound regime.

**Concrete anchor** (op#MxFp8LayerNorm kw-1, 2026-05-20):
```cpp
auto xDataFp8 = xData.ReinterpretCast<fp8_e4m3fn_t>();
Cast(xF32, xDataFp8, RoundMode::CAST_NONE, norm_size_);
PipeBarrier<PIPE_V>();
for (int32_t b = 0; b < n_blocks_; b++) {
    uint8_t sb = scalesLocal.GetValue(b);
    float scale = E8m0_byte_to_scale(sb);   // guarded: 0 -> 2^-127; 255 -> NaN
    Muls(xF32[b * 32], xF32[b * 32], scale, 32);
}
PipeBarrier<PIPE_V>();
```

**Constraints**: `D` (last/normalized dim) MUST be a multiple of 32. The block axis is the inner axis
and never crosses row boundaries — this gives the op batch-invariance by construction. The scales
tile must be padded to a 32-byte multiple for `DataCopy` alignment (allocate
`n_blocks_padded = align_up(n_blocks, ...)`).

**E8M0 correction boundary**: OCP MX v1.0 (September 2023), §5.4.1 Table 7, printed p.14,
defines bias 127, finite exponent range `-127..127`, no zero or infinity, and `0xff` as NaN.
This agrees with the finite range in the existing [builtin data types table](../apis/simd_api/basic_api/data_structures/builtin_data_types.md)
and the route-specific [MXFP4 NaN byte case](../runbooks/precision/mx_fp4_nan_device_e8m0_0xff_fp4_0x0.md).
The endpoint correction is an IEEE fp32 representation check; it adds no device measurement of
subnormal handling, FTZ, NaN propagation, or the corrected helper's cost. Historical LayerNorm
results do not establish that either endpoint was exercised.
