---
type: Guide
title: 高阶 Matmul API 全链路骨架（host tiling 到 device 迭代）
description: Matmul 高阶 API 的完整组装链：host 侧 PlatformAscendCManager 取平台、MatmulApiTiling 逐项配置后生成 tiling；device 侧 TPipe 与 REGIST_MATMUL_OBJ 注册对象、SetTensorA/B/SetBias/SetTail 后 IterateAll 完成整矩阵迭代，含 MatmulConfig 自定义变体入口。
tags:
- task.implementation
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/04_advanced_api/00_matmul/matmul_format_gemv/matmul_format_gemv.asc
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/04_advanced_api/00_matmul/matmul_mixdualmaster/matmul_mixdualmaster.asc
  role: supporting
- resource: cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/weight_quant_batch_matmul_v2/op_host/op_tiling/weight_quant_batch_matmul_v2_tiling_custom.cpp
  role: supporting
created_at: '2026-10-10T06:41:29Z'
updated_at: '2026-10-10T09:52:36Z'
platforms:
- '950'
- a2
- a3
---

# 高阶 Matmul API 全链路骨架（host tiling 到 device 迭代）

## 适用场景

用高阶 Matmul API（`AscendC::Matmul` 模板）实现整矩阵乘：host 侧一次 tiling 计算，device 侧 `IterateAll` 自动迭代；GEMV/对齐/非对齐/带 bias 等形态共用同一骨架，差异集中在 tiling 侧 `SetXxxType` 配置与 `MatmulConfig` 模板参数。

## 链路骨架

**Host 侧（tiling 计算）**：

```cpp
constexpr bool IS_BIAS = true;           // Host/Device 共享同一 bias 开关
auto ascendcPlatform = platform_ascendc::PlatformAscendCManager::GetInstance("Ascend910B1");
matmul_tiling::MatmulApiTiling tilingApi(*ascendcPlatform->GetPlatformInfo());
tilingApi.SetDim(ascendcPlatform->GetCoreNumAic());          // 核数联动
tilingApi.SetAType(TPosition::GM, CubeFormat::ND, DataType::DT_FLOAT, false);
tilingApi.SetBType(TPosition::GM, CubeFormat::ND, DataType::DT_FLOAT, false);
tilingApi.SetCType(TPosition::GM, CubeFormat::ND, DataType::DT_FLOAT);
tilingApi.SetBiasType(TPosition::GM, CubeFormat::ND, DataType::DT_FLOAT);  // 含 CubeFormat
tilingApi.EnableBias(IS_BIAS);           // 显式开启 bias，缺失会按无 bias 计算 tiling
tilingApi.SetOrgShape(M, N, K);          // 原始形状（决定尾块切分）
tilingApi.SetShape(M, N, K);
tilingApi.SetBufferSpace(-1, -1, -1);    // L1/L0C/UB 预算（-1 用满额）
int64_t res = tilingApi.GetTiling(tilingData);   // 生成 tiling
if (res == -1) { return ge::GRAPH_FAILED; }      // tiling 失败不得交给 kernel
```

**Device 侧（注册与迭代）**：

```cpp
AscendC::TPipe pipe;
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), matmulKernel.matmulObj, &tiling);  // 注册三要素
// Init: SetGlobalBuffer 绑 A/B/C/bias；GetSysWorkSpacePtr() 非空是注册前置
// Process:
if (tailM > 0 || tailN > 0) { matmulObj.SetTail(tailM, tailN); }   // 尾块
matmulObj.SetTensorA(aGlobal, IS_TRANS_A);
matmulObj.SetTensorB(bGlobal, IS_TRANS_B);
if (IS_BIAS) { matmulObj.SetBias(biasGlobal); }   // 与 Host 的 EnableBias 同一开关
matmulObj.IterateAll(cGlobal);       // 整矩阵自动迭代
```

## 成员职责

| 环节 | API |
|---|---|
| 平台 | [PlatformAscendCManager](../../apis/utils_api/platform_info/platform_ascend_c_manager.md)、[GetCoreNumAic](../../apis/utils_api/platform_info/platform_ascend_c/get_core_num_aic.md)、[GetLibApiWorkSpaceSize](../../apis/utils_api/platform_info/platform_ascend_c/get_lib_api_work_space_size.md) |
| tiling 配置 | [MatmulTiling 构造](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/matmul_tiling_usage.md)、[SetDim](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_dim.md)、[SetAType](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_a_type.md)/[SetBType](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_b_type.md)/[SetCType](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_c_type.md)、[SetBiasType](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_bias_type.md)、[SetOrgShape](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_org_shape.md)、[SetBufferSpace](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_buffer_space.md)、[GetTiling](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/get_tiling.md) |
| 注册 | [REGIST_MATMUL_OBJ](../../apis/simd_api/adv_api/cube_compute/matmul_kernel/regist_matmul_obj.md)、[TPipe](../../apis/simd_api/basic_api/resource_management/t_pipe/t_pipe_intro.md)、[GetSysWorkSpacePtr](../../apis/simd_api/basic_api/resource_management/workspace/get_sys_work_space_ptr.md) |
| 迭代 | [SetTensorA](../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_tensor_a.md)/[SetTensorB](../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_tensor_b.md)、[SetBias](../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_bias.md)、[SetTail](../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_tail.md)、[IterateAll](../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate_all.md) |

## 跨 API 联动约束

1. **跨侧位置契约**：host 侧 `SetAType/SetBType/SetCType/SetBiasType` 声明的 `TPosition`（GM/VECIN/VECOUT/TSCM）必须与 kernel 侧实际张量来源一致——SetTensorA 卡明示 LocalTensor 重载仅支持 TSCM/VECOUT 位置。
2. **注册三要素成对**：`REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), obj, &tiling)` 首参数即 pipe 指针、第二参数为系统 workspace 指针，两者与 tiling 结构缺一不可；`GetSysWorkSpacePtr()` 为空需在 Init 阶段判定失败。
3. **核数-切分联动**：`SetDim(GetCoreNumAic())` 把 AIC 核数喂给切分；workspace 预算经 `GetLibApiWorkSpaceSize` 校验。
4. **OrgShape 与尾块**：host 侧 `tilingApi.SetOrgShape` 是 MatmulTiling 接口，提供原始形状；device 侧 `SetTail` 按其与 base 块差值设置尾块。同名的 kernel `Matmul::SetOrgShape` 用于运行时改 shape，不是这条 host tiling 调用。缺 tiling 侧 OrgShape 时尾块切分错误。
5. **预算约束链**：`SetBufferSpace(l1, l0c, ub)` 声明的预算约束 tiling 可选分块，分块决定 kernel 侧操作数布局——预算、分块、布局三层必须自洽（契约详见[经典 Cube 搬运流水](classic_cube_pipeline_two_forms.md)中的 TileShape 段）。

## MatmulConfig 自定义变体

默认 `CFG_NORM` 之外，`GetCustomMDLCFG/GetCustomCFG/GetCustomNORMCFG` 以 `constexpr MatmulConfig` 注入 `Matmul` 模板，可开启 MDL 双缓冲、UnitFlag 等特性；host tiling 与 device 注册流程不变。

## 失效边界与常见错误

- **AsyncGetTensorC 已废弃**：全官方样例零调用，卡片明示由 [GetTensorC](../../apis/simd_api/adv_api/cube_compute/matmul_kernel/get_tensor_c.md) 取代，新代码不要采用；
- host/kernel 两侧 TPosition 或 CubeFormat 不一致：IterateAll 结果错位或编译期报错；
- 漏判 `GetSysWorkSpacePtr() == nullptr`：注册失败在运行期才暴露；
- 逐 tile 手动控制（非 IterateAll）时改用 [Iterate](../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate.md)+[GetTensorC] 流水形态，参见[异步 Matmul 结果空间](async_result_buffers_and_completion.md)。

## 验证方式

- tiling 侧：`GetTiling` 返回值非负、tilingData 字段完整性；
- device 侧：单 tile 对拍 + 尾块对拍（M/N 不整除 base 时）；
- 配置对拍：bias 开关、transpose 标志与 A/B 实际布局一致。
