---
type: "Runbook"
title: "GET_TILING_DATA 首参传类型名致变量遮蔽类型"
description: "GET_TILING_DATA(<类型名>, tiling) 把类型名作宏首参，宏展开声明同名变量遮蔽类型，致 InitTilingData<HistogramTilingData> 模板实参 T 无法匹配 InitTilingData(const __gm__ uint8_t*, T*) 签名，报 candidate template ignored: invalid explicitly-specified argument for template parameter 'T'；判别依据为编译错 expanded from macro 行 &tiling_data 取首参地址，证明首参为变量名。"
tags: ["task.debugging", "topic.implementation.tiling"]
status: draft
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: []
aliases: ["variable_name_shadowing"]
---

# GET_TILING_DATA 首参传类型名致变量遮蔽类型

## 适用场景

- **工程形态**：自定义算子工程（ops-registry-invoke），kernel 侧用 `GET_TILING_DATA` 宏从 GM 拷贝 tiling 数据到本地变量（CANN 8.5.0-beta.1 自动生成 `kernel_meta_*/..._tiling_data.h` 提供 `GET_TILING_DATA`/`InitTilingData` 宏与 `HistogramTilingData` 类）。
- **API 路径**：`GET_TILING_DATA(var_name, tiling_arg)` → 展开为 `HistogramTilingData var_name; InitTilingData<HistogramTilingData>(tiling_arg, &var_name);`（首参为变量名，非类型名）。
- **验证平台与版本**：Ascend 910B（AIV only，不在注册平台词表 `950/a3/a2`，`platforms: []` 未定位）；CANN 8.5.0-beta.1。
- **适用粒度**：`platform_wide`——任何用 `GET_TILING_DATA` 宏的 kernel 均可能误传类型名作首参，不依赖具体算子公式。
- **不适用或未验证场景**：CANN 9.x 的 `GET_TILING_DATA` 宏签名是否相同未验证；若宏签名变更（如显式分类型/变量名两参）则本卡描述的遮蔽不再适用，迁移前先读生成的 `tiling_data.h` 确认宏展开。

## 判别方法

**触发**（tool_observed 失败）：在 Ascend 910B 上开发 Histogram 自定义算子，上一处 tiling 头冲突编译错修复后，kernel 入口改用 `GET_TILING_DATA(HistogramTilingData, tiling)` 从 GM 拷贝 tiling 数据。再次 `make` 构建，kernel 代码生成阶段报（verbatim 编译错，取自会话内 `make` 输出）：

```text
histogram.cpp:153:7: error: no matching function for call to 'InitTilingData'
      GET_TILING_DATA(HistogramTilingData, tiling);
      ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.../kernel_meta_Histogram_..._tiling_data.h:169:5: note: expanded from macro 'GET_TILING_DATA'
    InitTilingData<HistogramTilingData>(tiling_arg, &tiling_data);
    ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.../kernel_meta_Histogram_..._tiling_data.h:30:59: note: candidate template ignored: invalid explicitly-specified argument for template parameter 'T'
__inline__ __attribute__((always_inline)) __aicore__ void InitTilingData(const __gm__ uint8_t *p_tilingdata, T *tilingdata)
                                                          ^
```

随后连锁 `ld.lld: error: cannot open .../kernel_meta_Histogram_..._2.o` 与 `RuntimeError: Kernel Compilation Error: OpType Histogram`。

**探针**（可执行检查）：

1. 读编译错 `expanded from macro` 指向的自动生成头 `..._tiling_data.h` 第 169 行（`GET_TILING_DATA` 宏展开模板），确认展开形如 `InitTilingData<HistogramTilingData>(tiling_arg, &tiling_data);`——`&tiling_data` 取的是宏首参的地址，证明首参被用作**变量名**而非类型。
2. 对照 built-in kernel（如 `histogram_v2`）的 `GET_TILING_DATA` 调用，确认正解首参为小写变量名（如 `tilingData`），与类型名（大写首字母）区分。
3. 在报错 kernel 行把宏首参从类型名 `HistogramTilingData` 改为小写变量名 `tilingData`，重跑 `make`，观察 `no matching function for call to 'InitTilingData'` 与 `candidate template ignored` 是否消失。

**观测**（tool_observed）：

- 编译错 `expanded from macro` 行为 `InitTilingData<HistogramTilingData>(tiling_arg, &tiling_data);`——`&tiling_data` 取宏首参地址，首参=变量名。
- `InitTilingData` 模板签名为 `void InitTilingData(const __gm__ uint8_t *p_tilingdata, T *tilingdata)`，模板参数 `T` 须匹配第二参指针类型；显式实参 `InitTilingData<HistogramTilingData>` 被编译器拒绝：`candidate template ignored: invalid explicitly-specified argument for template parameter 'T'`。

**判读**（根因解读）：`GET_TILING_DATA` 宏首参是变量名。首参传类型名 `HistogramTilingData` 时，宏展开声明变量 `HistogramTilingData HistogramTilingData;`——**变量名遮蔽类型名**；于是 `InitTilingData<HistogramTilingData>` 中的 `HistogramTilingData` 解析为变量而非类型，模板参数 `T` 无法匹配 `InitTilingData(const __gm__ uint8_t*, T*)` 的签名，编译器报 `candidate template ignored: invalid explicitly-specified argument for template parameter 'T'`。关键判据二联：宏展开行 `&<首参>` 取地址证明首参为变量名；显式模板实参与变量名同名时被解析为变量致模板实参无效。

## 验证信号

来源：本次 Histogram 自定义算子开发会话（Ascend 910B，CANN 8.5.0-beta.1，kernel 改用 `GET_TILING_DATA` 后的二次构建与 judge 运行）。

- 按判读把宏首参从类型名 `HistogramTilingData` 改为小写变量名 `tilingData` 后，下一次 judge 运行返回 `ret=561002`（aclnn 运行时错，aclnnHistogramGetWorkspaceSize 层）而**不再是 kernel 编译错**——`no matching function for call to 'InitTilingData'` 与 `candidate template ignored` 消失，kernel 已成功编译生成二进制（来源平台:未定位（Ascend 910B）；证据等级: tool_observed）

<!-- cannbot:related:start -->
## 相关

- [GET_TILING_DATA](../../apis/simd_api/basic_api/kernel_tiling/get_tiling_data.md)（`exemplifies`）：获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。以宏展开方式编译。Host 侧需定义 TilingData 结构体并注册 Tiling 函数。返回默认注册的结构体。支持 950/a2/a3。；`GET_TILING_DATA(var_name, tiling_arg)` → 展开为 `HistogramTilingData var_name; InitTilingData<HistogramTilingData>(tiling_arg, &var_name);`（首参为变量名，非类型名）。。运行手册用真实宏展开说明接口首参为何必须是变量名，并给出编译失败探针。
- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](get_tiling_data_with_struct.md)（`related`）：“`GET_TILING_DATA` 宏首参是变量名。”对应 InitTilingData 模板实参错误中的类型名遮蔽；“`GET_TILING_DATA_WITH_STRUCT` 宏内部对 `tiling_struct` 参数做 `#` 字符串化”对应模板类型解析错和节级注册丢失，可据所用宏分流诊断。
<!-- cannbot:related:end -->
