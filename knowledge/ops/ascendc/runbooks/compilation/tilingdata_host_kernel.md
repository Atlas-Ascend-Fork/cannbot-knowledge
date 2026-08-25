---
type: "Runbook"
title: "TilingData 须 host 与 kernel 各定义一份"
description: "新增 TilingData struct 只写进 kernel 侧 struct.h 时 host 编译报 does not name a type；须在 host 可见头内同 namespace 重新定义一份，字段与 kernel 侧逐字一致，仿 SIMT 双定义模式。"
tags: ["task.debugging", "topic.implementation.operator_registration", "topic.tiling"]
status: stable
sources: []
created_at: "2026-08-18T08:28:30Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# TilingData 须 host 与 kernel 各定义一份

## 现象

为 `max_pool3d_grad`（Ascend950 / arch35）新增 separable tiling 路径时，把新 TilingData struct `MaxPool3DGradSeparableTilingData` 只写进了 kernel 侧头文件 `pooling/max_pool3d_grad/op_kernel/arch35/max_pool3d_grad_struct.h`，并在 host 侧 tiling 类头 `pooling/max_pool3d_grad/op_host/arch35/max_pool3d_grad_separable_tiling.h` 里直接 `#include "../../op_kernel/arch35/max_pool3d_grad_struct.h"` 以图取到该 struct。

构建 host 库（`bash build.sh --soc=ascend950 --ophost --noexec -j8`）报：

```
.../op_host/arch35/max_pool3d_grad_separable_tiling.h:28:5: error: 'MaxPool3DGradSeparableTilingData' does not name a type; did you mean 'MaxPool3DGradSeparableTiling'?
.../op_host/arch35/max_pool3d_grad_separable_tiling.h:22:50: error: 'MaxPool3DGradSeparableTilingData' was not declared in this scope; did you mean 'MaxPool3DGradSeparableTiling'?
.../op_host/arch35/max_pool3d_grad_separable_tiling.h:22:84: error: no matching function for call to 'gert::TilingContext::GetTilingData<<expression error>>()'
```

## 适用场景

- **工程形态**：算子仓开发，在 `op_host/arch35/` 下新增 tiling 类，其构造函数用 `context_->GetTilingData<MyTilingData>()` 取一个**本算子新定义的** TilingData struct 指针。
- **API 路径**：`GetTilingData<T>` 模板实例化要求 `T` 在 host 翻译单元内是完整类型；相关头为 `pool3d_grad_struct_common.h`（host 侧 struct 汇总头）与 `max_pool3d_grad_struct.h`（kernel 侧 struct 汇总头）。
- **验证平台与 CANN 版本**：Ascend950（arch35），`bash build.sh --soc=ascend950 --ophost --noexec -j8`。
- **适用粒度**：`operator_family`——任何"新 tiling 路径引入新 struct、且 struct 被同时用于 host tiling 计算与 kernel 计算"的算子都适用，不限于 pooling。
- **路线优先级**：`recommended_fastpath`——host/kernel 双定义是既有 SIMT 路径的标准模式，新路径照做即可。
- **不适用或未验证场景**：若新 struct 只在 kernel 侧使用、host 不 `GetTilingData` 它，则无需在 host 头定义；若能改公共 host 头 `pool3d_grad_struct_common.h` 也可只在那里定义一次（本 trace 该公共头跨算子共享、不能改）。a2/a3 未构建，未验证。

## 根因

AscendC 算子的 TilingData struct 需要同时被两个编译器看到：
1. **host 编译器**（编译 `op_host/*.cpp`，经 `pool3d_grad_struct_common.h` 取 struct）；
2. **kernel 编译器**（编译 `op_kernel/*.cpp`，经 `max_pool3d_grad_struct.h` 取 struct，该头还会 include kernel-only 头如 `kernel_operator.h`）。

kernel 侧 `max_pool3d_grad_struct.h` 含 kernel-only 构造，host 翻译单元不能 include 它。因此一个被 host 与 kernel 共用的 struct 必须**在两处分别定义**：一次在 host 可见的头（如 `pool3d_grad_struct_common.h` 或 host tiling 类头），一次在 kernel 可见的头（`max_pool3d_grad_struct.h`）。两边定义在同一 `namespace Pool3DGradNameSpace` 内、字段完全一致，靠**翻译单元隔离**避免重定义——host 翻译单元只看到 host 那份，kernel 翻译单元只看到 kernel 那份。

既有 SIMT 路径正是此模式：`MaxPool3DGradSimtTilingData` 同时存在于 `pool3d_grad_struct_common.h`（host）与 `max_pool3d_grad_struct.h`（kernel）。本 trace 的新 struct 只写进了 kernel 那份，host 翻译单元看不到，`GetTilingData<MaxPool3DGradSeparableTilingData>` 模板实例化时 `T` 不是完整类型，遂报 `does not name a type`。

## 判别方法

本规则按"触发 → 探针 → 观测 → 判别"四段组织；触发与观测均为 trace 中 tool_observed 的编译输出。

1. **触发（tool_observed 编译错）**：host 库构建报 `'MaxPool3DGradSeparableTilingData' does not name a type` / `was not declared in this scope`，并伴随 `no matching function for call to 'gert::TilingContext::GetTilingData<<expression error>>()'`，出错行指向 host tiling 类头里 `GetTilingData<新 struct>` 调用点。即命中本规则。

2. **探针（可执行检查）**：
   - 检查 host tiling 类头的 include 列表是否出现 `#include "../../op_kernel/.../struct.h"`——kernel 头通常带 kernel-only 构造，host 翻译单元吃不下；
   - 检查新 TilingData struct 是否**只**定义在 kernel 侧 `*_struct.h`，而在 host 可见的 struct 汇总头（如 `pool3d_grad_struct_common.h`）或 host tiling 类头里没有同 namespace 下的定义；
   - 可用 `grep -rn "struct <TilingDataName>" op_host/ op_kernel/` 确认该 struct 在 host 与 kernel 两侧是否各有一份。

3. **观测（tool_observed）**：修改前 host 构建报上述 `does not name a type` 三连错；把 host 头里对 kernel 侧 struct 头的 include 去掉、改为在 host 头内 `namespace Pool3DGradNameSpace` 中直接定义该 struct（字段与 kernel 侧逐字一致）后，host 库构建成功并链接 `libophost_nn.so`：`[100%] Built target ophost_nn`。

4. **判别（interpretation）**：若触发报错命中 `does not name a type` / `was not declared in this scope` 且探针确认 struct 仅在 kernel 侧定义、host 头试图 include kernel struct 头，根因是 host 翻译单元看不到该 struct（kernel 头含 kernel-only 构造不可被 host include），**正确修复方向是在 host 可见头内同 namespace 重新定义一份**，而不是修 `GetTilingData` 模板或给 kernel 头加 `#ifdef` 让 host 吃下。两边字段顺序与类型必须逐字一致，否则 host 写入的 tiling data 与 kernel 读取的布局错位，会引发运行时数据错乱（非编译期错误，更难查）。

## 预防

- 新增 TilingData struct 时，同步在 host 可见头与 kernel 可见头**各定义一份**，字段顺序/类型逐字一致；优先放在算子既有的 host struct 汇总头（若该头非跨算子共享、可改）。若公共 host 头不可改（如本 trace 的 `pool3d_grad_struct_common.h` 被多算子共用），则把 host 那份定义放进新 tiling 类自己的 host 头。
- host 头 include 列表里若出现 `#include "../../op_kernel/..."`，视为危险信号——kernel 头通常带 kernel-only 构造，host 翻译单元不能吃。
- 用 `GetTilingData<T>()` 前，确认 `T` 在 host 翻译单元是完整类型（不只是前向声明）。

## 坏实践

- 只在 kernel 侧 struct.h 定义新 struct，指望 host 头 include kernel 头来取——host 编译器吃不下 kernel-only 头，要么直接报错、要么把 struct 定义吞掉后报 `does not name a type`。
- host 与 kernel 两份定义字段顺序/类型不一致——编译能过，但 tiling data 布局错位，运行时拿到错值，是极难定位的运行错。

## 验证信号

- host 编译报 `'MaxPool3DGradSeparableTilingData' does not name a type` / `was not declared in this scope` / `no matching function for call to 'GetTilingData<<expression error>>()'`，指向 host tiling 类头的 `GetTilingData` 调用点（来源平台:950；证据等级:tool_observed）。
- 改为 host 头内同 namespace 直接定义 struct、去掉对 kernel 侧 struct 头的 include 后，host 库构建成功：`[100%] Built target ophost_nn`（来源平台:950；证据等级:tool_observed）。

未上板运行：本卡只证明"host 翻译单元可见 struct、host 库链接成功"，不证明运行正确性。

## 失效边界

- 本卡仅构建验证于 Ascend950（arch35）；a2/a3 未构建。host/kernel 双定义是 AscendC tiling 框架的通用约束——未验证，推断可迁移到 a2/a3。
- struct 的具体字段集（32 个 `int64_t`）是 max_pool3d_grad separable 路径的设计产物；迁移到其它算子时字段随该算子的 tiling 需求变化，但"host/kernel 各定义一份、字段逐字一致"的模式不变。

<!-- cannbot:related:start -->
## 相关

- [Kernel Tiling](../../apis/simd_api/basic_api/kernel_tiling/kernel_tiling.md)（`exemplifies`）：TilingData 须 host 与 kernel 各定义一份说明新增 TilingData struct 只写进 kernel 侧 struct.h 时 host 编译报 does not name a type；须在 host 可见头内同 namespace 重新定义一份，字段与 kernel 侧逐字一致，仿 SIMT 双定义模式。
- [TilingData结构定义](../../apis/utils_api/tiling_data_structure_register/tiling_data_struct_definition.md)（`exemplifies`）：TilingData 须 host 与 kernel 各定义一份：本故障来自host不可见kernel侧struct；TilingData定义/注册/属性传递卡给出正式契约，struct.h include与手写头遮蔽、rebase字段失配卡覆盖同一双侧类型同步链的具体失败。 目标卡《TilingData结构定义》补充：定义TilingData类并添加成员变量以保存Tiling参数，继承TilingDef基类后提供set/get字段、序列化保存和长度获取等接口。
- [TilingData结构注册](../../apis/utils_api/tiling_data_structure_register/tiling_data_struct_register.md)（`exemplifies`）：TilingData 须 host 与 kernel 各定义一份：本故障来自host不可见kernel侧struct；TilingData定义/注册/属性传递卡给出正式契约，struct.h include与手写头遮蔽、rebase字段失配卡覆盖同一双侧类型同步链的具体失败。 目标卡《TilingData结构注册》补充：注册定义的TilingData结构体并和自定义算子绑定。具体使用说明请参考调用示例。
- [Host 缺 SetDataSize 致 TilingData 截断](../precision/host_setdatasize_tilingdata.md)（`related`）：The host/kernel dual-definition runbook protects the same byte-layout contract before SetDataSize can accurately describe it.
- [REGISTER_TILING_DEFAULT 取小档致 NaN](register_tiling_default_nan.md)（`related`）：REGISTER_TILING_DEFAULT 取小档致 NaN 与《TilingData 须 host 与 kernel 各定义一份》的实质衔接是：REGISTER_TILING_DEFAULT 决定 opParaSize，必须覆盖最大 TilingData struct；注册宏、GET 宏、host/kernel 结构、SetDataSize 与追加越界卡描述同一 buffer 尺寸链。
- [通过TilingData传递属性信息](../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_data_attributes.md)（`related`）：TilingData 须 host 与 kernel 各定义一份：本故障来自host不可见kernel侧struct；TilingData定义/注册/属性传递卡给出正式契约，struct.h include与手写头遮蔽、rebase字段失配卡覆盖同一双侧类型同步链的具体失败。 目标卡《通过TilingData传递属性信息》补充：本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingData，由框架传到Kernel侧。
- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](get_tiling_data_with_struct.md)（`same_topic`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《TilingData 须 host 与 kernel 各定义一份》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [GM_ADDR 标量不可解引用为 tiling 结构体指针](gm_addr_tiling.md)（`same_topic`）：GM_ADDR 标量不可解引用为 tiling 结构体指针 与《TilingData 须 host 与 kernel 各定义一份》的实质衔接是：GM_ADDR 在该入口是 __gm__ uint8_t 标量而非结构体指针；typed __gm__ tiling 指针、Kernel Tiling/GET_TILING_DATA 和地址空间案例给出正确入口与强转边界。
- [REGISTER_TILING_DEFAULT 多 struct 冲突](register_tiling_default_struct.md)（`same_topic`）：REGISTER_TILING_DEFAULT 多 struct 冲突 与《TilingData 须 host 与 kernel 各定义一份》的实质衔接是：一个算子只能有一个 REGISTER_TILING_DEFAULT struct；新分支须按 TilingKey 注册，GET 宏、Host/Kernel struct、SetDataSize 与冲突故障共同约束 buffer 和 key。
- [TILING_DATA_DEF 迁移 rebase 字段失配判别](tiling_data_def_rebase.md)（`same_topic`）：TilingData 须 host 与 kernel 各定义一份：本故障来自host不可见kernel侧struct；TilingData定义/注册/属性传递卡给出正式契约，struct.h include与手写头遮蔽、rebase字段失配卡覆盖同一双侧类型同步链的具体失败。 目标卡《TILING_DATA_DEF 迁移 rebase 字段失配判别》补充：把 tiling data 从手写嵌套 struct 重构为 TILING_DATA_DEF 宏框架后 rebase 上游,上游在旧 struct 新增的 7 个字段未同步补到新类型的 TILING_DATA_FIELD_DEF,kernel 侧 tiling_-> 直读这些字段会编译失败。判别=git status 报 rebase in progress 且冲突落在 SetRunInfoTiling 区域时,diff HEAD 侧旧
- [kernel.h 须 include struct.h 才能识别 TPL](ascendc_tpl_kernel_h_must_include_struct_h.md)（`same_topic`）：TilingData 须 host 与 kernel 各定义一份：本故障来自host不可见kernel侧struct；TilingData定义/注册/属性传递卡给出正式契约，struct.h include与手写头遮蔽、rebase字段失配卡覆盖同一双侧类型同步链的具体失败。 目标卡《kernel.h 须 include struct.h 才能识别 TPL》补充：给算子加 RANK 模板参数（ASCENDC_TPL_ARGS_DECL）后，若 *_kernel.h 未 include *_struct.h，asc_opc 在 apt.cpp 预处理 include 树里看不到 TPL 宏，退化成非模板调用，kernel 编译失败被 wrapper dummy-output 掩盖。
- [手动 tiling 头遮蔽自动生成类致 no member 判别](tiling_no_member.md)（`same_topic`）：TilingData 须 host 与 kernel 各定义一份：本故障来自host不可见kernel侧struct；TilingData定义/注册/属性传递卡给出正式契约，struct.h include与手写头遮蔽、rebase字段失配卡覆盖同一双侧类型同步链的具体失败。 目标卡《手动 tiling 头遮蔽自动生成类致 no member 判别》补充：JOIN_OP_DEF True 工程里，op_host 用 BEGIN_TILING_DATA_DEF 定义 TilingData 后构建系统会自动生成 kernel 侧同名类并经 kernel_tiling/kernel_tiling.h 注入；若 kernel 又手动 #include <op>_tiling.h 定义同名类、并 REGISTER_TILING_DEFAULT + reinterpret_cast 直接访问字段，编
<!-- cannbot:related:end -->
