---
type: "Runbook"
title: "反量化 561103 实为 CheckBroadcastShape 过严"
description: "Ascend950 反量化算子 DequantizeCustom 多 dtype 变体 ST 上板返回 561103（ACLNN_ERR_INNER_NULLPTR），先误诊为 tiling key 共享 g_tilingDeclareParams，真因为 tiling 函数内 CheckBroadcastShape 把合法的反量化外积式广播判为不兼容。给出基于 plog/grep/源码读的判别方法。"
tags: ["task.debugging", "topic.tiling", "topic.compute.quantization"]
status: stable
sources: []
created_at: "2026-08-18T15:21:14Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# 反量化 561103 实为 CheckBroadcastShape 过严

## 适用场景

- **工程形态**：ops-registry-invoke 算子仓开发，多 dtype 变体共享同一份 tiling 实现，用 `ASCENDC_TPL_*` 宏模板（`TilingKey` 编码 dtype + rank）分发变体。
- **API 路径**：`ASCENDC_TPL_ARGS_DECL` / `GET_TPL_TILING_KEY`（tiling key 编码）→ `ctx_->SetTilingKey(...)` → host tiling 内 `CheckBroadcastShape` → `SelectBin` 选 kernel。
- **验证过的平台与 CANN 版本**：Ascend950（`--soc=ascend950`），CANN 9.1.0。仅 950 有实测证据。
- **适用粒度**：`operator_family`——任何“多输入广播算子的 tiling 函数里手写广播合法性校验”的场景。
- **路线优先级**：`recommended_fastpath`——广播校验只验证“各输入能广播到输出 shape”，不要要求各输入之间两两互兼容。
- **不适用或未验证场景**：a2/a3 未验证（推断可迁移，见 `## 失效边界`）；单输入算子不触发。

## 判别方法

**触发**（tool_observed）：在 dtype 注册问题（表现为 `SelectBin ... inconsistent with OpDef`）已确认排除后，ST/联调上板仍返回 `errno[561103] DequantizeAiCore failed`（plog 标注 `ACLNN_ERR_INNER_NULLPTR`）。该 561103 来自 tiling 函数返回失败、kernel 拿不到 workspace。

**探针**（executable check，按序执行）：

1. 确认 dtype 注册无误——plog 中**不应**再出现 `SelectBin ... inconsistent with OpDef`（若仍有则是另一类注册问题，不在本卡范围）。
2. `grep -n 'dequantize_struct_' operators/<op>/op_host/arch35/dequantize_tiling_arch35.cpp`——核对 tiling 实现里 `#include` 了几个变体 struct 头。本 trace 确认只 include 了一个变体头（`dequantize_struct_i8_fp16.h`），是 tiling key 误诊的入口线索，但不是 561103 真因。
3. 在 tiling 函数入口加日志或读 plog，确认 `CheckBroadcastShape` 是否打印 `dim %d broadcast incompatible: input[%d] size %d != %d` 并返回 false。若打印并返回 false 即命中本卡。
4. 构造一个反量化外积式广播用例（如 `x=[3,1]`、`scale=[1,4]`、`zero_point=[3,1]`、`output=[3,4]`），单独喂给 `CheckBroadcastShape`，观测其是否对该合法广播返回 false。

**观测**（tool_observed / artifact_verified）：源码读事件逐字恢复 `dequantize_tiling_arch35.cpp` 第 8 行只 include `dequantize_struct_i8_fp16.h` 单一变体头；第 359/362 行用 `ctx_->SetTilingKey(GET_TPL_TILING_KEY(input_dtype_c_, scale_dtype_c_, DEQUANTIZE_RANK_4/8))` 编码 key；`CheckBroadcastShape` 函数体（第 22–50 行逐字）如下：

```cpp
bool CheckBroadcastShape(
    const std::vector<std::vector<int64_t>>& padded_in,
    const std::vector<std::vector<int64_t>>& padded_out,
    int64_t max_rank)
{
    for (int64_t d = 0; d < max_rank; d++) {
        int64_t ref = -1;
        for (size_t i = 0; i < padded_in.size(); i++) {
            if (padded_in[i][d] != 1) {
                if (ref == -1) ref = padded_in[i][d];
                else if (padded_in[i][d] != ref) {
                    OP_LOGE("CheckBroadcastShape",
                        "dim %d broadcast incompatible: input[%d] size %d != %d",
                        (int)d, (int)i, (int)padded_in[i][d], (int)ref);
                    return false;
                }
            }
        }
        for (size_t i = 0; i < padded_out.size(); i++) {
            if (padded_out[i][d] != 1) {
                if (ref == -1) ref = padded_out[i][d];
                else if (padded_out[i][d] != ref) {
                    OP_LOGE("CheckBroadcastShape",
                        "dim %d broadcast incompatible: output[%d] size %d != %d",
                        (int)d, (int)i, (int)padded_out[i][d], (int)ref);
                    return false;
                }
            }
        }
    }
    return true;
}
```

**解释**（interpretation，agent 根因分析，非 API 规范主张）：该校验对每个维度要求所有输入的非 1 维度两两一致（同一 `ref`）。但反量化算子的 `scale` 合法地拥有与 `x`/`zero_point` 不同的独立广播模式：例如 `x=[3,1]`、`scale=[1,4]`、`zero_point=[3,1]`、`output=[3,4]` 是合法广播（各输入都能广播到 `[3,4]`），但 `CheckBroadcastShape` 在某些 axis 上会把 `scale` 的非 1 维度与 `x` 的非 1 维度判为互斥而拒绝、返回 false，导致 tiling 失败、kernel 拿不到 workspace，上报 `561103`。正确做法是只校验“每个输入和输出都能广播到 `max_bro_shape`”，不要求各输入之间两两互兼容。该因果链由“触发 561103 → 探针定位到 `CheckBroadcastShape` 返回 false → 观测到过严校验体”的 tool_observed 闭环交叉验证；放宽后的 post-fix 通过数为 agent 叙述，未作为验证信号。

## 验证信号

来源：本 trace 在 Ascend950 / CANN 9.1.0 上对 `operators/dequantize` 算子包做 ST 联调；失败信号在 normalized trace 中以非 redacted tool_result 形式保留。

- 修复前：ST 联调 plog 返回 `errno[561103] DequantizeAiCore failed`（标注 `ACLNN_ERR_INNER_NULLPTR`），在 dtype 注册问题排除后仍持续出现。（来源平台：950；证据等级：tool_observed）
- 修复前：拆分变体编译单元时 `make: *** [...] dequantize_tiling_i8_bf16.o Error 1`（及 `i8_fp32`/`i32_fp16` 等变体目标），`Traceback: RuntimeError: compile ascend all ops failed`。（来源平台：950；证据等级：tool_observed）
- 源码读：`dequantize_tiling_arch35.cpp` 仅 include `dequantize_struct_i8_fp16.h` 单一变体头；`CheckBroadcastShape` 函数体逐字如 `## 判别方法` 所示，对非 1 维度做两两互兼容强校验、不满足即 `OP_LOGE(...); return false`。（来源平台：950；证据等级：artifact_verified）

## 误诊

- **误诊 1**：把 `561103` 全部归因为 tiling key 编码（共享 `g_tilingDeclareParams`）。`ASCENDC_TPL_ARGS_DECL` 宏在每个编译单元的文件作用域生成 `static TilingDeclareParams g_tilingDeclareParams`，`GET_TPL_TILING_KEY(...)` 用它编码 key；tiling 实现只 `#include "dequantize_struct_i8_fp16.h"` 一个变体头，6 个变体即使 `input_dtype_c_`/`scale_dtype_c_` 不同，编码出的 tiling key 也都套用了 i8_fp16 的 params。agent 据此把 tiling 拆成 common header + 6 个变体 `.cpp`（每个变体 TU 各自 include 自己的 struct 头、各自生成独立的 `g_tilingDeclareParams`）。该拆分在编译期引入了两个新坑（均有 verbatim 证据）：narrowing conversion（`GET_TPL_TILING_KEY` 把 `int32_t` 传给期望 `uint64_t` 的形参，warnings-as-errors 下编译失败）；以及 ODR/linker（公共头 `dequantize_tiling_common.h` 里的命名空间级辅助函数被多个变体 TU include 后多重定义，需在每个签名前加 `inline` 修复）。但 tiling key 拆分修复后 ST 通过数没有变化，证明 tiling key 并非 `561103` 的真因——真因是 `CheckBroadcastShape` 过严。
- **误诊 2**：把变体 `.o` 编译失败先当作单纯 narrowing，实际 narrowing、`graph/c_types.h` include 顺序、ODR 三类问题在拆分后接连出现，需逐项处理（narrowing 加 `static_cast<uint64_t>`、c_types.h 先于 struct 头 include、辅助函数加 `inline`）。

## 失效边界

- **未验证，推断可迁移**：a2/a3 平台未在本 trace 内实测，`ASCENDC_TPL_*` 宏与 opbuild 行为属工具链层面，推断可迁移（未验证）。
- **不适用**：若算子只有一个 dtype 变体、或各输入广播模式天然互兼容（如纯 elementwise），则 `CheckBroadcastShape` 过严问题不显现。

<!-- cannbot:related:start -->
## 相关

- [softplus_v2_grad tiling rank 校验拒标量广播](softplus_v2_grad_tiling_rank.md)（`related`）：“正确做法是只校验“每个输入和输出都能广播到 `max_bro_shape`”，不要求各输入之间两两互兼容。”明确给出左端事实；“- **判读（interpretation，根因分析）**：raw rank 一致性校验是**冗余且自相矛盾**的插入。”明确给出右端事实。两页分别定位广播 tiling 的逐维兼容校验过严和 raw-rank 前置校验过严；排障时应先补 1 对齐，再校验每个输入能否广播到输出，而不是拒绝合法异 rank/外积广播。
- [标量输入被赋非标量 shape 致 561002 判别](shape_561002.md)（`related`）：“但反量化算子的 `scale` 合法地拥有与 `x`/`zero_point` 不同的独立广播模式：例如 `x=［3,1］`、`scale=［1,4］`、`zero_point=［3,1］`、`output=［3,4］` 是合法广播（各输入都能广播到 `［3,4］`），但 `CheckBroadcastShape` 在某些 axis 上会把 `scale` 的非 1 维度与 `x` 的非 1 维度判为互斥而拒绝、返回 false，导致 tiling 失败、kernel 拿不到 workspace，上报 `561103`。”明确给出左端事实；“根因排查发现：spec.yaml 明确规定 `w_square_sum` / `g_square_sum` / `weight_decay` / `learning_rate` 的 `role: scalar`（synthesize shape 为 `［］`/`()`/`(1,)`），但黑盒用例 gen_data 把这些标量输入赋了非标量大形状（如一维大 shape），违反 spec role:scalar，导致 host `TilingFunc`（`PadAndSqueeze`/`CheckBroadcastShape`）无法处理 → tiling 失败 → 561002 → NO_OUTPUT。”明确给出右端事实。一页说明 CheckBroadcastShape 实现拒绝合法外积广播，另一页说明测试把 scalar 角色输入造为大张量而使同类 PadAndSqueeze/CheckBroadcastShape 失败，二者提供实现缺陷与输入违约的鉴别路径。
<!-- cannbot:related:end -->
