---
type: "Runbook"
title: "L1/L0 tensor 须用 TPosition 构造非 SetAddr"
description: "CANN 9.2.0 arch35 上 TBuf 无 SetAddr、LocalTensor<T>(addr) 触 tPos trait 错；L1/L0A/L0B/L0C 须用 LocalTensor<T>(TPosition, addr, size) 构造。"
tags: ["task.debugging", "topic.implementation.api_layer.basic_api", "topic.implementation.memory_management"]
status: stable
sources: []
created_at: "2026-08-18T05:28:23Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# L1/L0 tensor 须用 TPosition 构造非 SetAddr

## 现象

在 CANN 9.2.0 + Ascend950PR（arch3510）上，去掉第三方 `tensor_api` 后用 CANN 原生 `LoadData`/`Mmad`/`Fixpipe` 重写 `SimpleBlockMmad`。最初仿照旧写法用 `TBuf<TPosition::VECCALC>::SetAddr(...)` 手动给 L0C buffer 设地址、用 `LocalTensor<T>(uint32_t addr)` 直接以裸地址构造 L1/L0A/L0B/L0C tensor。编译报 `error: no member named 'SetAddr' in 'AscendC::TBuf<AscendC::TPosition::VECCALC>'`（8 errors generated）以及 `LocalTensor<float>(uint32_t addr)` 触发 `BaseTensorTraitTensor<T>` 的 `tPos` trait 检查失败（裸类型 `float`/`__bf16` 无 `tPos`）。即：CANN 9.2.0 arch35 上不能通过 `TBuf::SetAddr` 或裸地址 `LocalTensor` 构造来手动管理 L1/L0A/L0B/L0C 的固定硬件地址。

## 适用场景

- **工程形态**：kernel 直调，device 侧手写 cube 数据搬运（GM→L1→L0A/L0B→Mmad→L0C→Fixpipe→GM），不经 `MatmulImpl` 高级封装。
- **API 路径**：CANN 原生 `TBuf<TPosition::A1/A2/B2/CO1>`、`LocalTensor<T>(TPosition, addr, size)`、`LoadData`/`Mmad`/`Fixpipe`（`basic_api/kernel_operator_*`）。
- **验证过的平台与 CANN 版本**：Ascend950PR（arch3510，simulator），CANN 9.2.0。
- **适用粒度**：`platform_wide`（CANN 9.2.0 arch35 上任何手写 cube 搬运 kernel 都适用）。
- **路线优先级**：`recommended_fastpath` —— 用 `LocalTensor<T>(TPosition, addr, size)` 构造 L1/L0 tensor 是该环境手写 cube 搬运的正确入口。
- **不适用或未验证场景**：`MatmulImpl` 高级 API 路线不涉及（其内部自管 L1/L0）；A2/A3（DAV_2201）上 TPosition 枚举值与构造签名可能不同，未验证。

## 根因

CANN 9.2.0 的 `TBuf<TPosition>` 不暴露 `SetAddr`（L1/L0 的固定硬件地址不由用户在 `TBuf` 上手动 set）；`LocalTensor<T>(uint32_t addr)` 这个"裸地址构造"路径会走 `BaseTensorTraitTensor<T>` 的 trait 检查，要求 `T` 有 `tPos` 成员——但裸 `float`/`__bf16` 不是 `TensorTrait` 类型，故编译失败。L1/L0A/L0B/L0C 的正确构造方式是带 `TPosition` 的构造函数 `LocalTensor<T>(TPosition pos, uint32_t addr, uint32_t tileSize)`，由 `TPosition`（`A1`=L1A、`A2`=L0A、`B2`=L0B、`CO1`=L0C）承担位置语义，裸类型无需具备 trait。

## 判别方法

本规则按"触发 → 探针 → 观测 → 判别"四段组织；触发与观测均为 trace 中 tool_observed 的编译输出。

1. **触发（tool_observed 编译错）**：编译报 `error: no member named 'SetAddr' in 'AscendC::TBuf<AscendC::TPosition::VECCALC>'` 指向 `buf.SetAddr(...)` 行；或 `LocalTensor<T>(addr)` 触发 `tPos`/`BaseTensorTraitTensor` 缺成员。即命中本规则。原始报错（verbatim）：

```
/home/w00955510/MC2/Sources/01.04/matmul_all_gather/include/block/simple_block_mmad.h:254:13: error: no member named 'SetAddr' in 'AscendC::TBuf<AscendC::TPosition::VECCALC>'
        buf.SetAddr(__cc__ T*, pingPong * HALF_L0C * sizeof(T));
        ~~~ ^
/home/w00955510/MC2/Sources/01.04/matmul_all_gather/include/block/simple_block_mmad.h:254:21: error: expected expression
        buf.SetAddr(__cc__ T*, pingPong * HALF_L0C * sizeof(T));
                    ^
/home/w00955510/Ascend/cann-9.2.0/tools/bisheng_compiler/lib/clang/15.0.5/include/__clang_cce_defines.h:65:16: note: expanded from macro '__cc__'
#define __cc__ __attribute__((cce_cube_c))
               ^
8 errors generated.
```

2. **探针（可执行检查）**：在 CANN 安装的 arch35 示例/头文件中检索 `TBuf<TPosition::` 与 `LocalTensor<` 的构造用法；可用 `grep -rn "TPosition::" $ASCEND_HOME/.../ascendc/.../arch35/` 确认官方写法。亦可在 `kernel_tensor.h`/`kernel_tensor_base.h` 中确认 `TBuf` 是否有 `SetAddr` 成员、`LocalTensor<T>(uint32_t)` 构造是否走 `BaseTensorTraitTensor` 的 `tPos` 检查。

3. **观测（tool_observed 官方示例）**：arch35 CANN 自带示例用 `TBuf<TPosition::A1> l1TBuf_;` 管理 L1A、`Fixpipe(cGlobal_[...], l0c_, params);` 写 GM；用 `LocalTensor<T>(TPosition::A2, addr, size)` 构造 L0A、`LocalTensor<T>(TPosition::B2, addr, size)` 构造 L0B、`LocalTensor<float>(TPosition::CO1, 0, size)` 构造 L0C。`TPosition` 枚举：`A1`（L1A）、`B1`（L1B）、`A2`（L0A）、`B2`（L0B）、`CO1`（L0C）、`CO2`（L0C output）等。

4. **判别（interpretation）**：若触发报错命中 `SetAddr`/`tPos`/`BaseTensorTraitTensor`，根因是 CANN 9.2.0 arch35 的 `TBuf<TPosition>` 不暴露 `SetAddr`、裸类型无 `tPos` trait，**正确修复方向是换构造函数签名**——把 L1/L0A/L0B/L0C 的构造改为 `LocalTensor<T>(TPosition, addr, size)` 或用 `TBuf<TPosition::...>` + `TPipe::InitBuffer` 管理，而不是给 `TBuf` 补 `SetAddr` 或给裸类型补 `TensorTrait`。

## 预防

- 从第三方 `tensor_api`（`MakeL1memPtr` 等）迁移到 CANN 原生 API 时，不要沿用"手动 set 地址"思路；L1/L0A/L0B/L0C 一律用 `LocalTensor<T>(TPosition, addr, size)` 构造，或用 `TBuf<TPosition::...>` + `TPipe::InitBuffer` 管理。
- 出现 `no member named 'SetAddr' in 'TBuf'` 或 `tPos` trait 报错，立刻改 `TPosition` 构造，不要再在 `TBuf`/trait 层找变通。

## 验证信号

- 编译报 `error: no member named 'SetAddr' in 'AscendC::TBuf<AscendC::TPosition::VECCALC>'` 于 `buf.SetAddr(__cc__ T*, pingPong * HALF_L0C * sizeof(T));`，`8 errors generated.`（来源平台:950；证据等级:tool_observed）。
- arch35 CANN 示例用 `TBuf<TPosition::A1> l1TBuf_;` 与 `Fixpipe(cGlobal_[fixedOffsetC + mloop * params.dstStride * M0 + nloop * N0], l0c_, params);`（来源平台:950；证据等级:tool_observed）。

## 失效边界

- **recommended_fastpath**：CANN 9.2.0 arch35（950PR）上手写 cube 搬运，L1/L0A/L0B/L0C 用 `LocalTensor<T>(TPosition, addr, size)` 构造。
- 推断可迁移（未验证）：A2/A3（DAV_2201）的同版本 CANN 头中可能保留相同 TPosition 枚举名，但采用前必须以目标 toolkit 头文件为准。
- `TPosition` 枚举值与构造签名在不同 CANN 版本/架构可能差异，跨版本迁移前先 `grep` 该 CANN 安装的 `TPosition` 定义与 `LocalTensor` 构造函数。

## 坏实践

- 试图给 `TBuf` 加 `SetAddr`、或为裸 `float`/`__bf16` 补 `TensorTrait`/`tPos` 以走 `LocalTensor<T>(addr)` 构造：正确做法是换构造函数签名，不是改类型 trait。

## 误诊

- 诊断早期一度以为 `LocalTensor<T>(uint32_t addr)` 是公开构造可用、又怀疑需 `TensorTrait` 特化；经读 `kernel_tensor.h`/`kernel_tensor_base.h` 后确认应改用带 `TPosition` 的构造函数（来源平台:950；证据等级:agent_reported）。

## 性能影响

未观测。

<!-- cannbot:related:start -->
## 相关

- [GetPosition](../../apis/simd_api/basic_api/data_structures/local_tensor/get_position.md)（`exemplifies`）：《GetPosition》处理“获取LocalTensor所在的TPosition逻辑位置，支持TPosition为VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2。”。《L1/L0 tensor 须用 TPosition 构造非 SetAddr》明确提供“CANN 9.2.0 arch35 上 TBuf 无 SetAddr、LocalTensor<T>(addr) 触 tPos trait 错；L1/L0A/L0B/L0C 须用 LocalTensor<T>(TPosition, addr, size) 构造。”，其参数、调用或验证步骤直接接入GetPosition 所读取的 LocalTensor 位置、构造来源和 TPosition 故障定位。
- [L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍](../../apis/simd_api/basic_api/cube_compute/cube_compute_load/l1_l0_a_b_memory_structure_intro.md)（`exemplifies`）：The runbook shows that L1/L0 tensors must encode their position in LocalTensor construction rather than attaching an address with SetAddr.
- [LoadData](../../apis/simd_api/basic_api/cube_compute/cube_compute_load/load_data_3_d.md)（`exemplifies`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《L1/L0 tensor 须用 TPosition 构造非 SetAddr》具体提供“CANN 9.2.0 arch35 上 TBuf 无 SetAddr、LocalTensor<T>(addr) 触 tPos trait 错；L1/L0A/L0B/L0C 须用 LocalTensor<T>(TPosition, addr, size) 构造。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [LoadData](../../apis/simd_api/basic_api/cube_compute/cube_compute_load/load_data_gm_to_l1_2_dv2.md)（`exemplifies`）：《LoadData》处理“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”。《L1/L0 tensor 须用 TPosition 构造非 SetAddr》明确提供“CANN 9.2.0 arch35 上 TBuf 无 SetAddr、LocalTensor<T>(addr) 触 tPos trait 错；L1/L0A/L0B/L0C 须用 LocalTensor<T>(TPosition, addr, size) 构造。”，其参数、调用或验证步骤直接接入GM 到 L1 二维 LoadData 的 Fmatrix、repeat、边界和地址合同。
- [LocalTensor构造函数](../../apis/simd_api/basic_api/data_structures/local_tensor/local_tensor_constructor.md)（`exemplifies`）：《LocalTensor构造函数》处理“LocalTensor构造函数。”。《L1/L0 tensor 须用 TPosition 构造非 SetAddr》明确“CANN 9.2.0 arch35 上 TBuf 无 SetAddr、LocalTensor<T>(addr) 触 tPos trait 错；L1/L0A/L0B/L0C 须用 LocalTensor<T>(TPosition, addr, size) 构造。”，可直接用于核对LocalTensor 的默认/静态地址构造、LocalMemAllocator 构造路径及错误实参诊断。
- [SetAddrWithOffset](../../apis/simd_api/basic_api/data_structures/local_tensor/set_addr_with_offset.md)（`exemplifies`）：SetAddrWithOffset 与《L1/L0 tensor 须用 TPosition 构造非 SetAddr》的实质衔接是：SetAddrWithOffset 与子视图/偏移接口共享元素偏移契约，所选故障卡直接说明错误基址叠加、L1/L0 限制及 DataCopy 偏移修复。
- [TPosition](../../apis/simd_api/basic_api/aux_data_structures/t_position.md)（`exemplifies`）：焦点处理TPosition 在 Tensor 和队列中的片上位置类型约束；L1/L0 tensor 须用 TPosition 构造非 SetAddr正文界定“CANN 9.2.0 arch35 上 TBuf 无 SetAddr、LocalTensor<T>(addr) 触 tPos trait 错；L1/L0A/L0B/L0C 须用 LocalTensor<T>(TPosition, addr,”。候选直接读取/构造 TPosition 或复现 TPosition 枚举和 L1/L0 Tensor 构造错误。
- [TBuf 不能直接传给 LocalTensor 形参](tbuf_gets_typed_localtensor_before_helper_call.md)（`related`）：该卡区分 TBuf 管理对象与 LocalTensor 可寻址视图，补充另一类因对象层级错误导致的 LocalTensor 编译失败，可避免把 TBuf 当作 SetAddr/裸地址替代。
- [TQue 位置参数须用 AscendC::TPosition 枚举](tque_ascendc_tposition.md)（`same_topic`）：TQue 位置参数须用 AscendC::TPosition 枚举 与《L1/L0 tensor 须用 TPosition 构造非 SetAddr》的实质衔接是：TPosition定义了TQue/LocalTensor位置枚举；L1/L0 构造案例和 GetPosition 分别给出相同位置契约的创建与读取方式。
<!-- cannbot:related:end -->
