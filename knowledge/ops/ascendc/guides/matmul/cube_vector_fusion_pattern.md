---
type: Guide
title: Cube+Vector 融合范式：CrossCore 通信与激活衔接
description: __mix__ 混合核编程范式：AIC 侧跑 Cube 搬运流水（Nd2Nz→LoadData→Mmad→Fixpipe）产出 tile 后 CrossCoreSetFlag 通知，AIV 侧 CrossCoreWaitFlag 等待后经 DataCopyPad 做 GM↔UB 激活计算；Cube:Vector 核数比 1:2 决定 GetBlockIdx 的映射关系。
tags:
- task.implementation
- topic.implementation.memory_management
- topic.implementation.synchronization
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/00_introduction/03_fusion_operation/matmul_leakyrelu_basic_api/matmul_leakyrelu_basic_api.asc
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/01_utilities/08_simulator/simulator.asc
  role: supporting
- resource: cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/all_gather_matmul_v2/op_kernel/all_gather_matmul_aiv_mode.h
  role: supporting
created_at: '2026-10-10T06:41:29Z'
updated_at: '2026-10-10T09:52:36Z'
platforms:
- '950'
---

# Cube+Vector 融合范式：CrossCore 通信与激活衔接

## 适用场景

`__mix__(1,2)` 混合核算子：Cube 核产出矩阵乘 tile、Vector 核接力激活/量化/归约（LeakyRelu/Gelu/Softmax 类）。SDK 原型为 matmul_leakyrelu，生产实例为 flash attention 系列（AIC 算 QK^T、AIV 做 softmax/加权）。

## 链路骨架

```cpp
// __global__ __mix__(1, 2) 入口只做 InitSocState，再进入类的 Process。
// AIC / AIV 用 ASCEND_IS_AIC、ASCEND_IS_AIV 在编译期分开，不用 GetBlockIdx 区分角色。
if ASCEND_IS_AIC {
    // Cube 流水：DataCopy(Nd2Nz) → MTE2_MTE1 → LoadData → MTE1_M → Mmad → M_FIX → Fixpipe
    AscendC::CrossCoreSetFlag<0x2, PIPE_FIX>(0);   // 样例：Fixpipe 完成后按 mode 2 通知
}
if ASCEND_IS_AIV {
    AscendC::CrossCoreWaitFlag(0);
    // 输出块起始：GetBlockIdx() / 2 映射回对应 Cube；半块：GetBlockIdx() % 2
    uint32_t gmOffset = mIndex * baseM * N + nIndex * baseN
        + AscendC::GetBlockIdx() % 2 * (baseM / 2 * N);
    AscendC::DataCopyPad<half>(vecLocal, cGM[gmOffset], extParams, padParams);
    AscendC::SetFlag<AscendC::HardEvent::MTE2_V>(EVENT_ID0);
    AscendC::WaitFlag<AscendC::HardEvent::MTE2_V>(EVENT_ID0);
    AscendC::LeakyRelu(vecLocal, vecLocal, (half)0.001, tileLen);
}
```

## 成员职责

| 侧 | API |
|---|---|
| AIC 流水 | 见[经典 Cube 搬运流水](classic_cube_pipeline_two_forms.md)全链 |
| 跨核同步 | [CrossCoreSetFlag](../../apis/simd_api/basic_api/sync_control/inter_core_sync/cross_core_set_flag_isasi.md)/[CrossCoreWaitFlag](../../apis/simd_api/basic_api/sync_control/inter_core_sync/cross_core_wait_flag_isasi.md) |
| AIV 搬运 | [DataCopyPad](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_pad_gm_to_ub.md)（GM→UB）/ [DataCopyPad UB→GM](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_pad_ub_to_gm.md) |
| 分核映射 | [GetBlockIdx](../../apis/simd_api/basic_api/tool_interface/system_resources_and_variables/get_block_idx.md)、[GetBlockNum](../../apis/simd_api/basic_api/tool_interface/system_resources_and_variables/get_block_num.md) |

## 跨 API 联动约束

1. **核比映射**：硬件 Cube:Vector = 1:2。AIV 用 `GetBlockIdx() / 2` 找到对应 Cube 的输出块，用 `GetBlockIdx() % 2` 取这块里自己负责的一半。`GetBlockIdx` 不表示 AIC 还是 AIV。
2. **CrossCore 的模板不是 HardEvent**：`CrossCoreSetFlag<modeId, pipe>(flagId)`，`CrossCoreWaitFlag` 的 mode 与 pipe 有默认值。样例在 Fixpipe 之后写 `CrossCoreSetFlag<0x2, PIPE_FIX>(0)`，AIV 侧 `CrossCoreWaitFlag(0)`。`0x2` 是 mode 2，`PIPE_FIX` 表示 FIX 流水完成后再通知。核内的 `SetFlag<HardEvent::M_FIX>` 只串本核 M 与 FIX，不能当成核间接口。
3. **AIC Fixpipe 目标即 AIV 读取源**：样例的 Fixpipe 在落 GM 时做 Nz→ND，并把 float 转成 half。AIV 的 DataCopyPad 按 ND 行距读取（`blockLen` 是 `baseN` 的字节数，`srcStride` 是行尾剩余字节），不是按 NZ 分块去读。
4. **非对齐激活走 DataCopyPad**：激活 tile 的 M/N 常不满足 32B 对齐，GM↔UB 用 DataCopyPad 而非 DataCopy；L2 缓存模式的方向特异枚举记录在 C API 卡 [asc_load/store_l2_cache_mode](../../apis/simd_api/c_api/defs/enum/asc_load_l2_cache_mode.md)（load 属 GM→UB、store 属 UB→GM，方向不可混用；该卡为 C API 形态，与本卡骨架的基础 API 调用分属不同 API 层级，枚举语义可参照）。

## 失效边界与常见错误

- 把核内 `HardEvent` 模板套到 `CrossCoreSetFlag` 上：接口对不上，也表达不了 mode 与 pipe；
- **mode 2 的两处证据需按版本/运行条件区分，不能互相推广**：
  - **官方接口定义**：mode 2 是「AI Core 内部，AIC 与**所有 AIV**之间的同步控制」——AIC 发 `CrossCoreSetFlag` 后，两个 AIV 上的 `CrossCoreWaitFlag` 才会继续；官方该接口的 modeId 支持表明确列出 `__mix__(1, 2)` 支持 mode 2（模式 0/1/2 下每核各 16 个 flagId）；本卡骨架沿用固定 SDK 示例的 mode 2 写法。
  - **特定实测差异**：[runbook](../../runbooks/precision/950_mix_1_2_mode_2_aiv1_flag.md) 在 Ascend 950DT / NpuArch DAV_3510 / **CANN 9.0.0** / bisheng `--soc=ascend950` 环境、特定 `__mix__(1,2)` 用例上观察到 AIV1 未收到 AIC 信号（输出缺失/全零），改用 mode 4 + AIC 侧对 AIV1 的 flagId 加 16（模式 4 在 950 上 AIC 有 32 个 flagId 的特性）后通过；该 runbook 同时注明 A2/A3 上 mode 2 行为不同。
  - **处置建议**：在目标版本/运行条件下实测确认；若复现既有失败形态，按 runbook 的具体环境与复现边界排查，不要据此得出「950 双 AIV 一律必须 mode 4」的通用结论；
- AIV 等待的 flagId 与 AIC 设置不一致：永久阻塞或读到半成品 tile；
- 忽略 1:2 核比直接按 1:1 映射：tile 一半无人处理；
- 用 DataCopy 搬非对齐激活：对齐约束触发编译/运行错误；
- 本卡为 AIC→AIV 单向生产-消费；双向流水（AIV 回写后 AIC 再读）需对称增加一组 CrossCore 事件；
- 混合核的 UB 用量受 AIC/AIV 共享上限约束（trouble_shooting 样例专题演示越界形态）。

## 验证方式

- 单 Cube 单 tile 对拍（M/N 取最小 base 块）→ 多 tile → 多核；
- flagId 一致性：故意错配观察 WaitFlag 挂起（防御性断言）；
- 激活数值对拍：LeakyRelu 输入含负数、tile 边界非对齐。
