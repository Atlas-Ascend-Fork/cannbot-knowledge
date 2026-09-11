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