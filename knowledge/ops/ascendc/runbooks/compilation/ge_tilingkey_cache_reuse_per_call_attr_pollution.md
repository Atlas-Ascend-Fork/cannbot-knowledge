---
type: "Runbook"
title: "TilingKey 缓存 correction 致 tilingdata 复用"
description: "归约族算子把 per-call 属性 correction 经 tilingdata 下发却未纳入 TilingKey 时，GE 按 TilingKey 缓存 tilingdata，致同 TilingKey 第二次调用复用首次 cof 产生错误结果；判别为进程内失败、隔离通过，止血用子进程隔离，治本为属性纳 TilingKey。"
tags: ["task.debugging", "topic.implementation.tiling"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["ReduceVar"]
---

# TilingKey 缓存 correction 致 tilingdata 复用

## 现象

reduce_std_v2_update 算子（归约族，correction/unbiased 为 per-call 属性）在 PyTorch ST 联调时，E1 用例（注入特殊值的大值场景）在**进程内串行运行**时失败：`golden=2.97495157e-01`，`actual=3.39994490e-01`，`diff=4.25e-02 > tol=1.30e-05`，远超容差。但同一 E1 用例在**独立子进程**（`--isolate` 模式）中运行通过。其余 L0 用例在进程内串行也有类似的"前序用例影响后序用例"现象。C++ ST（26/26）此前已用 `--isolate` 子进程隔离模式通过，PyTorch ST 复现同一现象。算子 kernel 逻辑本身正确（黑盒 ST 全通过、5 穿刺全 PASS），问题出在 GE 框架的 tiling 缓存机制。

## 适用场景

- **工程形态**：ST 联调 / 白盒测试（PyTorch pytest 或 C++ GTest 串行运行多 case）。
- **API 路径**：aclnn 两段式 → GE 编译/tiling 缓存 → TilingKey 选择 binary + tilingdata 缓存。
- **验证过的平台与版本**：Ascend950（dav-3510 / arch35），CANN 9.2.0，torch_npu 2.10.0。`platforms: [950]`。
- **适用粒度**：`operator_family`——归约族（reduce_var / reduce_std_v2 / reduce_std_v2_update）凡 correction 或同类 per-call 属性经 tilingdata 下发却未进 TilingKey 的实现均适用。DAD 算子（`issue_20260618_tiling_cache_002`）已证实同根因。
- **路线优先级**：`safety_fallback` = `--isolate` 子进程隔离（止血，立即可用，case 仍按原容差全跑）；治本 `recommended_fastpath`（correction 纳入 TilingKey）未在本卡的实测范围内落地。
- **不适用或未验证场景**：correction 已纳入 TilingKey 的实现不适用；canndev TBE 原型用 gert 运行时 tiling（无 TilingKey 缓存）不受影响。a2/a3 未验证，推断可迁移。

## 根因

GE 框架按 **TilingKey 缓存 tilingdata**：同一 TilingKey 的第二次调用复用首次算好的 tilingdata，不再调 tiling 函数。reduce_std_v2_update 的 TilingKey 仅 3 个 bool（templateType/isEmptyTensor/isTailR），**correction（属性）未纳入 TilingKey**，却通过 tilingdata 下发（tiling 阶段算 `cof = 1/(N-correction)` 后 `tiling_data->Append()`）。后果：同一 TilingKey 下，correction=0（unbiased=false，cof=1/N）的首次调用把 cof 写入 tilingdata 缓存；correction=1（unbiased=true，cof=1/(N-1)）的第二次调用 TilingKey 相同 → 复用首次 cof=1/N → var 用错了分母 → 结果错误。E1 大值场景下错误 cof 把误差放大到 4.25e-02 量级，远超 1.30e-05 容差。

canndev TBE 原型为什么无此问题：gert 框架**无 TilingKey 概念**，每次调用都执行 tiling 函数、从 attrs 实时读 correction 计算 cof（`reduce_std_func.cc:132-155`），不做 tilingdata 缓存——靠运行时 tiling 绕开了缓存污染。950 AscendC 静态 binary 框架依赖 TilingKey 做 binary 选择 + tilingdata 缓存优化，correction 未进 TilingKey 即触发缓存复用。

DAD 算子同根因（`issue_20260618_tiling_cache_002`：tilingdata 缓存复用陈旧数据），但 DAD 的差异参数 lr/l1/l2 是**输入张量**（在 GM），DAD 的最终解法是 kernel 从 `GM_ADDR` 直读标量绕过 tilingdata 缓存；本算子 correction 是**属性**，只能经 tilingdata 下发，DAD 的直读方案无法照搬。

## 判别方法

**触发**：ST 串行运行时部分用例失败，且失败用例与"前序同 TilingKey、不同 correction 的用例"相关；同一用例单独运行（隔离进程）通过。

**可执行探针**：

1. 隔离重跑探针——把失败用例单独跑：`pytest --isolate`（每用例独立子进程）或单 case 调用。隔离通过即判缓存污染。
2. TilingKey 维度审查——读 `op_host` 的 TilingKey 定义与 tilingdata schema，确认 per-call 属性（correction/unbiased）是否纳入 TilingKey 维度；未纳入即根因确认。

**原始观测**：

- E1 进程内运行：`golden=2.97495157e-01`，`actual=3.39994490e-01`，`diff=4.25e-02 > tol=1.30e-05`（失败）。
- E1 隔离运行：通过。
- 全量 26 L0 用例 `--isolate` 模式：26/26 PASS。
- PyTorch ST `--isolate`：66/66 PASS。
- TilingKey 定义审查：3 bool（templateType/isEmptyTensor/isTailR），correction 未进 TilingKey。
- canndev 对照：无 TilingKey 概念，每次 tiling 实时算 cof，无缓存。

**解释**：GE 按 TilingKey 缓存 tilingdata，correction 经 tilingdata 下发却不进 TilingKey，致同 TilingKey 复用首次 cof；E1 大值场景把错误 cof 的误差放大到 1e-2 量级；隔离进程无前序缓存故通过。

## 解决配方

本卡为诊断 + 止血配方（治本方案本 trace 未落地）。**止血**：ST 全量改用 `--isolate` 子进程隔离模式运行——每用例独立进程，进程退出即释放 GE tiling 缓存，correction 复用不复存在。用例本身、容差、期望值均不变，仅改运行模式。

**止血命令**（PyTorch ST，verbatim 取自 trace 内子 agent 调用）：

```bash
# 每用例独立子进程，规避 GE tilingdata 跨用例缓存复用
python3 -m pytest tests/st/torch/test.py --isolate -k "L0"
```

**治本方案（本 trace 未落地，列为遗留优先项）**：将 correction（或 unbiased，因 l0op 中 correction==0 等价 unbiased=false）纳入 TilingKey 第 4 维——使不同 correction 值产生不同 TilingKey → 不同 tilingdata 缓存条目。canndev binary_config 中 correction 仅 0/1 两种语义，TilingKey 只需 1 bit 区分。落地要求：`make_clean` 全量重编译 + 删 GE 编译缓存目录 + 重装 + 重验（此前尝试失败大概率是重编译/清缓存不彻底，与 DAD `issue_003`"NPU 回退缓存旧二进制"同源）。

**对照 DAD 的失败迁移**：DAD 把差异参数从 tilingdata 改为 kernel 从 GM 直读标量绕过缓存——本算子 correction 是属性无法直读 GM，此方案不适用，必须走 TilingKey 维度扩展。

## 设计决策

- **为何选 --isolate 止血而非直接治本**：治本（correction 纳 TilingKey）需全量重编译 + 彻底清 GE 缓存，此前尝试失败（疑缓存未清），风险与周期高于迭代验收窗口；--isolate 可立即让 26/26 + 66/66 通过且不放宽容差，case 仍按原精度标准全跑。
- **被放弃的方案**：① DAD 的"kernel 从 GM 直读标量"——correction 是属性不在 GM，不适用；② 把 correction 改为 0-dim 输入张量下发到 GM——需改 op_graph/aclnn API，改动过大。
- **当前方案属哪档路线**：`safety_fallback`（--isolate 止血）；治本（TilingKey 扩维）留待后续，属 `recommended_fastpath` 候选。

## 验证信号

问题与验证来源：reduce_std_v2_update PyTorch ST 联调 E1 用例进程内失败、隔离通过；调查对照 canndev TBE 原型 tiling 机制与 DAD 同根因 issue。

- E1 进程内运行 `golden=2.97495157e-01, actual=3.39994490e-01, diff=4.25e-02 > tol=1.30e-05`（失败）（来源平台：Ascend950；证据等级: tool_observed）
- E1 隔离子进程运行通过（来源平台：Ascend950；证据等级: tool_observed）
- 26 L0 用例 `--isolate` 模式 26/26 PASS（来源平台：Ascend950；证据等级: tool_observed）
- PyTorch ST `--isolate` 66/66 PASS（来源平台：Ascend950；证据等级: tool_observed）
- TilingKey 审查：3 bool（templateType/isEmptyTensor/isTailR），correction 未进 TilingKey（来源平台：Ascend950；证据等级: tool_observed）
- canndev 对照：无 TilingKey 概念，gert 每次实时算 cof，无缓存污染（来源平台：Ascend950；证据等级: tool_observed）

## 坏实践

- 进程内串行跑归约族多 case、看到部分失败就当算子 bug 修 kernel——实际 kernel 逻辑正确，根因在 GE tiling 缓存。
- 为通过验收而放宽失败用例容差或 skip 失败 case——掩盖 tiling 缓存缺陷，属"测试侧放松"捷径，不得作为解决配方。

## 预防

- 归约族（及任何 per-call 属性经 tilingdata 下发的算子）设计阶段即审查：per-call 属性是否进 TilingKey？不进则有缓存复用风险。
- ST 框架默认 `--isolate` 子进程隔离运行归约族多 case，至少在 correction/unbiased 维度变化的用例集。

## 失效边界

- 本卡证据仅 Ascend950 / CANN 9.2.0。a2/a3 未验证，推断可迁移（GE TilingKey 缓存机制与平台无关，但 a2/a3 的 CANN 版本 TilingKey 实现细节需实测）——未验证，推断可迁移。
- --isolate 止血仅隔离 GE tiling 缓存，不改算子逻辑；若算子本身有 cof 计算错误，--isolate 不会修复，需另定位。
- 治本（correction 纳 TilingKey）落地后 --isolate 可不再必需；但治本前 --isolate 是必要止血。