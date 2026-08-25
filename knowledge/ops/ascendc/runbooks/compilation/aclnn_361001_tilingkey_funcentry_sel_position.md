---
type: "Runbook"
title: "ACLNN 361001 — tilingKey 与 funcEntry 映射失"
description: "Host SetTilingKey(N) 后运行时按 funcEntry=tilingKey 查找内核入口，若 kernel 二进制未通过 ASCENDC_TPL_SEL 在对应 SEL 位置注册该 funcEntry，则 BinaryGetFunctionByEntry 失败并报 361001。给出 funcEntry=SEL 位置=tilingKey 的判别与 SEL 占位修复。"
tags: ["task.debugging", "topic.tiling", "topic.implementation.tiling"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# ACLNN 361001 — tilingKey 与 funcEntry 映射失

## 现象

在为 TileWithAxis 算子（ascend950 / arch35）实现 Branch-1 kernel（`tilingKey=1, ubAxis=inner`）后，运行 aclnn ST：`aclnnTileWithAxisGetWorkspaceSize` 与 `aclnnTileWithAxis`（launch）均返回 OK，但 `aclrtSynchronizeStream(stream)` 返回 **361001**。所有 Branch-1 ST 用例（10 个）失败，只有 BR1-9（空张量，走 op_api 空快速路径）通过。开启 `ASCEND_GLOBAL_LOG_LEVEL=0` 抓运行时日志，定位到运行时调用 `BinaryGetFunctionByEntry(funcEntry=1)` 找不到入口——kernel 二进制只注册了 `funcEntry_0`，而 Host TilingFunc 调用了 `context->SetTilingKey(1)`。Branch-2（tilingKey=2）与 Branch-3（tilingKey=3）首次联调时同样以 361001 失败，因为 stub kernel 仅有 `funcEntry_0`。

## 适用场景

- **工程形态**：aclnn 算子开发（ops-registry-invoke），Host TilingFunc 使用 `SetTilingKey(N)` 多分支分发，kernel 用 `ASCENDC_TPL` 模板按 KEY 编译多个分支。
- **API 路径**：`ASCENDC_TPL` / `ASCENDC_TPL_SEL` / `ASCENDC_TPL_ARGS_SEL` / `ASCENDC_TPL_UINT_SEL`（struct.h 中声明 KEY 取值列表）；Host 侧 `context->SetTilingKey()`；运行时 `BinaryGetFunctionByEntry(funcEntry=tilingKey)`。
- **验证过的平台与 CANN 版本**：Ascend950（arch35），CANN 9.1.0。
- **适用粒度**：`operator_family`（任何使用 `SetTilingKey` + `ASCENDC_TPL` 多分支 kernel 分发的 AscendC 算子）。
- **路线优先级**：`recommended_fastpath`。
- **明确不适用或未验证场景**：单分支（无 `SetTilingKey` 或恒为 0）的算子不会触发；a2/a3 平台未验证（推断可迁移，标注于 `## 失效边界`）。

## 判别方法

1. **触发信号**：aclnn launch 返回 OK 但 `aclrtSynchronizeStream` 报 361001；或 ST 全部用例（除走空快速路径的空张量用例）一致失败。
2. **可执行探针**：查看部署后的 kernel 配置 JSON（`$ASCEND_OPP_PATH/opp/vendors/<OpType>/op_impl/ai_core/tbe/kernel/config/ascend950/<op>.json`）的 `binList` 与 funcEntry 列表；再 `cat` 构建产物中的 kernel list 文件，确认注册了哪些 `funcEntry_N`。
3. **原始观测**：运行时 DEBUG 日志显示 `BinaryGetFunctionByEntry(funcEntry=N)` 失败（kernel 二进制仅含 `funcEntry_0`），而 Host 侧 `SetTilingKey(N)` 设置了 N>0。
4. **解释**：funcEntry = `ASCENDC_TPL_SEL` 列表中的**位置（index_value）**；运行时**直接令 `funcEntry = tilingKey`** 查找入口。因此要让 `tilingKey=1` 可达，必须让 `KEY=1` 的 SEL 组合出现在 SEL 列表的 index 1 处——即需要一个 index 0 的占位（dummy KEY=0，运行时永不调用），再放 KEY=1。同理 KEY=2 放 index 2。funcEntry 既不是 tilingKey 的编码值本身，也不是 DECL 列表顺序——它是 SEL 列表中该组合的**位置**；只有当 SEL 按 KEY 升序且无空缺时，位置才恰好等于 KEY。

## 解决配方

修复在 `op_kernel/arch35/<op>_struct.h` 的 `ASCENDC_TPL_SEL` 中显式列出全部 KEY（含 index 0 的占位 KEY_0），使每个 `tilingKey=N` 都能在 SEL 位置 N 找到对应入口；并在 kernel 头里 `#include` struct.h，使 `ASCENDC_TPL` 符号进入 tiling `.so`（kernel-file 链）。

**before**（struct.h 只声明了 KEY=0，SEL 仅一项 → 只有 funcEntry_0）：

```cpp
ASCENDC_TPL_SEL(
    ASCENDC_TPL_ARGS_SEL(
        ASCENDC_TPL_UINT_SEL(KEY, ASCENDC_TPL_UI_LIST, TILE_WITH_AXIS_KEY_0))
);
```

Host 调 `SetTilingKey(1)` 时运行时查 `funcEntry=1` 不存在 → 361001。

**after**（加入 KEY_0 占位 + KEY_1，使 KEY=1 位于 SEL 位置 1）：

```cpp
ASCENDC_TPL_SEL(
    ASCENDC_TPL_ARGS_SEL(
        ASCENDC_TPL_UINT_SEL(KEY, ASCENDC_TPL_UI_LIST, TILE_WITH_AXIS_KEY_0)),
    ASCENDC_TPL_ARGS_SEL(
        ASCENDC_TPL_UINT_SEL(KEY, ASCENDC_TPL_UI_LIST, TILE_WITH_AXIS_KEY_1))
);
```

Branch-2/3 同理扩展（KEY_2 放位置 2、KEY_3 放位置 3）：

```cpp
ASCENDC_TPL_SEL(
    ASCENDC_TPL_ARGS_SEL(
        ASCENDC_TPL_UINT_SEL(KEY, ASCENDC_TPL_UI_LIST, TILE_WITH_AXIS_KEY_0)),
    ASCENDC_TPL_ARGS_SEL(
        ASCENDC_TPL_UINT_SEL(KEY, ASCENDC_TPL_UI_LIST, TILE_WITH_AXIS_KEY_1)),
    ASCENDC_TPL_ARGS_SEL(
        ASCENDC_TPL_UINT_SEL(KEY, ASCENDC_TPL_UI_LIST, TILE_WITH_AXIS_KEY_2))
);
```

kernel 头需 include struct.h（使 ASCENDC_TPL 符号在 tiling .so 中可见，参考 scale_custom 的 kernel-file 链）。

## 验证信号

本次开发会话（TileWithAxis Branch-1 联调）修复后实测：

- 构建产物 kernel 配置 JSON 中出现 `funcEntry_0`（KEY=0 占位）与 `funcEntry_1`（KEY=1 Branch-1）两个入口（来源平台：950；证据等级: tool_observed）。
- Branch-1 aclnn ST：10/10 用例 bitwise 通过，含空张量、特殊值、多核、全部 dtype（来源平台：950；证据等级: tool_observed）。
- 回归：公共 TilingUT 21/21 + Branch-1 TilingUT 10/10 均无退化（来源平台：950；证据等级: tool_observed）。
## 失效边界

- Ascend950（arch35）实测；a2/a3 平台未验证，推断可迁移（`ASCENDC_TPL` / `SetTilingKey` 为跨 arch 通用机制），但 funcEntry 编号策略是否随 toolkit 版本变化未验证。
- 若 SEL 列表顺序与 KEY 升序不一致（例如 SEL{2,1}），funcEntry≠tilingKey，本卡的"位置=tilingKey"简化不再成立——需按 SEL 实际位置核对 kernel JSON。
- 本卡仅覆盖 funcEntry 注册缺失导致的 361001；kernel 本身访问非法内存同样可能引发 361001 类（vector core exception），需用 507035/361001 的运行时日志区分。

## 预防

- 任何使用 `SetTilingKey(N>0)` 的算子，struct.h 的 `ASCENDC_TPL_SEL` 必须为 0..N 全部 KEY 显式列出 SEL 项，且 KEY=0 留作占位（不调用）。
- 联调前先 `cat` kernel 配置 JSON 确认 funcEntry 数量 = tilingKey 取值数 + 1（含占位）。

## 坏实践

- 只在 SEL 中列出"用到的 KEY"而忽略 index 0 占位 → funcEntry 编号错位，`tilingKey=1` 命中 index 0 的占位而非 KEY=1。
- 误以为 funcEntry = tilingKey 的编码值（实际 funcEntry = SEL 位置），跳过占位直接放 KEY=1 于 index 0 → `tilingKey=1` 查 `funcEntry_1` 仍不存在。

## 误诊

- 起初误判为 kernel 未实现/空 kernel 崩溃（507035 vector core exception），后通过运行时 DEBUG 日志定位到 `BinaryGetFunctionByEntry(funcEntry=1)` 失败，才确认是 funcEntry 注册问题而非 kernel 本身崩溃（agent_reported，非实测信号）。

<!-- cannbot:related:start -->
## 相关

- [ASCENDC_TPL_SEL_PARAM](../../apis/utils_api/tiling_template_programming/ascendc_tpl_sel_param.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《ASCENDC_TPL_SEL_PARAM》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [EnableL1BankConflictOptimise](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/enable_l1_bank_conflict_optimise.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《EnableL1BankConflictOptimise》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [GET_TPL_TILING_KEY](../../apis/utils_api/tiling_template_programming/get_tpl_tiling_key.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《GET_TPL_TILING_KEY》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [IcpuSetTilingKey](../../apis/simd_api/basic_api/debug_interface/cpu_twin_debug/icpu_set_tiling_key.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《IcpuSetTilingKey》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [REGISTER_TILING_FOR_TILINGKEY](../../apis/simd_api/basic_api/kernel_tiling/register_tiling_for_tilingkey.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《REGISTER_TILING_FOR_TILINGKEY》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [TILING_KEY_IS](../../apis/simd_api/basic_api/kernel_tiling/tiling_key_is.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《TILING_KEY_IS》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [TILING_KEY_LIST](../../apis/simd_api/basic_api/kernel_tiling/tiling_key_list.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《TILING_KEY_LIST》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [TilingData结构注册](../../apis/utils_api/tiling_data_structure_register/tiling_data_struct_register.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《TilingData结构注册》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [aclnn 全绿但 GE 图模式 error 263 分层判别](aclnn_ge_error_263.md)（`related`）：当图模式选择了不存在的 kernel 变体时，tilingKey 与 funcEntry 映射错位会表现为 361001；目标卡提供映射位置校验法，补足总卡的第三条分支。
- [sub-kernel 后缀 _N 是 tilingKey 位编码非序号](sub_kernel_n_tilingkey.md)（`related`）：focal 解释后缀 key 值后，该卡补充运行时还会以 tilingKey 查 funcEntry；SEL 位置/占位若与 key 不一致会报 361001，可把设计性 gap 与入口缺失区分。
- [多分支策略](../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/multi_branch_strategy.md)（`related`）：多分支策略 与《ACLNN 361001 — tilingKey 与 funcEntry 映射失》的实质衔接是：多分支策略由 Host 选择 TilingKey、Kernel 用 TILING_KEY_IS 常量折叠；REGISTER_TILING_DEFAULT/FOR_TILINGKEY 绑定结构，GET_TILING_DATA 取参数，所选故障卡分别验证 key 编码、funcEntry、缓存和默认结构注册失配。
- [运行时加载机制](../../guides/programming_guide/advanced_programming/aclnn_operator_development/invocation/runtime_loading_mechanism.md)（`related`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《运行时加载机制》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [高级编程基本流程](../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/host_tiling_implementation.md)（`related`）：高级编程基本流程 与《ACLNN 361001 — tilingKey 与 funcEntry 映射失》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [561103: isGroup=-1 哨兵致 tilingKey 路由失配](561103_isgroup_1_tilingkey.md)（`same_topic`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《561103: isGroup=-1 哨兵致 tilingKey 路由失配》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [GMM A8W4 561000 缺 binary entry 无 JIT 回退](gmm_a8w4_561000_binary_entry_jit.md)（`same_topic`）：GMM 卡观测 tilingKey=91308033 查不到 funcEntry；目标卡系统解释 SetTilingKey 到 binary funcEntry 注册缺口及核验方法，是同一运行时失败机制。
- [kernel.h 须 include struct.h 才能识别 TPL](ascendc_tpl_kernel_h_must_include_struct_h.md)（`same_topic`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《kernel.h 须 include struct.h 才能识别 TPL》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [tilingKey 编码与 TPL 位打包不一致致路由错误](tiling_key_tpl_bit_encoding_mismatch.md)（`same_topic`）：tilingKey 编码与 TPL 位打包不一致致路由错误：这些卡沿同一 TPL 路由链闭合：GET_TPL_TILING_KEY按位编码，host funcEntry必须使用相同值，sub-kernel后缀展示实际编码，ASCENDC_TPL_SEL缺失或 isGroup哨兵会在相邻环节产生同类错路由。 目标卡《ACLNN 361001 — tilingKey 与 funcEntry 映射失》补充：Host SetTilingKey(N) 后运行时按 funcEntry=tilingKey 查找内核入口，若 kernel 二进制未通过 ASCENDC_TPL_SEL 在对应 SEL 位置注册该 funcEntry，则 BinaryGetFunctionByEntry 失败并报 361001。给出 funcEntry=SEL 位置=tilingKey 的判别与 SEL 占位修复。
- [缺 ASCENDC_TPL_SEL 致运行时分发静默 no-op 跳过](ascendc_tpl_sel_no_op.md)（`same_topic`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《缺 ASCENDC_TPL_SEL 致运行时分发静默 no-op 跳过》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
<!-- cannbot:related:end -->
