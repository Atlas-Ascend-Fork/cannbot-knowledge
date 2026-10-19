---
type: Optimization
title: Int8 Dot With Int32 Accumulator
description: int8 量化 GEMM 默认采用 int32 累加的原生 int8 tl.dot，UB 不足时降级 tile 几何而非回退加宽操作数。
tags: [task.optimization, topic.precision, topic.compute.quantization, topic.tiling]
status: stable
sources:
- resource: https://gitcode.com/AgenticCompiler/BiShengKernelAgent/blob/21053d2fd6e8d7bb885dec66d887dd9e75014c5f/skills/triton/triton-npu-optimize-knowledge/references/patterns/int8-dot-int32-accumulator.md
  role: primary
created_at: '2026-10-15T02:12:54Z'
updated_at: '2026-10-15T02:12:54Z'
platforms: [a2, a3, '950']
---
# Int8 Dot With Int32 Accumulator

## Summary

In an int8-by-int8 quantized GEMM (per-channel scale, optional bias / pertoken / offset), make the native int8 `tl.dot` with an **int32 accumulator** the default structure for every exact tile, and respond to UB overflow at wide tiles by **demoting the tile geometry** (e.g. 128x128 -> 64x128 with a doubled grid) instead of reverting the operand path to fp16-widened dot. The int32-to-fp32 conversion happens once in the epilogue.

## Use When

Your operator is an int8×int8 quantized GEMM with dequant scales applied
after the integer reduction. The current kernel widens
the int8 operands to fp16 or fp32 before `tl.dot` and accumulates in fp32. A
typical example:

```python
a = a_tile.to(tl.float16)   # int8 operands widened before the dot
acc += tl.dot(a, b)         # acc is fp32
```

With int8 inputs, every product and partial sum is computed without
rounding, and you can prove the int32 accumulator cannot overflow for the
largest supported K and value bounds.

The native int8 dot with an int32 accumulator runs the faster integer MMAD
path with half the operand footprint of the fp16-widened form.

## Avoid When

- Inputs are not int8 by contract (then this becomes a `dot-operand-precision-ablation` ablation with a real accuracy contract).
- The epilogue needs the fp32 accumulator to stay live across a long chain that cannot be restructured.
- The target lowering lacks an int8 MMAD path (verify IR: expect xi8 MMAD + xi32 accumulator).

## Signals

### Code

- `x1.to(tl.float16)` / `x2.to(tl.float16)` immediately before `tl.dot`, with `acc = tl.zeros(..., tl.float32)`.
- `INT8_DOT`-style constexpr gates that enable the native path only for a few shapes while wide tiles keep the widened path.

### Compile

- UB overflow when enabling int8 on wide tiles, driven by the i32 accumulator plus the conversion epilogue and not scaling with K.

### Profile

- Kernel time dominated by the widened-operand dot while the int8 alternative compiles on narrower geometry.

## Method

Confirm the fit first: the inputs must be int8 by contract, and the accumulated int32 range must be proven for the largest supported K and value bounds. Compare the native integer accumulation against the reference accumulation semantics before making it the default path.

The optimization core is to make the native int8 `tl.dot` with an int32 accumulator the default structure for every exact tile, with a single int32-to-fp32 conversion in the epilogue, and to hold that structure when wide tiles overflow UB by shrinking the tile instead of the operand width.

### Rule: Default every exact tile to int8 dot with an int32 accumulator

```diff
- acc = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)
+ acc = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.int32)
  ...
- a = a_tile.to(tl.float16); b = b_tile.to(tl.float16)
- acc += tl.dot(a, b)
+ acc = tl.dot(a_i8, b_i8, acc)
  ...
  out_tile = acc.to(tl.float32) * scale   # unchanged epilogue; single conversion site
```

The int32-to-fp32 conversion happens once in the epilogue; scale, bias, pertoken, and offset semantics are unchanged.

### Rule: Answer UB overflow by demoting tile geometry, not widening operands

The i32 accumulator plus the conversion epilogue is a fixed UB cost that does **not** scale with K. When a wide tile overflows UB, demote one tile dimension and double the grid (e.g. 128x128 -> 64x128, or BN 256 -> 128) and keep the native int8 path. Falling back to fp16-widened dot forfeits the MMAD gain on the shapes that dominate runtime. A leaner epilogue can make a previously over-large tile fit, so retest the demotion point per kernel structure and size it jointly with the tile search per `tile-footprint-fitting`.

Discipline note: when you demote a tile, keep the int8 path and the epilogue fixed, and retest UB fit and accuracy before attempting any further tile change.

## What To Verify After Applying

- IR shows xi8 MMAD with xi32 accumulator; no fp16 widening remains on exact tiles.
- UB fit per (BLOCK_M, BLOCK_N) after demotion; the demotion rule covers every exact shape in the operator domain.
- Epilogue performs exactly one int32-to-fp32 conversion; scale/bias/pertoken/offset semantics unchanged.
- Accuracy against the widened reference, repeated across supported K, value, dtype, and tile regimes.
