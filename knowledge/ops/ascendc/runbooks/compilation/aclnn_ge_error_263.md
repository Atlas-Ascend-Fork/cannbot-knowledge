---
type: "Runbook"
title: "aclnn 全绿但 GE 图模式 error 263 分层判别"
description: "aclnn 预编译 ST 全绿但 GE 图模式 TBE 动态编译 RunGraph 触发 AI Core error 263(aivec) 时，用 plog/kernel-JSON/空张量探针区分「tiling 未传递误判」「tiling 大小未注册」「kernel 向量指令执行期崩」三类原因；arg5=0 不代表 tiling 未传递（sysParam 单独传递），空张量 RunGraph 成功即排除图基础设施。"
tags: ["task.debugging", "topic.tiling", "topic.implementation.masking"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# aclnn 全绿但 GE 图模式 error 263 分层判别

## 适用场景

- 工程形态：kernel 直调 + aclnn 预编译 ST + GE 图模式 TBE 动态编译 `session.RunGraph`（route_probe / test_geir）。
- API 路径：`session.RunGraph` + TBE 动态编译（`te_<op>_<hash>` kernel cache）+ plog（`/root/ascend/log/debug/plog/`、`/root/ascend/log/run/plog/`）。
- 验证过的平台与 CANN 版本：Ascend950（`Ascend950PR_9579` kernel_cache），CANN 9.1.0。
- 适用粒度：operator_family（所有须跑 GE 图模式的 regbase arch32 算子）。
- 路线优先级：recommended_fastpath（判别流程本身；各探针指向的具体修复路线见对应根因卡）。
- 不适用或未验证场景：aclnn 预编译路径自身的 error 263（不涉及 TBE 动态编译）；非 regbase 架构。

## 判别方法

触发（tool_observed）：在 Ascend950 上为 masked-select 类算子跑 GE 图模式 route_probe（最小 GE 图：x 与 value float32、mask bool、输出 UNKNOWN_RANK，单次 `session.RunGraph`），`RunGraph` 退出码非 0、plog 记 `aivec error exception, error code = 263, 82`（errorStr 指地址未对齐或越界；`vec error info: 0x...`、`mte error: 0x40000`）；同算子 aclnn 预编译 ST 全绿，同环境 AddCustom GE 图模式全绿。

探针（executable check）：按下述顺序执行，原始观测决定归因。

探针 1 — tiling 函数是否被调用：

```bash
grep -iE "Op tiling succeed|TilingFunc|optiling" /root/ascend/log/run/plog/plog-*.log | grep -i <op>
```

探针 2 — tiling 数据大小是否正确注册（读 TBE kernel JSON）：

```bash
find /root/atc_data/kernel_cache/Ascend950PR_9579/te_<op>_* -name '*.json'
# 核对 opParaSize 是否等于 sizeof(<TilingData>)
```

探针 3 — arg5=0 是否等于 tiling 未传递（关键误诊点）：

```bash
grep -iE "args\(0 to|GetArgsInfo|argsSize|logical_addrs" /root/ascend/log/debug/plog/plog-*.log | tail
```

探针 4 — 空张量 RunGraph 探针（区分图基础设施 vs kernel 向量执行）：

```cpp
// 空张量：kernel 对空输入为 no-op，不触发向量 Select
std::vector<T> x{};   // shape [0,4]
```

探针 5 — kernel 是否用了自定义 VF / Reg:: 内联：

```bash
grep -rn "__simd_vf__\|asc_vf_call\|Reg::\|MicroAPI" op_kernel/
```

观测（tool_observed）：

- 探针 1：route.log 含 `Op tiling succeed. op_type:<op>` 与 `logical_addrs size:<M>`（M=用户参数数，不含 tiling/sys）→ tiling 函数被调用且成功，排除「tiling 未注册/未调用」。
- 探针 2：补 `REGISTER_TILING_DEFAULT(<TilingData>)` 后 TBE kernel JSON `opParaSize` 由 392 变为 680（= `sizeof(<TilingData>)`），tiling 大小注册生效；但 `opParaSize` 正确后崩溃依旧。注意 `REGISTER_NONE_TILING` 是空宏，不注册 tiling struct 大小。
- 探针 3：`args(0 to N) after execute: ..., 0` 末位为 0。tiling 在 GE 图模式作为 sysParam 单独传递，不计入 `parameters` 字段、也不在「after execute」读数中保留指针——arg5=0 不代表 tiling 未传递。本 trace 据 arg5=0 推断 tiling 未传递、追加 `REGISTER_TILING_DEFAULT` 与改非模板 `extern "C"` 入口均未解决崩溃。
- 探针 4：空张量（shape [0,4]）`RunGraph` 返回 status=0、输出 shape=[0,4]、dtype=DT_FLOAT（InferShape V1 广播与公共 dtype 规则均正确）；所有非空张量（任意 dtype/shape）`RunGraph` 均崩 error 263 → 图基础设施（InferShape/InferDataType/tiling/编译）全部正常，崩溃只在 kernel 向量指令对非空张量执行时触发。
- 探针 5：源码 grep `__simd_vf__`/`asc_vf_call` 仅余注释（实现代码已移除）；改普通 `AscendC::CompareScalar`+`Select`（`basic_api/interface/`，非 VF）后 aclnn 仍全绿、GE 图模式非空张量仍崩 error 263。

判别与解释（interpretation，agent 根因分析，非 API 规范主张）：探针 1+2 过 → tiling 链路正常；探针 4 空张量过、非空崩 → 图基础设施正常、崩溃在 kernel 向量执行；探针 5 命中 VF → 先按自定义 VF 在 TBE 动态编译下被禁的失败路线修复；改普通 API 后 aclnn 仍绿但 GE 仍崩 → 根因不在 VF/API 选型，在 TBE 生成 binary 的向量指令执行期（本 trace 终态，未追到机制层）。arg5=0 是 GE 框架在 kernel 执行后清理 tiling 指针读数所致，非 tiling 未传递；该机制由观测归纳，未在文档中找到显式说明。

## 验证信号

来源：本 trace 在 Ascend950（CANN 9.1.0）上对 masked-select 类算子做 route_probe RunGraph + plog/ kernel JSON / 空张量探针，配套 aclnn 预编译 ST 与 AddCustom GE 图模式 baseline。

- 探针 1：route.log 含 `Op tiling succeed. op_type:MaskedFill` 与 `logical_addrs size:5`（tiling 函数被调用且成功，sysParam 单独传递）。（来源平台：950；证据等级：tool_observed）
- 探针 2：补 `REGISTER_TILING_DEFAULT(TilingData8)` 后 TBE kernel JSON `opParaSize` 由 392 变为 680（= `sizeof(TilingData8)`），tiling 大小注册生效但崩溃未解。（来源平台：950；证据等级：tool_observed）
- 探针 4：空张量（shape [0,4]）RunGraph 返回 status=0、输出 shape=[0,4]、dtype=DT_FLOAT；所有非空张量（任意 dtype/shape）RunGraph 均崩 error 263。（来源平台：950；证据等级：tool_observed）
- 探针 5：源码 grep `__simd_vf__`/`asc_vf_call` 仅余注释（实现代码已移除）；改普通 `AscendC::CompareScalar`+`Select` 后 aclnn 148/148 全绿、GE 图模式非空张量仍崩 error 263。（来源平台：950；证据等级：tool_observed）

## 失效边界

- 判别流程在 Ascend950 regbase arch32 + CANN 9.1.0 上实测；其他架构/版本未验证，推断可迁移（探针命令不依赖架构特有路径，但 `Ascend950PR_9579` kernel_cache 路径需按目标平台替换）。
- 探针 3「arg5=0 ≠ tiling 未传递」的判读基于 GE 图模式 sysParam 传递机制；aclnn 路径的 tiling 由 `aclnnSetTilingData` 传递，不在本判别范围。
- 本卡只诊断到「崩溃在 kernel 向量指令执行期、非图基础设施、非 tiling 链路」这一层；普通 `AscendC::CompareScalar`+`Select` 在 TBE 动态编译下对非空张量崩溃的真实机制层根因未追到。

<!-- cannbot:related:start -->
## 相关

- [AscGe](../../apis/simd_api/c_api/vector_compute/asc_ge.md)（`exemplifies`）：《aclnn 全绿但 GE 图模式 error 263 分层判别》给出“aclnn 预编译 ST 全绿但 GE 图模式 TBE 动态编译 RunGraph 触发 AI Core error 263(aivec) 时，用 plog/kernel-JSON/空张量探针区分「tiling 未传递误判」「tiling 大小未注册」「kernel 向量指令执行期崩」三类原因；arg5=0 不代表 tiling 未传递（sysParam 单独传递），空张量 RunGraph 成功即排除图基础设施。”；该约束/探针可直接复现、解释或前置验证《AscGe》中的“Ge（greater than or equal to），逐元素比较src0 >= src1是否成立，成立则输出结果为1，否则输出结果为0，每个元素的比较结果占一个bit。”。
- [ACLNN 361001 — tilingKey 与 funcEntry 映射失](aclnn_361001_tilingkey_funcentry_sel_position.md)（`related`）：当图模式选择了不存在的 kernel 变体时，tilingKey 与 funcEntry 映射错位会表现为 361001；目标卡提供映射位置校验法，补足总卡的第三条分支。
- [Cube 直调 retCode=0x26：AIV 误跑 Cube API 越界](cube_retcode_0x26_aiv_cube_api.md)（`related`）：《Cube 直调 retCode=0x26：AIV 误跑 Cube API 越界》说明Cube 核直调 kernel 入口 extern "C" __global__ __aicore__ 未标记核类型时 bisheng 按 MIX 模式编译，kernel 被派发到 AIV 核执行 Cube 专属 API（LoadData/Mmad/Fixpipe），AIV 核无 L0A/L0B/L0C 硬件单元，访问 AIC 内部 buffer 越界，触发 aicore exception retCode=0x26 / ErrCode=507015，plog 表现为 aivector error 而非 Cube 侧错误。判别要点：代码用 Cube API、报错却是 aivector error + fixp_error 非零 + scalar access internal buffer of AICore is out of bounds。；《aclnn 全绿但 GE 图模式 error 263 分层判别》说明aclnn 预编译 ST 全绿但 GE 图模式 TBE 动态编译 RunGraph 触发 AI Core error 263(aivec) 时，用 plog/kernel-JSON/空张量探针区分「tiling 未传递误判」「tiling 大小未注册」「kernel 向量指令执行期崩」三类原因；arg5=0 不代表 tiling 未传递（sysParam 单独传递），空张量 RunGraph 成功即排除图基础设施。。二者在报错的判别核心是未标核类型导致AIV执行LoadData/Mmad等Cube专属指令，需从kernel type和Cube调用两端验证上存在可执行的直接衔接。
- [GE图模式263: 自定义VF Select被禁](ge_263_vf_select.md)（`related`）：总诊断卡的 GE-only error 263 分支之一就是自定义 VF Select 在图模式被禁止；目标卡提供对应日志签名和替换动作。
- [__simd_vf__ if constexpr 致 hoisted 报错](simd_vf_if_constexpr_lowering_banned_exit_70.md)（`related`）：《__simd_vf__ if constexpr 致 hoisted 报错》说明dav-3510 上某 Reg __simd_vf__ 实现使用 if constexpr 与 constexpr trait 时，bisheng 后端报 Unsupported Inst must be hoisted 并退出 70；记录源码定位与编译边界，不提供未完成的 fallback 实现。；《aclnn 全绿但 GE 图模式 error 263 分层判别》说明aclnn 预编译 ST 全绿但 GE 图模式 TBE 动态编译 RunGraph 触发 AI Core error 263(aivec) 时，用 plog/kernel-JSON/空张量探针区分「tiling 未传递误判」「tiling 大小未注册」「kernel 向量指令执行期崩」三类原因；arg5=0 不代表 tiling 未传递（sysParam 单独传递），空张量 RunGraph 成功即排除图基础设施。。二者在该编译失败锁定__simd_vf__中的if constexpr/trait lowering，同类模板隔离、helper/VF边界与后端崩溃用于交叉验证上存在可执行的直接衔接。
- [te_fusion 未调 TilingPrepare 致 GEIR FPE](te_fusion_tilingprepare_geir_fpe.md)（`related`）：总诊断卡把 GEIR FPE 归到 TilingPrepare 缺失分支；目标卡给出 te_fusion 调用链和补 TilingPrepare 的闭环修复。
<!-- cannbot:related:end -->
