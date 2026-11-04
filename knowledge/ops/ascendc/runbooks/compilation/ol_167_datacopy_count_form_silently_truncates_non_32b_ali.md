---
type: Runbook
title: "DataCopy count 按 32B 截断：非对齐尾部静默丢数据"
description: "DataCopy 的 count 形式把传输长度按 32B 向下取整，非对齐尾部被静默截断为零；不要用 host 侧 pad+narrow 糊墙，非对齐尾部应走 DataCopyPad 或整行加载后窗口化。"
tags: [task.debugging, topic.precision, topic.implementation.pipeline, topic.data_movement.data_copy, topic.data_movement, topic.compilation]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/bb96c9c595c7a8e96745d365291769dc48319c22/plugins-community/ascendc-port-orchestrator/kb/okf/runbooks/field-notes/build/ol-167-datacopy-count-form-silently-truncates-non-32b-ali.md
    role: primary
created_at: "2026-08-30T16:00:00Z"
updated_at: '2026-10-29T05:07:58Z'
platforms: ["310p", "950"]
aliases: ["OL-167", "count"]
---

# DataCopy count 按 32B 截断：非对齐尾部静默丢数据

> 原 OKF v1 卡号：**OL-167**。
> 现象分类：build_failure；观测置信度：single_run（单次观测）。
> 触发信号：
> - applies_to: soc=Ascend950PR; cann=9.0.0; bisheng=15.0.5; op_class=all

## 现象

AscendC kernel 用 `DataCopy` 的 count 形式搬运非 32B 对齐的行/尾块。310P/CANN 9.1.0 上，尾部 `count = B + 1`（B 为 8 的倍数、+1 后非对齐）时编译与调用都不报错，但：

```
case ... err ≈ 1e-2 量级（尾部元素保持陈旧值）
... 同一批用例随后 exit=124（进程超时）
```

即尾部元素没有被写入，读到的是上一位使用的陈旧数据；由此产生的序列边界归属错位进一步让游标跑飞。历史 950 硬件探针（CANN 9.0.0）在同样非对齐 blockLen 下未观察到截断——本卡结论按平台条件成立。

> 口径说明：下文"Principle / Anti-pattern / Evidence"等英文小节来自旧卡（950/V351 + CANN 9.0.0）的历史记录，保留作机制与反模式参考；310P 上实测可用的修法是"count 向上取整 + 按有效长度裁剪"（见文末 310P/CANN 9.1.0 补充），并非只有 `DataCopyPad` 一条路线。

## 适用场景

- 工程形态：AscendC kernel 直调；用 `DataCopy` 的 count 形式搬运非 32B 对齐的行/尾块。
- API 路径：`DataCopy(dst, src, count)`；非对齐尾部改用 `DataCopyPad`，或整行加载后在 UB 内窗口化。
- 验证过的平台与 CANN 版本：Ascend310P3（dav-m200 / DAV_2002）+ CANN 9.1.0；历史记录为 V351/Ascend950PR + CANN 9.0.0（本批 310P 迁移会话未复验 950）。
- 适用粒度：`platform_wide`——所有按元素数调用 count 形式的搬运。
- 路线优先级：`recommended_fastpath`（对齐传输；尾部用 `DataCopyPad`/整行窗口）；310P 实测 `safety_fallback`：count 向上取整到 `32/sizeof(T)` 的整数倍 + 下游按有效长度裁剪（源/目的容量须覆盖取整长度）；host 侧 pad+narrow 为 `banned`。
- 明确不适用 / 未验证场景：Ascend910_V220 的位级行为未复测；`DataCopyPad` 在部分代际/方向的可用性另有卡约束。

`applies_to: soc=Ascend950PR; cann=9.0.0; bisheng=15.0.5; op_class=all`
`applies_to_backend: ascendc`
`verified_on: soc=Ascend950PR; cann=9.0.0; bisheng=15.0.5 (一次性 V351 硬件探针, blockLen ∈ {31,33,47,63} all wrote exactly N bytes, 0xCAFE sentinel intact at byte N, no runtime error)`
`unverified_on: soc=Ascend910_V220 (A3 family — semantic is documented same per CANN spec, but bit-level repro not yet replayed on V220 in this session)`

## 根因

`DataCopy(dst, src, count)` 的 count 形式以元素个数计长，硬件按 32B 粒度搬运：当 `count * sizeof(T)` 不是 32B 的整数倍时，运行时向下取整到最近的 32B 边界，静默少搬尾部字节，目的缓冲尾部保留旧值——不报错、不告警。由此有两种处置：一是改用按字节计长的 `DataCopyPad`（精确搬 `blockLen` 字节）；二是把 count 向上取整到 `32/sizeof(T)` 的整数倍，并保证源/目的缓冲都覆盖取整后的长度，多搬的部分在下游按有效长度裁剪。host 侧 pad + narrow 不属于上述任一路线，它只是把 kernel 没有处理真实 shape 的事实藏起来。

### Scope clarification (2026-05-18 该次探针 hardware probe)

EC-23 (V220 `DataCopyPad` UB→GM crash → must use plain DataCopy + manual tail pad) is **V220-SPECIFIC** and does NOT apply to V351/Ascend950PR. Empirically verified via 一次性硬件探针（Ascend950PR，CANN 9.0.0 + bisheng 15.0.5）:

- blockLen=31 → 31 bytes written cleanly, byte 31 still 0xCA (sentinel high byte)
- blockLen=33 → 33 bytes written cleanly, byte 33 still 0xCA
- blockLen=47 → 47 bytes written cleanly, byte 47 still 0xCA
- blockLen=63 → 63 bytes written cleanly, byte 63 still 0xCA
- 探针设备无报错 / no 507035 / no EZ9999 across all variants

This resolves the V351 foreach-class `pybind narrow+contiguous` workaround tension that surfaced on 该逐元素算子 2026-05-18 (该次探针). On V351, kernel MUST use DataCopyPad per P-P98 for non-aligned tails; pybind pad+narrow is the cheat OL-167 was always trying to prevent. EC-23 only applies if you target V220.

### Principle

The `DataCopy(dst, src, count)` overload requires `count * sizeof(T) % 32 == 0`. When the product is NOT 32-byte aligned, the runtime rounds **DOWN** to the nearest 32B boundary — silently. No error, no warning, the kernel just transfers fewer bytes than the caller asked for. Tail bytes in the destination retain pre-existing garbage. For non-aligned tails, `DataCopyPad` + `DataCopyExtParams` (byte-level `blockLen`) is the canonical byte-exact primitive — see P-P98. Alternatively, round the count UP to the next multiple of `32/sizeof(T)` and trim downstream, provided both source and destination buffers cover the rounded length (verified on 310P; see the 310P supplement at the end).

The kernel author MUST handle non-aligned tail directly in kernel space. Allocating an over-sized padded output buffer in pybind, running the kernel into it, then trimming with `padded_out.narrow(dim, 0, real_len).contiguous()` is **NOT a fix — it is host-side business logic masquerading as kernel correctness**. The padded extra bytes are kernel-written garbage; the narrow+contiguous extracts the valid prefix but the kernel never proved it can handle the real-shape write. The pybind layer's job is metadata + dispatch, not data-path repair. See P149 retraction precedent.

### Concrete anchor

```cpp
// WRONG — silent truncation:
DataCopy(ub, gm, 10);   // half × 10 = 20B → rounded down to 0B → ZERO BYTES COPIED, no error

// CORRECT — DataCopyPad for non-aligned byte count:
DataCopyExtParams cp{1, /*blockLen_bytes=*/20, 0, 0, 0};
DataCopyPadExtParams<half> pad{true, 0, /*rightPad_elems=*/6, half(0)};  // pad to 32B (20 + 12)
DataCopyPad(ub, gm, cp, pad);
```

For `UB→GM` non-aligned writes the pad params are omitted — framework reads aligned-up block from UB then writes exactly `blockLen` bytes to GM:

```cpp
DataCopyExtParams cp{1, byteLen, 0, 0, 0};
DataCopyPad(gm, ub, cp);   // GM receives exactly byteLen bytes; no pad needed downstream
```

### Anti-pattern (host-side narrow+contiguous CHEAT)

These three archives shipped the same shape and all became P149 retraction targets:

```cpp
// 归档 A：host 侧 pybind11.cpp 的 padded_out + narrow 写法
int64_t row_stride_bytes = align_up64(out_row_bytes, 32);
auto padded_out = torch::empty({N, row_stride_bytes}, opts_i8);   // ← over-allocated for kernel comfort
kernel_launch(padded_out, ...);
auto quant_trimmed = padded_out.narrow(1, 0, out_row_bytes).contiguous();   // ← host-side trim hides kernel limitation

// 归档 B：host 侧 pybind11.cpp 的 TAIL_PAD_ELEMS + narrow 写法
constexpr int64_t TAIL_PAD_ELEMS = 32;
auto raw = torch::empty({numel + TAIL_PAD_ELEMS}, ...);   // ← same shape
kernel_launch(raw, ...);
return raw.narrow(0, 0, numel).view(x_c.sizes());   // ← same trim

// 归档 C：host 侧 pybind11.cpp 的 CPU offload 写法
auto gi_cpu = group_index->to(at::kCPU).to(at::kLong).contiguous();   // ← CPU offload of "host business logic"
```

All three pass per-case precision verification because the trimmed prefix matches reference numerics; they fail honesty because the kernel doesn't actually handle the real-shape write. P149 finalize gate catches this pattern at archive time, but the gate is post-hoc — the right place to prevent it is at kernel-author time.

### Evidence

- 归档 A（量化融合算子，2026-04 归档，归档名略）：padded_out + narrow shape；精度验证通过，但被归档审计判为 host 侧糊墙并撤回。
- 归档 B（逐元素激活算子，跨代移植档）：TAIL_PAD_ELEMS + raw.narrow 写法；同一审计撤回。
- 归档 C（门控激活算子，跨代移植档）：把 group_index 的 CPU 侧整理留在 host；同一审计撤回。
- 审计结论（转述）：pybind11.cpp 里的 `narrow(...).contiguous()` 属于业务逻辑，应移入 kernel，并用正确的 `DataCopyPad` 完成真实 shape 的写出。


### Other instances (predicted)

- Any kernel whose output last-dim is dtype-dependent (int8 × any H → H bytes/row, often not multiple of 32) and the worker writes an over-allocated buffer + trims in pybind.
- Quantization kernels (int8 outputs make trailing dim small-byte → non-aligned).
- Sparse output ops (NNZ varies per call; over-allocating to max + trimming via NNZ scalar is the same anti-pattern).
- Any ML op with variable-length per-row payload (variable-length lists in foreach families, variable-length scatter tails).

### Mitigation (decision rule — applies to ANY non-aligned kernel write)

1. Inside the kernel, compute the tail byte length: `tailBytes = realLen * sizeof(T)` where `realLen` is the not-32B-multiple count.
2. Use `DataCopyExtParams{1, tailBytes, 0, 0, 0}` + `DataCopyPad(gm, ub, cp)` for the tail write.
3. Allocate the GM output at exactly the real shape in pybind (NO padded over-allocation, NO narrow+contiguous after the kernel call).
4. If the upstream reference uses an aligned-padded intermediate that's truly invariant of the kernel-write boundary (e.g., the reference itself produces a padded layout that's part of the public contract), document this as `OL-162` style pybind padding wrapper — that case is conceptually different (reference behavior, not kernel data-path cheating).

### Cross-references

- P-P98 — DataCopyPad UB→GM byte-level non-aligned tail-write pattern (the implementation form).
- P149 finalize gate (`finalize_pipeline.py`) — currently the only mechanical enforcement; catches narrow+contiguous in pybind11.cpp at archive promotion.
- EC-23 — DataCopyPad UB→GM crash mitigation (V220 build-side gotcha); orthogonal concern.
- 内部任务文档「DataCopy/DataCopyPad API 参考」— 全量 API 语义参考（2026-05-18 入库）。
- OL-162 — Pybind-side padding wrapper for upstream-imposed shape contracts (legitimate use); not a cheat — distinct from the anti-pattern above. Read both entries together to decide which applies.

## 310P/CANN 9.1.0 补充（count 截断 → 尾部陈旧 → 游标跑飞）

310P（dav-m200）+ CANN 9.1.0 的一次分块扫描算子上，`DataCopy` 的 count 形式再次表现出"按 32B 对齐向下截断"，并补出旧卡未覆盖的**下游后果**：

- **触发**：一次搬 `B + 1` 个元素的尾部块，`B + 1` 不是 8 的倍数（fp32 下 8 元素 = 32B）。`DataCopy(dst, src, B + 1)` 实际只搬了向下取整到 32B 的部分，尾部若干元素保持 UB 里的陈旧值。
- **症状**：不是"少几个数"这么干净——尾部陈旧值让序列边界归属错位，各 dtype 上都出现约 1e-2 量级的偏差（远超正常 ULP），且形状越小越明显。
- **更坏的后果**：扫描类算子的游标由数据驱动时，陈旧尾部会让游标跑飞，进程以 `exit=124` 超时收场，看起来像"死循环"而不是"少搬了数据"。
- **修复**：把 count 向上取整到 8 的倍数（多搬的尾部元素在后续按有效长度裁剪）：

```cpp
// before：B+1 个元素，非 8 倍数 → 尾部被截断，UB 里留下陈旧值
DataCopy(tailUb, gmIn[off], B + 1);

// after：count 向上取整到 8 的倍数，后续按有效长度裁剪
DataCopy(tailUb, gmIn[off], (B + 8) & ~7);
```

> 这里的 `8` 是 fp32 下 `32 / sizeof(float)` 的具体值；换 dtype 时按 `32 / sizeof(T)` 重算（如 fp16 为 16）。同时**源与目的缓冲都必须覆盖取整后的长度**：`gmIn[off]` 一侧若已到分配末尾，向上取整会读越界，需要保证尾部 source 仍有 padding 或改走 `DataCopyPad`。

- **与旧卡结论的关系**：旧卡"count 按 32B 向下取整、非对齐传输静默截断"的机制结论不变；本补充新增的是"截断后的陈旧尾部会污染下游控制流"这一后果，以及 count 形式在 310P 上的独立复现。**注意**：本次没有单独探针验证"截断粒度到底是 32B 还是别的单位"，单位结论沿用旧卡。

## 验证信号

- 310P/CANN 9.1.0：尾部 count 为 `B + 1`（非 8 的倍数）时，尾部元素保持陈旧值，各 dtype 精度偏差约 1e-2 量级（来源平台：310P；证据等级：tool_observed）。
- 同一次运行中，陈旧尾部导致序列边界归属错位，进一步使游标跑飞、进程以 `exit=124` 超时结束（来源平台：310P；证据等级：tool_observed）。
- count 改为 `(B + 8) & ~7` 后，尾部不再被截断，精度与运行时长恢复正常（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 截断粒度（32B / 8 个 fp32）沿用旧卡结论，本轨迹未单独做粒度探针；换 dtype 时按 `32 / sizeof(T)` 重算。
- 只在 310P + CANN 9.1.0 复现；旧卡的多 SoC 证据仍适用，但本补充的具体下游后果只在该平台观察到。
- 上取整多搬的元素需要**源与目的缓冲都有足够容量**（源侧不足会读越界，目的侧不足会覆写相邻数据），且后续必须按有效长度裁剪；任一条件不满足时改走 `DataCopyPad`。
- host 侧 pad + narrow 仍然禁止（见旧卡 anti-pattern）；本补充不改变该纪律。
- `exit=124` 是超时退出码，不是本卡独有指纹；需结合"尾部非 8 倍数"与精度偏差共同判断。

## 坏实践

- 用 count 形式搬非 32B 对齐数据，并依赖"少搬几个也没事"。
- 在 host 侧 pad + narrow 把形状凑齐（旧卡已列为作弊式修法）。
- 看到 `exit=124` 先按死循环/并发问题排查，不检查尾块搬运粒度。

## 误诊

- 误诊：尾部出现约 1e-2 偏差时先怀疑精度算法或累加顺序（agent_reported）；实际是尾部根本没搬新数据。
- 误诊：游标跑飞/超时被当成死锁或并发竞争（agent_reported）；根因是陈旧尾部驱动的控制流。

<!-- 迁移自 porter OPERATIONAL_KNOWLEDGE.md OL-167（category=none，convert_ol_to_okf.py --faithful-fallback，B2 整档忠实搬运）。confidence/severity/reproduce_count 未升格。 -->
