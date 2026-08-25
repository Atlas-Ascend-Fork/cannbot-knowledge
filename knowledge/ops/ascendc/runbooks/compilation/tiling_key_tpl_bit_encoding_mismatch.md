---
type: "Runbook"
title: "tilingKey 编码与 TPL 位打包不一致致路由错误"
description: "host ComputeTilingKey 用语义顺序值 (0/1/2/3/4) 与 ASCENDC_TPL GET_TPL_TILING_KEY 的位打包编码 (0/4/2/1/5) 不一致，normal-tail-R 被路由到 group-tail-A 存根 sub-kernel 产出垃圾。"
tags: ["task.debugging", "topic.implementation.operator_registration", "topic.tiling"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# tilingKey 编码与 TPL 位打包不一致致路由错误

## 现象

在 Ascend 950 (dav-3510) 上实现 `euclidean_norm` 算子 Branch-0 (normal-tail-A) kernel 后跑 ACLNN ST（`operators/euclidean_norm_package/tests/aclnn`，`bash run.sh`）：11 条用例 5 PASSED、6 FAILED，其中 6 条失败全部是 tail-R 路径（`axes=[-1]` 或 2D `axes=[1]`，`ctx.isTailR = (axisNum % 2 == 0)` 为 true）。失败用例的 `actual` 不是 0 而是垃圾值（如 `actual=1168065792 expected=11`，0x45A00000 是 fp32 表示的 3200.0），说明 kernel 确实执行了但走了错模板。`inspect_build.py` 列出编译产物 sub-kernel 后缀为 `_0/_4/_2/_1/_5` 五个。

## 适用场景

- **工程形态**：ACLNN 算子仓开发（ops-registry-invoke），多分支 TPL kernel + host tiling。
- **API 路径**：`ASCENDC_TPL_ARGS_DECL` + `ASCENDC_TPL_SEL` + `GET_TPL_TILING_KEY`（`asc/include/tiling/template_argument.h`），host 侧 `gert::TilingContext::SetTilingKey`。
- **验证过的平台与 CANN 版本**：Ascend 950 (dav-3510)，CANN 9.1.0。
- **适用粒度**：`operator_family`（任何用 ASCENDC_TPL 多 bool 模板参数 + host ComputeTilingKey 的 Reduction 算子）。
- **路线优先级**：`recommended_fastpath`（host tilingKey 必须等于 TPL 位编码值）。
- **明确不适用或未验证场景**：单分支无 TPL 的 kernel（无 SetTilingKey）；非 dav-3510 平台的 bitWidth 假设未验证（TPL bitWidth 随参数 bitWidth 变化）。

## 根因

`ASCENDC_TPL_ARGS_DECL(EuclideanNorm, ASCENDC_TPL_BOOL_DECL(templateType,0,1), ASCENDC_TPL_BOOL_DECL(isEmptyTensor,0,1), ASCENDC_TPL_BOOL_DECL(isTailR,0,1))` 声明三个 bool 模板参数，每个 bitWidth=1。`GET_TPL_TILING_KEY(...)` 调 `AscendC::EncodeTilingKey` 按 bitWidth 顺序位打包：bit0=templateType(isGroup)、bit1=isEmptyTensor、bit2=isTailR。故 TPL sub-kernel 后缀为：
- (0,0,0)=0 → normal-tail-A
- (0,0,1)=4 → normal-tail-R（bit2=4）
- (0,1,0)=2 → empty
- (1,0,0)=1 → group-tail-A
- (1,0,1)=5 → group-tail-R

而 host 侧 `ComputeTilingKey(bool isGroup, bool isEmptyTensor, bool isTailR)` 用语义顺序编码 `empty=2 / normal-tail-A=0 / normal-tail-R=1 / group-tail-A=3 / group-tail-R=4`。当 host 对 normal-tail-R `SetTilingKey(1)`，runtime 按后缀 `_1` 路由到 TPL 解码为 (1,0,0)=group-tail-A 的 sub-kernel，而 group 模板的 Init/Process 是存根，输出垃圾。

## 解决配方

修复 `operators/euclidean_norm_package/op_host/arch35/euclidean_norm_tiling_common.cpp` 的 `ComputeTilingKey`，让其返回值与 TPL 位编码一致。

**修复前**（语义顺序编码）：

```cpp
// §9.11 — ComputeTilingKey: (isGroup, isEmptyTensor, isTailR) -> tilingKey
//   empty=2 / normal-tail-A=0 / normal-tail-R=1 / group-tail-A=3 / group-tail-R=4
// ===========================================================================
int32_t ComputeTilingKey(bool isGroup, bool isEmptyTensor, bool isTailR)
{
    if (isEmptyTensor) return 2;
    if (isGroup) return isTailR ? 4 : 3;
    return isTailR ? 1 : 0;
}
```

**修复后**（TPL 位编码）：

```cpp
// ===========================================================================
int32_t ComputeTilingKey(bool isGroup, bool isEmptyTensor, bool isTailR)
{
    // Encode as TPL bits: templateType(isGroup) at bit 0, isEmptyTensor at bit 1, isTailR at bit 2
    return (isGroup ? 1 : 0) | (isEmptyTensor ? 2 : 0) | (isTailR ? 4 : 0);
}

// §8.2 — RouteTilingKey: empty-first priority -> tail type -> group
int32_t RouteTilingKey(const EuclideanNormCtx& ctx)
{
    if (ctx.emptyKind != EuclideanNormEmptyKind::NORMAL) return 2;
    return ComputeTilingKey(ctx.isGroup, false, ctx.isTailR);
}
```

`HandleEmptyTensor` 调 `ComputeTilingKey(false,true,false)=(0)|(2)|(0)=2` 不变；normal/group 路径调 `ComputeTilingKey(ctx.isGroup,false,ctx.isTailR)`：normal-tail-A=0、normal-tail-R=4、group-tail-A=1、group-tail-R=5，与 TPL 后缀一一对应。

同步更新 tiling UT（`tests/tiling/test_tiling.cpp`）的 `OracleTilingKey` 与 `GroupRouteTest` 的 `expKey`：`group_tailR: 4->5`、`group_tailA: 3->1`、`normal_tailR_a: 1->4`。

## 验证信号

本卡验证来源为 dav-3510/CANN 9.1.0 的 ST 跑与 tiling UT 跑。

- ST 5/11 → 7/11：cases 5（unaligned_tail fp16）、6（int32_partial_chunk_trunc）由 garbage 输出转为 PASSED（来源平台：950；证据等级: tool_observed）
- tiling UT 修复后 common 66/66 + branch0 9/9 全 PASSED（来源平台：950；证据等级: tool_observed）
- sub-kernel 后缀 `_0/_4/_2/_1/_5` 与 host ComputeTilingKey 返回值 0/4/2/1/5 一一对应（来源平台：950；证据等级: artifact_verified）

## 设计决策

- 选 TPL 位编码而非保持语义顺序 + 加映射表：位编码是 `GET_TPL_TILING_KEY` 的既定契约，host 侧直接产出同值最简单、零映射、运行时无需二次查表。
- 放弃的候选：在 `SetTilingKey` 前加 `hostKeyToTplKey` 映射函数（语义保留 + 显式映射）——多一层间接、易漏维护，未被采用。
- 当前方案属 `recommended_fastpath`：host tilingKey 与 TPL 编码同构。

## 预防

- 凡用 `ASCENDC_TPL_ARGS_DECL` 声明多 bool 模板参数的算子，host `ComputeTilingKey` 必须按 `GET_TPL_TILING_KEY` 的位打包顺序（bitWidth=1 时按声明顺序 bit0/bit1/bit2…）返回值，禁止用语义顺序值。
- 用 `python3 .opencode/skills/ascendc-build-system/scripts/inspect_build.py <build_dir>` 列出实际 sub-kernel 后缀，与 host `SetTilingKey` 入参逐一比对，作为编译期回归门禁。

## 失效边界

- 推断可迁移：a2 / a3 平台同样使用 `ASCENDC_TPL` + `GET_TPL_TILING_KEY`，位打包逻辑同构——未验证，推断可迁移。
- 未验证：TPL 参数 bitWidth 非 1（如 int 枚举参数）时位布局不同，本卡公式不直接适用，需按 `EncodeTilingKey` 的 bitWidth 累加重算。

<!-- cannbot:related:start -->
## 相关

- [ASCENDC_TPL_SEL_PARAM](../../apis/utils_api/tiling_template_programming/ascendc_tpl_sel_param.md)（`exemplifies`）：ASCENDC_TPL_SEL_PARAM 与《tilingKey 编码与 TPL 位打包不一致致路由错误》的实质衔接是：TPL 参数必须与模板定义、GET_TPL_TILING_KEY 和 TILING_KEY_IS 位编码一致；所选故障卡覆盖缺宏、头文件、funcEntry 和缓存复用失配。
- [EnableL1BankConflictOptimise](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/enable_l1_bank_conflict_optimise.md)（`exemplifies`）：EnableL1BankConflictOptimise 与《tilingKey 编码与 TPL 位打包不一致致路由错误》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [GET_TPL_TILING_KEY](../../apis/utils_api/tiling_template_programming/get_tpl_tiling_key.md)（`exemplifies`）：tilingKey 编码与 TPL 位打包不一致致路由错误：这些卡沿同一 TPL 路由链闭合：GET_TPL_TILING_KEY按位编码，host funcEntry必须使用相同值，sub-kernel后缀展示实际编码，ASCENDC_TPL_SEL缺失或 isGroup哨兵会在相邻环节产生同类错路由。 目标卡《GET_TPL_TILING_KEY》补充：Tiling模板编程时，开发者通过调用此接口自动生成TilingKey。该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。 使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考Tiling模板编程。
- [IcpuSetTilingKey](../../apis/simd_api/basic_api/debug_interface/cpu_twin_debug/icpu_set_tiling_key.md)（`exemplifies`）：IcpuSetTilingKey 与《tilingKey 编码与 TPL 位打包不一致致路由错误》的实质衔接是：IcpuSetTilingKey 只在 CPU 孪生调试中选择 IcpuRunKf 的 kernel 分支；TILING_KEY 宏及路由故障卡直接约束编码、缓存和 funcEntry 映射。
- [TILING_KEY_IS](../../apis/simd_api/basic_api/kernel_tiling/tiling_key_is.md)（`exemplifies`）：该 runbook 给出 Host 语义编号与模板位打包编码不一致时分支路由错误的确定诊断，直接验证 key 判定契约。
- [TILING_KEY_LIST](../../apis/simd_api/basic_api/kernel_tiling/tiling_key_list.md)（`exemplifies`）：tilingKey 编码与 TPL 位打包不一致致路由错误说明host ComputeTilingKey 用语义顺序值 (0/1/2/3/4) 与 ASCENDC_TPL GET_TPL_TILING_KEY 的位打包编码 (0/4/2/1/5) 不一致，normal-tail-R 被路由到 group-tail-A 存根 sub-kernel 产出垃圾。
- [多分支策略](../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/multi_branch_strategy.md)（`related`）：多分支策略 与《tilingKey 编码与 TPL 位打包不一致致路由错误》的实质衔接是：多分支策略由 Host 选择 TilingKey、Kernel 用 TILING_KEY_IS 常量折叠；REGISTER_TILING_DEFAULT/FOR_TILINGKEY 绑定结构，GET_TILING_DATA 取参数，所选故障卡分别验证 key 编码、funcEntry、缓存和默认结构注册失配。
- [高级编程基本流程](../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/host_tiling_implementation.md)（`related`）：高级编程基本流程 与《tilingKey 编码与 TPL 位打包不一致致路由错误》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [561103: isGroup=-1 哨兵致 tilingKey 路由失配](561103_isgroup_1_tilingkey.md)（`same_topic`）：tilingKey 编码与 TPL 位打包不一致致路由错误：这些卡沿同一 TPL 路由链闭合：GET_TPL_TILING_KEY按位编码，host funcEntry必须使用相同值，sub-kernel后缀展示实际编码，ASCENDC_TPL_SEL缺失或 isGroup哨兵会在相邻环节产生同类错路由。 目标卡《561103: isGroup=-1 哨兵致 tilingKey 路由失配》补充：多分支归约算子 TilingFunc 重构后非 Group 分支未显式置 ctx.isGroup=0，-1 哨兵使 ChooseTilingKey 二值路由全分支失配返回 -1，TilingFunc GRAPH_FAILED 致 aclnn 561103。
- [ACLNN 361001 — tilingKey 与 funcEntry 映射失](aclnn_361001_tilingkey_funcentry_sel_position.md)（`same_topic`）：tilingKey 编码与 TPL 位打包不一致致路由错误：这些卡沿同一 TPL 路由链闭合：GET_TPL_TILING_KEY按位编码，host funcEntry必须使用相同值，sub-kernel后缀展示实际编码，ASCENDC_TPL_SEL缺失或 isGroup哨兵会在相邻环节产生同类错路由。 目标卡《ACLNN 361001 — tilingKey 与 funcEntry 映射失》补充：Host SetTilingKey(N) 后运行时按 funcEntry=tilingKey 查找内核入口，若 kernel 二进制未通过 ASCENDC_TPL_SEL 在对应 SEL 位置注册该 funcEntry，则 BinaryGetFunctionByEntry 失败并报 361001。给出 funcEntry=SEL 位置=tilingKey 的判别与 SEL 占位修复。
- [sub-kernel 后缀 _N 是 tilingKey 位编码非序号](sub_kernel_n_tilingkey.md)（`same_topic`）：tilingKey 编码与 TPL 位打包不一致致路由错误：这些卡沿同一 TPL 路由链闭合：GET_TPL_TILING_KEY按位编码，host funcEntry必须使用相同值，sub-kernel后缀展示实际编码，ASCENDC_TPL_SEL缺失或 isGroup哨兵会在相邻环节产生同类错路由。 目标卡《sub-kernel 后缀 _N 是 tilingKey 位编码非序号》补充：编译产出的 .o 中 sub-kernel 后缀 _N 是 FastEncodeTilingKeyDirect 的位编码 tilingKey（T|E<<1|R<<2），非连续序号；_3 空位是设计性 gap，[0,4,2,1,5] 是 TPL_SEL 展开顺序副产物。
- [缺 ASCENDC_TPL_SEL 致运行时分发静默 no-op 跳过](ascendc_tpl_sel_no_op.md)（`same_topic`）：tilingKey 编码与 TPL 位打包不一致致路由错误：这些卡沿同一 TPL 路由链闭合：GET_TPL_TILING_KEY按位编码，host funcEntry必须使用相同值，sub-kernel后缀展示实际编码，ASCENDC_TPL_SEL缺失或 isGroup哨兵会在相邻环节产生同类错路由。 目标卡《缺 ASCENDC_TPL_SEL 致运行时分发静默 no-op 跳过》补充：euclidean_norm kernel 入口用非模板 extern C + 运行时 if/else + PipeBarrier fall-through 兜底，偏离 proto.md §3 / DESIGN §5.6.1 的 ASCENDC_TPL_SEL 编译期分发；未命中分支静默 no-op，Group+tail-A special-value 用例被 harness 以 SKIP (no golden) 跳过而非报错。
<!-- cannbot:related:end -->
