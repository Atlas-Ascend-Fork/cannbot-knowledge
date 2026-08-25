---
type: "Runbook"
title: "标量属性入 TilingData 致同 shape 跨调用陈旧"
description: "registry-invoke 自定义算子把 per-call 标量属性（beta/threshold）写入 TilingData，框架按 (算子, shape, dtype) 缓存 TilingData 不含属性值，导致同 shape/dtype 不同属性的后续调用复用陈旧属性、产出错误数值。判别=隔离单跑正确 + 同进程顺序跑取陈旧属性数值。"
tags: ["task.debugging", "topic.implementation.tiling", "topic.implementation.operator_registration", "topic.precision"]
status: stable
sources: []
created_at: "2026-08-18T15:34:26Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["tiling_cache"]
---

# 标量属性入 TilingData 致同 shape 跨调用陈旧

## 现象

在一次 `softplus_v2_grad` 算子精度调试会话中（ops-registry-invoke 流程），构建已通过并以 `--soc=ascend950` 安装到 vendors 路径（CANN `cann-9.0.0-beta.2`）。Phase 0 完成代码生效三段确认：重建后对 `build/op_kernel/ascendc_kernels/binary/ascend950/softplus_v2_grad_apt/SoftplusV2Grad_*.o` 跑 `sha256sum`，`./build/custom_opp_ubuntu_x86_64.run --quiet` 安装，再对安装路径下同名 `.o` 跑 `sha256sum` 比对一致，并 `ldd ./test_aclnn_softplus_v2_grad` 确认实际加载 vendors 软链路径。

随后跑精度用例：C++ ST（57 例）与 PyTorch 接入 L0（51 例）全部通过；但 PyTorch 接入 L1（CSV 驱动 527 例）出现 `总计: 527 / 通过: 421 / 失败: 106 / 跳过: 0`。失败用例的 `beta`/`threshold` 多为极端值——`±3.403e38`（±FLT_MAX）、`±1.175e-38`（最小正常数）、数百~数千量级、或 `0`/接近 `0`。失败信号形形色色：标量 1/1 mismatch（如 `[37/527] [FAIL] aclnnSoftplusV2Grad_L1_037 MERE=5.380860e+06 ... mismatch=1/1`）、整片全错（`[98/527] [FAIL] aclnnSoftplusV2Grad_L1_098 MERE=inf ... mismatch=1856000/1856000`）、以及部分 mismatch 配大 MERE。重跑一次得 102 例失败、与首次 106 例有 4 例差异，说明失败集主要由参数（beta/threshold/shape）触发，对具体随机数据仅弱相关。

算子公式（kernel 头注释，verbatim 取自 `op_kernel/arch35/softplus_v2_grad_kernel.h` file_read 事件）：

```
bx = beta * self
mask = (bx > threshold)
bx_clamped = min(max(bx, -50), threshold)   // exp 输入双 clamp 防 exp 溢出
sigmoid = exp(bx_clamped) / (1 + exp(bx_clamped))
grad_sig = grad_output * sigmoid
grad_input = where(mask, grad_output, grad_sig)
```

golden（`tests/st/torch/golden.py`，verbatim）：

```
z = beta * self
gradInput = np.where(z > threshold, gradOutput, gradOutput / (1.0 + exp(-z)))
           = gradOutput * sigmoid(z)   当 z <= threshold
           = gradOutput                当 z >  threshold
```

`beta` 与 `threshold` 作为 `OP_ATTR(beta, threshold)` 进入 L0 launcher，tiling 函数以 `attrs->GetFloat(0/1)` 读出后写入 `TilingData.beta_scalar`/`threshold_scalar`，kernel 从 `td_->beta_scalar`/`td_->threshold_scalar` 取值。

## 适用场景

- **工程形态**：ops-registry-invoke（算子仓开发）流程产出的自定义 aclnn 算子；PyTorch 接入（libtorch_adapter.so + `torch.ops.<op>.forward`）两段式 L1 跑批。
- **API 路径**：`aclnn<Op>` L0 launcher 宏 `ADD_TO_LAUNCHER_LIST_AICORE(..., OP_ATTR(beta, threshold), ...)` → host 侧 tiling 函数 `attrs->GetFloat(...)` → `TilingData` 标量字段 → kernel `td_->` 读取。
- **验证过的平台与 CANN 版本**：Ascend950（`--soc=ascend950`，kernel binary 路径 `ascend950/softplus_v2_grad_apt`），CANN `cann-9.0.0-beta.2`。与 frontmatter `platforms: [950]` 严格一致。
- **适用粒度**：`operator_family`——适用于任何 registry-invoke 自定义算子，只要把 per-call 标量属性存进 `TilingData` 且同 (shape, dtype) 会在同一进程内以不同属性值被多次调用。
- **路线优先级**：`recommended_fastpath`——诊断"同 shape 跨调用属性失真"类精度失败时，首选隔离-vs-顺序复现探针（见 `## 判别方法`），再决定是否走"属性移出 TilingData"修复。
- **不适用或未验证场景**：单次调用进程（每次 `python3` 只调一次算子）不受影响；同 shape/dtype 且属性值相同的跨调用不受影响；非 registry-invoke 模型（如直接 Kernel 直调 ops-direct-invoke）的 tiling 通道未在本 trace 验证；A2/A3 平台未验证，推断可迁移但见 `## 失效边界`。

## 判别方法

**触发（trigger，tool_observed）**：自定义算子把 per-call 标量属性（`beta`/`threshold` 或同类 α/scale/axis-scalar）写入 `TilingData`，且同一进程内连续调用共享相同 (输入 shape, dtype) 但属性值不同的用例。L1 CSV 跑批天然满足：527 例中大量标量/同 shape 用例，属性值各异。触发表现为批跑出现 mismatch，失败用例属性多为极端值。

**探针（probe）**——隔离 vs 顺序对比：

1. 选一个失败用例的 (beta, threshold, shape, dtype)，在**独立 python 进程**中单跑一次（fresh process，只 `load_library` + 一次 `forward`），打印 `golden` 与 `actual`。
2. 在**同一 python 进程**内，先跑另一组同 (shape, dtype) 但不同 (beta, threshold) 的用例，再跑步骤 1 的那组参数，打印 `golden` 与 `actual`。
3. 对比：若隔离正确、顺序错误，且顺序错误的 `actual` 恰好等于"用序列早期某次属性代入本组 shape/self 计算的结果"，则判定为 TilingData 跨调用陈旧。

**观测（observation，tool_observed，verbatim 取自 raw 转写记录）**：

顺序跑（同一进程，7 组 shape=[1] fp32、属性各异的 `t()` 调用，`2>&1 | tail -20` 截尾）最后一行：

```
  beta=1.0 thr=-1e+38 self=0.5 grad=1.0: golden=1.0 actual=0.6224592924118042 MISMATCH
```

隔离跑（`for params in "200.0 100.0 1.0 1.0" "1.0 -1e38 1.0 0.5"; do python3 -c "..."; done`，每组独立进程）：

```
ISOLATED beta=200.0 thr=100.0 self=1.0 grad=1.0: golden=1.0 actual=1.0
ISOLATED beta=1.0 thr=-1e+38 self=1.0 grad=0.5: golden=0.5 actual=0.5
```

机制判读：顺序用例 `beta=1, thr=-1e38, self=0.5, grad=1.0` 的 `z=0.5 > -1e38` 应走线性分支 `grad_input=grad=1.0`（即 golden=1.0）；但 `actual=0.6224592924118042 = sigmoid(0.5)`，正是"把 threshold 当成 100（序列早期某次值）、0.5 < 100 走 sigmoid 分支"的结果。隔离单跑同参数 `actual=0.5=grad`（线性分支正确）。两者唯一差异是"同进程内是否先跑过同 shape/dtype 的其他属性用例"。

**解释（interpretation，属 agent 根因分析，非源码层独立验证）**：CANN 框架对 registry-invoke 自定义算子的 tiling 结果按 (算子, 输入 shape, dtype) 缓存，缓存键不含 `OP_ATTR` 中的标量属性值。`beta_scalar`/`threshold_scalar` 被写进 `TilingData` 后随 tiling 结果一起被缓存；当第二次调用 shape/dtype 相同但属性不同时，框架命中缓存、不重跑 tiling 函数，kernel 读到的是首次的陈旧 `beta_scalar`/`threshold_scalar`。tiling 函数本身在隔离单跑时被正常调用（故隔离正确），在顺序同 shape 调用时被缓存跳过（故顺序错误）。

> 注：框架缓存键的确切组成未在 CANN 源码层直接验证——`op_api` 代码无显式缓存，对 `include/graph/` 与 `tiling_context.h` grep `AtomicCache/TilingCache/DisableCache/SetCacheKey` 未命中可用 API，属行为层推断。

## 根因

`beta_scalar` 与 `threshold_scalar` 作为 per-call 标量属性被存入 `TilingData`，而 `TilingData` 是 CANN 框架按 (算子, 输入 shape, dtype) 缓存的单元（缓存键不含 `OP_ATTR` 标量值）。同 shape/dtype 不同属性的后续调用复用陈旧 `TilingData`，kernel 读到陈旧 `beta`/`threshold`，分支判定与数值均偏离 golden。

补充：`bx_clamped = min(max(bx, -50), threshold)` 的上界 clamp 到 `threshold` 在 `threshold` 为大正值（>~88）时无法防 `exp` 上溢——但本 trace 证实这并非失败主因：`exp` 上溢时 golden 与 kernel 同为 NaN/Inf 会匹配；真正的 mismatch 来自陈旧属性导致的分支错选（线性 vs sigmoid 选错）。

## 预防

- 不要把 per-call 标量属性（`beta`/`threshold`/`alpha`/`scale`/`axis-scalar` 等）存进 `TilingData`。`TilingData` 只应放"由 shape/dtype 决定、可安全缓存"的切分/布局量；任何在同一 (shape, dtype) 下可能取不同值的属性都必须走 per-call 通道。
- 候选 per-call 通道（本 trace 未实现、未验证，仅作方向）：把标量属性写入 per-call workspace（device 内存，每次调用重新分配），kernel 从 workspace GM 读取；或在 L0 launcher 侧把属性作为 kernel launch 参数透传（若框架支持）；或在 `ReleaseTo` 前调 `AbandonCache` 类接口禁用 repeat/tiling cache 强制 tiling 函数每次执行。
- 测试工程侧：L1 CSV 跑批若用例间共享 (shape, dtype) 且属性各异，恰好是这类 bug 的天然探针——C++ ST 用唯一 shape 规避了它（故 57/57 通过），不能因此认为算子正确。

## 验证信号

- PyTorch 接入 L1 跑批：527 例通过 421、失败 106（首次）/102（重跑），失败用例属性多为极端值（±FLT_MAX、最小正常数、数百~数千、0）（来源平台:950；证据等级:tool_observed）
- 顺序复现：同进程内连续 7 组 shape=[1] fp32 属性各异的 `t()` 调用，最后一组 `beta=1.0 thr=-1e+38 self=0.5 grad=1.0` 输出 `golden=1.0 actual=0.6224592924118042 MISMATCH`（actual=sigmoid(0.5)，套用了序列早期 thr=100）（来源平台:950；证据等级:tool_observed）
- 隔离复现：同两组参数各起独立进程单跑，输出 `ISOLATED beta=200.0 thr=100.0 self=1.0 grad=1.0: golden=1.0 actual=1.0` 与 `ISOLATED beta=1.0 thr=-1e+38 self=1.0 grad=0.5: golden=0.5 actual=0.5`（线性分支正确）（来源平台:950；证据等级:tool_observed）
- kernel 公式与 golden 公式 verbatim 取自 file_read 事件（`op_kernel/arch35/softplus_v2_grad_kernel.h`、`tests/st/torch/golden.py`），属性经 `TilingData.beta_scalar`/`threshold_scalar` 入 kernel（来源平台:950；证据等级:artifact_verified）

## 失效边界

- 本结论在 Ascend950 + CANN `cann-9.0.0-beta.2`、registry-invoke 流程下行为层证实。A2/A3 平台与其它 CANN 版本未验证，推断可迁移（registry-invoke 的 tiling 缓存机制是框架级、跨平台一致的可能性高，但未实测）。
- 框架 tiling 缓存键是否真的不含 `OP_ATTR`、以及是否存在 `SetCacheKey`/`DisableCache`/`AbandonCache` 类 API 可把属性纳入键或禁用缓存，未在源码层定位。若某版本框架已把属性纳入缓存键，本卡描述的失真即不成立。
- 单次调用进程、或同 (shape, dtype) 同属性的跨调用不触发本失真。
- 本卡只覆盖"标量属性入 TilingData 被缓存陈旧"这一根因；同 trace 中观察到的 spec.yaml `rank(gradOutput)==rank(self)` 约束与 numpy 广播允许不同 rank 的矛盾、以及陈旧 `npu_run_log.txt` 记录的 423 个 561103 ERROR，均未在本 workspace 复现/定位，不在本卡覆盖范围。

## 坏实践

- 用 C++ ST（唯一 shape 用例）通过即声称算子正确——C++ ST 的用例 shape 互不重复，恰好绕开了 tiling 缓存冲突，掩盖了 L1 才会暴露的同 shape 跨调用陈旧。把 ST 全过当作精度门禁会漏掉这类 bug。
- 为了让失败用例"通过"而放宽容差/删除失败用例/缩小 shape——本 trace 的失败用例 mismatch 量级（MERE=5.38e6、inf）远超任何合理容差，绕过即掩盖真因；正确做法是定位根因（属性陈旧）并改 tiling 通道。

## 误诊

- 一度怀疑 `bx_clamped = min(max(bx, -50), threshold)` 上界 clamp 到 `threshold` 在大正值 `threshold` 时致 `exp` 上溢产生 NaN（agent 推理）。逐例核对后：`exp` 上溢时 golden（`torch.ops.aten.softplus_backward`）与 kernel 同为 NaN/Inf 会匹配，不构成 mismatch；真正的 mismatch 来自陈旧属性导致的分支错选。该假设被行为数据否决。
- 一度怀疑 NDDMA 广播搬运在 `[3,1] vs [1,4]`（双输入均需广播）时 offset/stride 计算错误（agent 推理，源于陈旧 `npu_run_log.txt`）。在本 workspace 重建后跑 C++ ST，该用例通过；陈旧日志来自另一 workspace 路径，不可作为本算子的失败证据。
- 一度怀疑 `beta/threshold` 在 tiling 函数中读取错误或 `TilingData` 布局错位（agent 推理）。被隔离单跑正确（属性正常传入）否决——属性读取与布局无误，问题在跨调用缓存复用。

<!-- cannbot:related:start -->
## 相关

- [Host 缺 SetDataSize 致 TilingData 截断](host_setdatasize_tilingdata.md)（`related`）：即使 shape/key 正确，Host 若未 SetDataSize 仍会使 Kernel 读取不完整结构；这是序列化而非缓存根因。
- [softplus_v2_grad tiling rank 校验拒标量广播](../compilation/softplus_v2_grad_tiling_rank.md)（`related`）：Softplus rank 卡说明 raw rank/shape 写入 TilingData 的时机，能核对 shape 字段本身是否在缓存前就错误。
- [反量化 561103 实为 CheckBroadcastShape 过严](../compilation/561103_checkbroadcastshape.md)（`related`）：广播 shape 校验在 Host tiling 入口提供前置错误信号，可区分非法 shape 与合法 shape 下复用旧 TilingData。
- [ACLNN L2 缓存键漏 scalar 致批跑误命中](../compilation/aclnn_l2_cache_key_missing_scalar_partial_mismatch.md)（`same_topic`）：该卡给出独立进程正确、同进程顺序调用错误且 actual 对应旧 threshold 的隔离探针，直接复现 L2 cache key 漏 scalar 的部分匹配。
- [TilingKey 缓存 correction 致 tilingdata 复用](../compilation/ge_tilingkey_cache_reuse_per_call_attr_pollution.md)（`same_topic`）：TilingKey 缓存 correction 致 tilingdata 复用 与《标量属性入 TilingData 致同 shape 跨调用陈旧》的实质衔接是：该问题由 GE 按 TilingKey 缓存 correction 造成同 shape 调用复用旧 TilingData；属性传递指南和注册/判定宏共同说明如何让变化属性进入正确 tiling 分派。
- [aclnn TilingData 缓存致 runtime attr 陈旧](aclnn_tilingdata_runtime_attr.md)（`same_topic`）：两卡都以同 shape 不同 runtime scalar 连跑复现 TilingData 陈旧；一张是 softplus ACLNN 实例，一张提炼 shape-only 缓存根因。
- [算子属性默认值 stringstream 截断致 FP32 标量误差](stringstream_fp32.md)（`same_topic`）：算子属性默认值 stringstream 截断致 FP32 标量误差 与《标量属性入 TilingData 致同 shape 跨调用陈旧》的实质衔接是：OpDef Attr是默认 float 字面量进入 op_build 序列化的起点，GET_TILING_DATA_WITH_STRUCT是 device 读取终点；TilingData缓存与 numpy标量提升是相同稳定ULP现象的关键差分根因。
<!-- cannbot:related:end -->
