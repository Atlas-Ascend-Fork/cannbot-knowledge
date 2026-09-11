---
type: "Runbook"
title: EZ9999 找不到 infer 回调 — 补 IMPL_OP 注册
description: GEIR 图模式全量 EXEC_FAILURE：OpDef SetInferDataType 绑定不进运行时注册表；在注册单元补 IMPL_OP V2 注册后恢复。
tags: [task.debugging, topic.implementation.operator_registration]
status: stable
sources: []
created_at: '2026-09-09T11:49:41Z'
updated_at: '2026-09-09T11:49:41Z'
platforms: ["950"]
cann_versions: ["9.0.0-beta.2"]
---
# EZ9999 找不到 infer 回调 — 补 IMPL_OP 注册


## 现象

在 AscendC 算子仓开发流程中给一个自定义算子（2 输入 5 输出、带 `has_bias` 布尔属性、宿主侧自写 InferShape/InferDataType）打通 GEIR 图模式验证：InferShape/InferDataType 从桩替换为完整实现后，`cmake` 构建算子包成功（`libcust_opsproto_rt2.0.so` 正常产出，`nm` 可见 `ge::InferShape` / `ge::InferDataType` 符号），kernel 二进制与 ops-info 均安装进本轮隔离 staging，随后跑 TTK GEIR 验证（`bash skills/geir-route-tester/scripts/run_ttk_geir.sh "$PWD" <OP> verify`）。结果正向套件 44 个用例**全部 EXEC_FAILURE、0 个 PASS**，结果 CSV 中每行报错原文：

```
ERROR: GEIR execution failed (rc=255): [TTK-GEIR] RunGraph failed: -1, error: EZ9999: Inner Error!
EZ9999[PID: 2660368] 2026-09-07-14:08:19.613.486 (EZ9999):  Can not find Node op1[ThnnFusedGruCellGrad] cust...
```

极具迷惑性的是：编译、链接、安装全绿，staging 加载日志（`AddSoToRegistry:Save so symbol and handle in path[.../libcust_opsproto_rt2.0.so] successfully!`）明确显示 .so 已加载，而报错文案却提示"确认 op_proto .so 是否加载成功"——当时代码状态是：InferShape/InferDataType 函数本体已完整实现并编入 .so，但**只经 OpDef 的 `SetInferShape`/`SetInferDataType` 绑定**（include `register/op_def_registry.h`），没有任何 `IMPL_OP` 注册。

## 适用场景

- 工程形态：AscendC 算子仓开发（ops-registry-invoke 流程）下的 GEIR/GE 图模式验证（TTK `geir` 套件）；aclnn 直调路径不经图准备阶段的注册表查找，不适用本卡。
- API 路径：宿主侧推导回调注册——`register/op_def_registry.h` 的 `OpDef::SetInferShape`/`SetInferDataType` 与 `register/op_impl_registry.h` 的 `IMPL_OP` / `gert::OpImplRegisterV2`。
- 验证过的平台与 CANN 版本：Ascend950（`AddConfig("ascend950")`、`kernel/ascend950` 产物、上板 GE 执行）+ CANN 9.0.0-beta.2（与 frontmatter `platforms` 一致）。
- 适用粒度：`operator_family`——任何走 GE 图模式、含宿主推导回调的自定义算子。
- 路线优先级：**recommended_fastpath**。
- 明确不适用/未验证：CANN 9.0.0-beta.2 之外版本未验证；只缺 InferShape 注册（不缺 InferDataType）是否同样失败未单独验证（本卡修复同时注册两者）；下述机制链中"两条查找通路不对称"的 CANN 内部实现细节为日志级证据支撑的推断。

## 根因

宿主侧 InferDataType 回调只经 OpDef `SetInferDataType` 绑定、未进入 `OpImplRegisterV2` 运行时注册表，GE 图准备阶段按注册表查找 infer_datatype 回调失败。

机制链（DEBUG 日志逐条对应，均在同轮 staging 加载区段内）：

1. .so 加载成功：`AddSoToRegistry:Save so symbol and handle in path[.../op_proto/lib/linux/x86_64//libcust_opsproto_rt2.0.so] successfully!`
2. 但运行时注册表只登记了 tiling 系回调：
   ```
   RegisterOpImplToRegistry:LocalRegistry[21998484978668984] Op type[ThnnFusedGruCellGrad] register OP_IMPL : [Tiling][TilingParse]
   ```
   ——没有 `[InferShape]`、没有 `[InferDataType]`。
3. `MergeFunctions` 对该算子只出现 `tiling_parse / compile_info_creator / compile_info_deleter / tiling / max_tiling_data_size func has been registered`，无 infer_shape/infer_datatype 注册行。
4. 图准备阶段 InferShape 以 V2 被调起（`CallInferFunc:Op op1[ThnnFusedGruCellGrad] Call InferShapeFuncV2`），随后 dtype 推导按注册表查找失败——这才是被截断的 `Can not find Node ... cust` 的全文：
   ```
   InferDtypeByRegisteredFuncOrRule: ErrorNo: 4294967295(failed)Can not find Node op1[ThnnFusedGruCellGrad] custom infer_datatype func. Please confirm whether the op_proto shared library (.so) has been loaded successfully, and that you have already developed the infer_datatype func or marked the T-derivation rules on the IR.
   InferDataTypeOnCompile: ErrorNo: 4294967295(failed)[Check][InferDataType] result failed, op_desc[op1], ret[-1]
   CallInferFuncV2:Assert failed: [Call][InferFuncV2]Failed to infer data_type of node op1[ThnnFusedGruCellGrad].
   ```
   → InferShapePass 失败 → `RunGraph failed: -1` → EZ9999。
5. `nm` 证实"函数在 .so 里、注册对象不在"：修复前 `T _ZN2ge10InferShapeEPN4gert17InferShapeContextE`、`T _ZN2ge13InferDataTypeEPN4gert20InferDataTypeContextE`（函数已定义）、`U _ZN3ops5OpDef16SetInferDataTypeEPFj...`（OpDef 绑定为外部引用），但没有 `op_impl_register_<OpType>` 静态对象。

一句话：**符号存在 ≠ 运行时注册**。`IMPL_OP` 宏在静态初始化期构造 `gert::OpImplRegisterV2(#op_type)` 对象并链式登记回调，运行时的 `RegisterOpImplToRegistry`/`MergeTypesToImpl` 只认这条通路；只做 OpDef 绑定，推导回调就不在注册表里。

## 判别方法

对 EXEC_FAILURE 的 GEIR 结果日志（`tests/geir/logs/positive-source-static.log`，需 DEBUG 级）执行：

```bash
grep -a "Can not find Node\|RegisterOpImplToRegistry.*<OpType>\|MergeTypesToImpl.*<OpType>\|CallInferFunc.*<OpType>" \
  operators/<OP>_package/tests/geir/logs/positive-source-static.log | head -10
```

- 命中 `register OP_IMPL : [Tiling][TilingParse]` 而**无** `[InferShape]`/`[InferDataType]`，且随后出现 `Can not find Node op1[<OpType>] custom infer_datatype func` → 即本卡根因。
- 再用 `nm` 双确认（函数符号在、注册对象缺）：

```bash
nm operators/<OP>_package/build/libcust_opsproto_rt2.0.so | grep -i "op_impl_register\|InferDataType\|InferShape"
```

修复前：有 `T _ZN2ge...InferShape/InferDataType...` 但无 `op_impl_register_<OpType>`；修复后应出现 `_ZL38op_impl_register_<OpType>0`（bss 静态对象）。

## 设计决策

- **双注册并存**：`IMPL_OP(<OpType>).InferShape(...).InferDataType(...)` 与 OpDef 的 `SetInferShape`/`SetInferDataType` 绑定同时保留，两者指向同一函数指针。图模式验证工作流的路由门禁本来就要求 `RegisterOpImplToRegistry` 出现 `[InferShape]`/`[InferDataType]` 且 `MergeTypesToImpl:op type <OpType> infer_shape/infer_datatype func registered first.`——只靠 OpDef 绑定既过不了运行时也过不了路由取证。
- **备选方案（未采用）**：`OpImplRegisterV2::InferOutDataTypeSameWithFirstInput()` 内建规则（头文件注释：将第一个输入的 datatype 作为所有输出的 datatype；若与自定义 InferDataType 同时注册，最后注册的规则生效）。若算子输出 dtype 全随首输入且无需在推导阶段拒收非法 dtype，可用该规则替代自定义 InferDataType；本算子需要在图推理阶段拒收 dtype 越界/不一致输入（负向用例契约），故保留显式函数。
- **注册位置**：放在 op_graph 侧注册翻译单元（graph_infer.cpp）文件尾、`namespace ge` 之外（宏展开为全局作用域静态对象），include 从 `register/op_def_registry.h` 换成 `register/op_impl_registry.h`；InferShape 函数本体仍在 op_host 文件中，用前置声明衔接（两文件链入同一个 .so）。
- **为何不退回 V1**：仓库自带的 legacy V1 示例（`COMMON_INFER_FUNC_REG`）是编译检查用途、默认不链接；工作流明确把命中 `InferShapeFuncV1` 视为硬停止条件，必须走 V2（`IMPL_OP`）。

## 系统信息

- 工具链：CANN 9.0.0-beta.2（`/home/<user>/Ascend/cann-9.0.0-beta.2`，x86_64-linux 头文件）；TTK GEIR runner（隔离 staging + `ASCEND_CUSTOM_OPP_PATH`）。
- 目标平台：Ascend950（`AICore().SetTiling(...).AddConfig("ascend950")`）。
- 相关文件（与事件流实际读写一一对应）：
  - `operators/<OP>_package/op_graph/thnn_fused_gru_cell_grad_graph_infer.cpp`——本卡修改点（include + IMPL_OP 注册）
  - `operators/<OP>_package/op_host/thnn_fused_gru_cell_grad_infershape.cpp`——InferShape 本体（未改）
  - `operators/<OP>_package/op_host/thnn_fused_gru_cell_grad_def.cpp`——OpDef 绑定（保留）
  - `operators/<OP>_package/build/libcust_opsproto_rt2.0.so`——nm 检查对象
  - CANN 头：`register/op_impl_registry.h`、`register/op_def.h`、`register/op_def_registry.h`
- 构建/验证命令：
  ```bash
  source docs/<OP>/develop/env.sh
  cmake -S operators/<OP>_package -B operators/<OP>_package/build
  cmake --build operators/<OP>_package/build --target binary package -j
  bash skills/geir-route-tester/scripts/run_ttk_geir.sh "$PWD" <OP> verify
  ```

## 完整代码

**before**（`op_graph/thnn_fused_gru_cell_grad_graph_infer.cpp` 修复前全文——只有函数定义与 OpDef 绑定，无注册）：

```cpp
/**
 * =============================================================================
 * <OP>_package/op_graph/thnn_fused_gru_cell_grad_graph_infer.cpp
 * =============================================================================
 * Role: InferDataType (V2) for ThnnFusedGruCellGrad（经 OpDef
 *       SetInferDataType 绑定，非 IMPL_OP 注册）。五个输出 dtype 一律随
 *       grad_hy（proto.md §2 三组合内逐 IO 同 dtype）。校验输入 dtype 在合法域
 *       {DT_FLOAT, DT_FLOAT16, DT_BF16} 内且双输入一致，非法输入返回
 *       GRAPH_FAILED。
 * =============================================================================
 */

#include "register/op_def_registry.h"

namespace ge {

// [REF_SAMPLE] 原样例工程 InferDataType（x/y dtype 相等校验后写单输出 z）
// 整段注释保留，全文见 git 历史。本实现按 GRU 反传契约改为五输出随首输入，
// 并增加 dtype 合法域 + 双输入一致校验。

graphStatus InferDataType(gert::InferDataTypeContext* context)
{
    const ge::DataType gradHyDtype = context->GetInputDataType(0);
    const ge::DataType storageDtype = context->GetInputDataType(1);

    // ── dtype 合法域校验：仅 {DT_FLOAT, DT_FLOAT16, DT_BF16}（proto.md §2）──
    const bool gradHyOk =
        (gradHyDtype == ge::DT_FLOAT) || (gradHyDtype == ge::DT_FLOAT16) || (gradHyDtype == ge::DT_BF16);
    const bool storageOk =
        (storageDtype == ge::DT_FLOAT) || (storageDtype == ge::DT_FLOAT16) || (storageDtype == ge::DT_BF16);
    if (!gradHyOk || !storageOk) {
        return GRAPH_FAILED;
    }

    // ── 双输入 dtype 一致校验（proto.md §2：三组合内逐 IO 同 dtype）──
    if (gradHyDtype != storageDtype) {
        return GRAPH_FAILED;
    }

    // ── 五输出 dtype 随 grad_hy ──
    for (size_t i = 0; i < 5; ++i) {
        if (context->SetOutputDataType(i, gradHyDtype) != GRAPH_SUCCESS) {
            return GRAPH_FAILED;
        }
    }
    return GRAPH_SUCCESS;
}

} // namespace ge
```

**after**（同一文件修复后全文——include 换 `op_impl_registry.h`，文件尾追加 IMPL_OP V2 注册）：

```cpp
/**
 * =============================================================================
 * <OP>_package/op_graph/thnn_fused_gru_cell_grad_graph_infer.cpp
 * =============================================================================
 * Role: InferShape + InferDataType (V2) for ThnnFusedGruCellGrad。
 *       同时经 OpDef SetInferShape/SetInferDataType 绑定和 IMPL_OP V2 注册
 *       （OpImplRegisterV2），确保 runtime 能通过 RegisterOpImplToRegistry
 *       发现回调。五个输出 dtype 一律随 grad_hy（proto.md §2 三组合内逐 IO 同
 *       dtype）。校验输入 dtype 在合法域 {DT_FLOAT, DT_FLOAT16, DT_BF16} 内
 *       且双输入一致，非法输入返回 GRAPH_FAILED。
 * =============================================================================
 */

#include "register/op_impl_registry.h"

namespace ge {

// [REF_SAMPLE] 原样例工程 InferDataType（x/y dtype 相等校验后写单输出 z）
// 整段注释保留，全文见 git 历史。本实现按 GRU 反传契约改为五输出随首输入，
// 并增加 dtype 合法域 + 双输入一致校验。

graphStatus InferDataType(gert::InferDataTypeContext* context)
{
    const ge::DataType gradHyDtype = context->GetInputDataType(0);
    const ge::DataType storageDtype = context->GetInputDataType(1);

    // ── dtype 合法域校验：仅 {DT_FLOAT, DT_FLOAT16, DT_BF16}（proto.md §2）──
    const bool gradHyOk =
        (gradHyDtype == ge::DT_FLOAT) || (gradHyDtype == ge::DT_FLOAT16) || (gradHyDtype == ge::DT_BF16);
    const bool storageOk =
        (storageDtype == ge::DT_FLOAT) || (storageDtype == ge::DT_FLOAT16) || (storageDtype == ge::DT_BF16);
    if (!gradHyOk || !storageOk) {
        return GRAPH_FAILED;
    }

    // ── 双输入 dtype 一致校验（proto.md §2：三组合内逐 IO 同 dtype）──
    if (gradHyDtype != storageDtype) {
        return GRAPH_FAILED;
    }

    // ── 五输出 dtype 随 grad_hy ──
    for (size_t i = 0; i < 5; ++i) {
        if (context->SetOutputDataType(i, gradHyDtype) != GRAPH_SUCCESS) {
            return GRAPH_FAILED;
        }
    }
    return GRAPH_SUCCESS;
}

// 前置声明（定义在 op_host/thnn_fused_gru_cell_grad_infershape.cpp）
graphStatus InferShape(gert::InferShapeContext* context);

} // namespace ge

// ── V2 注册（OpImplRegisterV2）：使 InferShape/InferDataType 进入
//    RegisterOpImplToRegistry 通路，供 runtime MergeTypesToImpl 发现。
//    与 OpDef SetInferShape/SetInferDataType 并行，两者注册同一函数指针。──
IMPL_OP(ThnnFusedGruCellGrad)
    .InferShape(ge::InferShape)
    .InferDataType(ge::InferDataType);
```

（OpDef 侧 `this->SetInferShape(ge::InferShape).SetInferDataType(ge::InferDataType);` 保持不变。）

## 预防

给走 GE 图模式的算子仓上 GEIR 验证前过一遍检查清单：

1. 宿主推导回调一律补 `IMPL_OP(<OpType>)` V2 注册（`register/op_impl_registry.h`），不要只依赖 OpDef 的 `SetInferShape`/`SetInferDataType`——后者在图准备阶段不够用。
2. 构建后先 `nm` 自检：`nm <build>/libcust_opsproto_rt2.0.so | grep op_impl_register` 必须看到 `op_impl_register_<OpType><N>` 静态对象，再进六套件（单套件一轮十几分钟起步，别把注册问题留到图执行阶段才发现）。
3. 日志门禁三条：`RegisterOpImplToRegistry ... [<OpType>] ... [InferShape]`、`[InferDataType]` 与 `MergeTypesToImpl:op type <OpType> infer_shape/infer_datatype func registered first.`——必须落在**本轮 staging** 的 `AddSoToRegistry` 区段内（不能拿全局安装包的区段拼接证据）。
4. 报错文案让查".so 是否加载"，先用 `AddSoToRegistry` 日志排除加载问题，再查注册表——别被文案带偏去重装。

## 验证信号

以下信号来自该算子 GEIR 图模式联调：同一轮隔离 staging 验证运行（TTK GEIR 正向源码静态套件）的命令输出、CANN DEBUG 日志与结果 CSV；修复（IMPL_OP 注册）为该轮唯一代码改动，前后各跑完整一轮。

- 修复前：正向源码静态套件 44 用例全部 EXEC_FAILURE、0 PASS，报错原文 `ERROR: GEIR execution failed (rc=255): [TTK-GEIR] RunGraph failed: -1, error: EZ9999: Inner Error! ... Can not find Node op1[ThnnFusedGruCellGrad] cust...`（来源平台：Ascend950；证据等级：tool_observed）
- 注册表证据：`RegisterOpImplToRegistry:LocalRegistry[...] Op type[ThnnFusedGruCellGrad] register OP_IMPL : [Tiling][TilingParse]`——仅 Tiling/TilingParse，无推导回调（来源平台：Ascend950；证据等级：tool_observed）
- 精确定位：`InferDtypeByRegisteredFuncOrRule: ErrorNo: 4294967295(failed)Can not find Node op1[ThnnFusedGruCellGrad] custom infer_datatype func. ...` + `[Check][InferDataType] result failed, op_desc[op1], ret[-1]`（来源平台：Ascend950；证据等级：tool_observed）
- 修复后构建产物：`nm` 出现 `_ZL38op_impl_register_ThnnFusedGruCellGrad0` 静态注册对象（来源平台：Ascend950；证据等级：tool_observed）
- 修后首轮：首个用例从 EXEC_FAILURE 变为真实执行+比对通过（结果 CSV：`precision="PASS,PASS,PASS,100%,100%"`、`precision_status=PASS`）（来源平台：Ascend950；证据等级：tool_observed）
- 修后整轮：44/44 用例全部完成执行并进入精度比对，`Can not find Node` 报错消失（后续验证转入精度判读问题）（来源平台：Ascend950；证据等级：tool_observed）

## 失效边界

- 仅在 CANN 9.0.0-beta.2 + Ascend950 实测（单算子、单平台、单轮验证）；其他 CANN 版本的注册行为未验证，推断可迁移但未证实。
- aclnn 直调路径不经图准备阶段注册表查找，本卡不适用。
- "InferShape 经 OpDef 绑定即可被调起、InferDataType 必须走注册表"的两通路不对称性来自日志与头文件推断，CANN 内部实现源码未核；只缺 InferShape 注册的独立后果未验证。
- 单跑结果（内部 single_run），跨算子/跨轨迹复现待 curator 判定。

## 坏实践

- 只写函数 + OpDef 绑定就认为注册完成——`nm` 里有 `T ge::Infer*` 符号不代表运行时注册表有条目。
- 见到"Please confirm whether the op_proto shared library (.so) has been loaded successfully"就去重装/排查 .so 路径——该文案在本场景是误导，加载证据（AddSoToRegistry）与失败点（注册表查找）是两回事。
- 把注册问题留到六套件整轮跑完才发现：GEIR 单用例约 15-20s、单套件 15-20 分钟，先 `nm`+路由日志三条自检再上套件。

## 误诊

- **误诊 1（环境残留）**：先发现 CANN OPP 全局目录 `.../opp/vendors/<OP>` 有旧版安装包，怀疑与 staging 冲突，执行 `uninstall.sh --quiet` 卸载后重跑——仍 0 PASS / 43 行 EXEC_FAILURE。残留安装不是根因；卸载这一步对问题无效。
- **误诊 2（符号缺失）**：一度怀疑 InferDataType 没编进 .so——`nm` 推翻：函数符号是 `T`（已定义），缺的是 `op_impl_register_<OpType>` 静态注册对象。

## 未决事项

- 只缺 InferShape 注册（InferDataType 注册在）是否同样失败：未单独验证——可在下个算子上做对照实验（分别只注册其一）。
- 该版本 CANN 中 OpDef `SetInferDataType` 存储的函数指针究竟被哪条通路消费：未追到 CANN 实现源码层；建议复现时用 `ltrace`/断点或读 `op_impl_space_registry_v2_impl.cc` 对应版本源码确认两通路边界。
