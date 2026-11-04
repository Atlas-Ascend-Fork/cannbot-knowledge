---
type: Runbook
title: "DataCopyPad 后标量读：MTE2_V 不够，310P 需全屏障"
description: "DataCopyPad 落到 UB 后，GetValue / 裸 __gm__ 读走标量管；只等 MTE2_V 时标量读仍与 DMA 竞速，可读到垃圾索引并触发越界访问或静默挂死。310P 实测跨管全屏障 PipeBarrier<PIPE_ALL>() 生效；950 历史记录为 HardEvent::MTE2_S（本批未复验）。"
tags: [task.debugging, topic.implementation.synchronization, topic.programming_model.execution_unit.vector, topic.implementation.masking, topic.data_movement.data_copy, topic.data_movement]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/bb96c9c595c7a8e96745d365291769dc48319c22/plugins-community/ascendc-port-orchestrator/kb/okf/runbooks/field-notes/build/ec-73-a-scalar-read-getvalue-raw-gm-deref-of-data-just-d.md
    role: primary
created_at: "2026-07-09T16:00:00Z"
updated_at: '2026-10-29T05:07:58Z'
platforms: ["310p", "950"]
aliases: ["EC-73", "GetValue", "__gm__", "DataCopyPad"]
---

# DataCopyPad 后标量读：MTE2_V 不够，310P 需全屏障

> 原 OKF v1 卡号：**EC-73**。
> 现象分类：runtime/silent_corruption；观测置信度：single_run（单次观测）。
> 触发信号：
> - no compile error. At runtime the kernel reads plausible-looking but WRONG scalar values (e.g. sampling/gather indices) right after a DataCopyPad-to-UB, computes

## 现象

采样/变形注意力类 kernel 里，`DataCopyPad` 把索引/元数据搬入 UB 后立刻用标量读消费：

```cpp
DataCopyPad(idxLocal, idxGm, copyParams, padParams);
SyncFunc<HardEvent::MTE2_V>();      // 只护栏向量管
int64_t k = idxLocal.GetValue(i);   // 标量读仍与 DMA 竞速
```

编译无错误；运行期读到“看似合理但错误”的标量（采样/聚集索引），据此算出越界 GM 偏移，越界读把设备静默挂死（无 fault、无 507035），易被误判为设备已卡死。

## 适用场景

- 工程形态：AscendC kernel 直调；`DataCopyPad` 把索引/元数据搬入 UB 后立刻用标量读消费。
- API 路径：`DataCopyPad` + `GetValue` / `SetValue` / 裸 `__gm__` 指针读；跨管序在 310P 用 `PipeBarrier<PIPE_ALL>()`，950 历史记录用 `HardEvent::MTE2_S`（替代不够的 `MTE2_V`）。
- 验证过的平台与 CANN 版本：Ascend310P3（dav-m200 / DAV_2002）+ CANN 9.1.0 独立复现；历史记录为 Ascend950PR + CANN 9.1.T500（本批 310P 迁移会话未复验 950）。
- 适用粒度：`platform_wide`——所有“DMA 落 UB 后标量读”的 kernel 阶段。
- 路线优先级：`recommended_fastpath`（标量消费前建立跨管序：310P 用 `PIPE_ALL`；950 历史路线为 `MTE2_S`）。
- 明确不适用 / 未验证场景：纯向量消费、无标量读的链路不受本卡约束；Ascend910_V220 未复测。

## 根因

`DataCopyPad`/`DataCopy` 的落地在 **MTE2** 管；`GetValue`/`SetValue`/裸 `__gm__` 指针读在**标量（S）管**。`HardEvent::MTE2_V` 只建立 MTE2 → 向量管的顺序，不覆盖标量管，因此标量读仍可与在途 DMA 竞速，读到旧值/垃圾值；据此算出的偏移可能越界，导致设备静默挂死。要让标量读看到已落地的数据，必须在两者之间建立 MTE2 → S 的跨管顺序：950 历史记录用 `HardEvent::MTE2_S`，310P 实测用 `PipeBarrier<PIPE_ALL>()`（`MTE2_S` 在 310P 是否足够未定，见失效边界）。

> 以下英文小节为**旧卡（仅 950 / Ascend950PR_957b + CANN 9.1.T500）历史记录**；310P 上 `MTE2_S` 是否足够未定，实测生效的是 `PipeBarrier<PIPE_ALL>()`（见文末 310P 补充）。旧文中的 "Only MTE2_S orders…" 是 950 条件下的结论，不适用于 310P。

`applies_to: soc=Ascend950PR_957b; cann=9.1.T500; bisheng=n/a; op_class=all`
`verified_on: soc=Ascend950PR_957b; cann=9.1.T500`
`unverified_on: soc=Ascend910_V220 (A2/A3 — the MTE2→S dependency is general AscendC pipe semantics, but not retested here)`

- **Error pattern**: no compile error. At runtime the kernel reads plausible-looking but WRONG scalar values (e.g. sampling/gather indices) right after a `DataCopyPad`-to-UB, computes an out-of-range GM offset from them, and the OOB read wedges the device (silent hang, no fault). Confounds easily with a wedged-NPU artifact (OL-189) — but the MTE2_S fix is independently required.
- **Root cause**: `DataCopyPad` moves data on the **MTE2** pipe. A subsequent `GetValue`/`SetValue`/raw pointer read runs on the **scalar (S)** pipe. Only `HardEvent::MTE2_S` orders the DMA-completion against the scalar read. Syncing `MTE2_V` (the common reflex for "DMA then VEC compute") guards VEC consumers but NOT the scalar pipe — the scalar read still races the in-flight DMA and observes stale/garbage UB.
- **Fix**:
  ```cpp
  // BEFORE (scalar read races the DMA — garbage index → OOB → hang):
  DataCopyPad(idxLocal, idxGm, copyParams, padParams);
  SyncFunc<HardEvent::MTE2_V>();           // ← guards VEC, NOT the scalar read below
  int64_t k = idxLocal.GetValue(i);        // races MTE2

  // AFTER (scalar read ordered after the DMA):
  DataCopyPad(idxLocal, idxGm, copyParams, padParams);
  event_t ev = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::MTE2_S));
  SetFlag<HardEvent::MTE2_S>(ev);
  WaitFlag<HardEvent::MTE2_S>(ev);
  int64_t k = idxLocal.GetValue(i);        // safe
  ```
- **Evidence**: 一个采样/变形注意力算子 port_a3_to_a5 kw-1 (2026-06-20, A5/Ascend950PR_957b/CANN 9.1.T500): scalar reads of `DataCopyPad`'d sampling indices under MTE2_V-only sync produced garbage indices → OOB GM access → hang; adding the `MTE2_S` Set/Wait fixed it.
- **Other instances (predicted)**: any kernel that DMA-loads index/offset/shape metadata to UB and then reads it scalar-side to drive addressing — gather/scatter, deformable/sampling ops, dynamic-shape tiling readers, variable-length list ops. General rule: a scalar consumer of `DataCopyPad`/`DataCopy`-to-UB data must sync `MTE2_S`, not `MTE2_V`.
- **Related**: EC-13 (`SyncFunc` API form + the `MTE2_S (GM→scalar)` event list), PB-43-class scalar-pipe sync (`SetFlag`/`WaitFlag` vs unsupported `PipeBarrier<PIPE_S>`), OL-189 (wedged-NPU can mask this — verify the fix on a fresh card).

## 310P/CANN 9.1.0 补充（独立复现：MTE2_V 不序标量管，需 PIPE_ALL）

在 Ascend310P3（dav-m200）+ CANN 9.1.0 上独立复现了"拷贝后立刻标量读"的同一类故障，并补出与旧卡结论的条件分支：

- **现象**：`DataCopy` 把一小块元数据搬到 UB 后立即 `GetValue` 取标量；拷贝终态经 D2H 导出核对逐位正确，但标量读到的是 0（有效行数 = 0），后续逐行存储整段被跳过，e2e 输出全零或上一轮残留。
- **`MTE2_V` 不够**：旧卡结论在 310P 上同样成立——`SetFlag/WaitFlag<HardEvent::MTE2_V>` 只建立 MTE2 → V 的序，**不约束标量管**。
- **310P 上实际生效的修法**：在拷贝与标量读之间加 `PipeBarrier<PIPE_ALL>()`（跨管全屏障），读值立即正确。
- **不要被旧注释挡住**：本轨迹早期在代码里留过"310P 禁加 `PIPE_ALL`，加了会异常终止"的注释；事后定位那次异常终止来自"零有效行时的行 -1 越界写"，与屏障无关。屏障只是让原本偶发的问题稳定暴露。

```cpp
// before：只有 MTE2_V，标量读可能先于拷贝落地
DataCopy(metaUb, gmMeta[base], DataCopyParams(8, 1, 0, 0));
SetFlag<HardEvent::MTE2_V>(evM2);
WaitFlag<HardEvent::MTE2_V>(evM2);
int32_t len = metaUb.GetValue(7);      // 可能读到 0 / 旧值

// after：跨管全屏障
DataCopy(metaUb, gmMeta[base], DataCopyParams(8, 1, 0, 0));
SetFlag<HardEvent::MTE2_V>(evM2);
WaitFlag<HardEvent::MTE2_V>(evM2);
PipeBarrier<PIPE_ALL>();
int32_t len = metaUb.GetValue(7);      // 已有序
```

## 验证信号

- 310P/CANN 9.1.0：加 `PIPE_ALL` 前，探针看到拷贝终态逐位正确，而业务按"有效行数 = 0"走、e2e 全零/残留；加后同一 unit 读到 `len = 64`、存储循环进入，输出不再全零（来源平台：310P；证据等级：tool_observed）。
- 同一份代码只把 `MTE2_V` 换成 `MTE2_S`（在"拷贝不落地"未修的前提下）症状不变——该实验被混淆，不能作为 `MTE2_S` 无效的证据（来源平台：310P；证据等级：tool_observed）。
- 该改动与"整块拷贝 + 大缓冲池"同批生效后，全量精度用例全部通过且重编后复验仍全部通过（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- **`MTE2_S` 在 310P 是否足够未定**：本次尝试与"拷贝不落地"故障混淆；要下结论必须重做干净 A/B（前提是拷贝已确认落地）。
- "标量读早"目前是行为级推断（终态正确 + 业务按 0 走），没有指令级取证（如反汇编确认标量读先于 MTE2 完成发射）。
- `PIPE_ALL` 每个 unit 排空一次流水线；unit 数很多时的成本未量化，本轨迹只在 unit 入口用一次。
- 只覆盖"拷贝 → 标量读"方向；"标量写 → 拷贝"需要另一类事件/屏障，未覆盖。
- 其它代际未验证；与"DataCopy 不落地"故障必须先用探针区分，否则会混成同一类。

## 坏实践

- 用 `MTE2_V` 事件对当"标量可见"的保证。
- 只 dump 终态做验证（终态永远是对的，必须留"读的那一刻"的值）。
- 看到旧注释写"某屏障导致异常终止"就照单全收，不核对那条结论出自哪个故障语境。

## 误诊

- 误诊：把"加 `PIPE_ALL` 后 kernel 异常终止"归罪于屏障（agent_reported）；实际是零有效行时的行 -1 越界写，屏障只是让问题稳定暴露。
- 误诊：换 `MTE2_S` 没修好，就判定"`MTE2_S` 在 310P 无效"（agent_reported）；当时首个拦路虎是拷贝不落地。
- 误诊：终态字段全对，就认为"数据没问题、是业务逻辑错"（agent_reported）；这是读序问题的典型错觉。

<!-- 迁移自 porter kb/target/ascendc/（EC-73，convert_family_to_okf.py，M1，整档忠实搬运）。confidence/severity/reproduce_count 未升格。 -->
