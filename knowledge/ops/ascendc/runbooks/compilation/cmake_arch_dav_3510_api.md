---
type: "Runbook"
title: "CMake arch 子目录隔离 dav-3510 专属 API"
description: "xpu_ops v2 框架的 CMake 用 file(GLOB_RECURSE) 扫描算子根目录 .cpp（排除 arch_* 子目录）对所有架构编译，仅当前架构的 arch_<X>/*.cpp 按架构编译。把 dav-3510 专属 API（MicroAPI/RegTensor/aicpu tiling/get_aiv_num）代码放在根目录时，NPU_ARCH=dav-2201 全量编译因找不到这些符号而 exit=2；将专属代码移入 arch_3510/ 子目录后 dav-2201 单算子编译通过。判别=用 -DOPERATOR_NAME 单算子构建隔离错误来源，确认错误来自兄弟算子根目录代码而非目标算子 arch_2201 代码。"
tags: ["task.debugging", "topic.compilation", "topic.implementation"]
status: stable
sources: []
created_at: "2026-08-18T15:56:42Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# CMake arch 子目录隔离 dav-3510 专属 API

## 适用场景

- **工程形态**：构建——使用 xpu_ops v2 框架的 CMake 构建系统（`ops/backends/ascend/CMakeLists.txt` 与 `build_asc.cmake`），按 `NPU_ARCH` 派生 `ASCEND_ARCH_OPS_DIR` 隔离不同架构的算子实现。
- **API 路径**：CMake 变量 `NPU_ARCH`（`dav-3510`/`dav-2201`）→ 派生 `ASCEND_ARCH_OPS_DIR`（`arch_3510`/`arch_2201`）→ `file(GLOB_RECURSE)` 扫描算子根目录 .cpp（排除 `arch_*` 子目录，对所有架构编译）+ 当前架构 `arch_<X>/*.cpp`（仅匹配架构编译）。
- **验证平台与版本**：Ascend950PR（dav-3510），CANN 版本未从 trace 恢复。
- **适用粒度**：`operator_family`——所有在 v2 框架根目录使用 dav-3510 专属 API 的算子（dequant_swiglu_quant、moe_gating_topk、moe_init_routing_dynamic_quant）均适用。
- **不适用或未验证场景**：无 `ASCEND_ARCH_OPS_DIR` 派生与 `arch_*` 子目录扫描机制的旧版 CMake 不适用；a3/a2 平台未验证。

## 判别方法

**触发**（tool_observed 失败）：在 xpu_ops v2 框架中迁移 dequant_swiglu_quant 算子，算子根目录（`kernels/dequant_swiglu_quant/*.cpp`）使用 dav-3510 专属 API（`DequantSwigluQuantAicpuTiling` aicpu tiling kernel、`MicroAPI`、`RegTensor`、`get_aiv_num`、`get_ub_size`）。配置 `NPU_ARCH=dav-2201` 执行全量构建，`make` 返回 exit=2（compile_failure）。

**探针**（可执行检查）：

1. 用单算子构建隔离错误来源：`cmake .. -DTARGET_DEVICE=ASCEND -DNPU_ARCH=dav-2201 -DOPERATOR_NAME=dequant_swiglu_quant && make -j64`，确认目标算子的 `arch_2201/` 代码本身能否编译通过。
2. 在全量构建失败的输出中 grep 报错的 `.cpp` 文件名与未定义符号（`MicroAPI`/`RegTensor`/`DequantSwigluQuantAicpuTiling`/`get_aiv_num`），确认错误是否来自兄弟算子（moe_gating_topk、moe_init_routing_dynamic_quant）根目录代码而非目标算子 `arch_2201/` 代码。
3. 将 dav-3510 专属 API 的 kernel/layer 代码移入 `arch_3510/` 子目录，根目录只保留跨架构共享的 struct 声明头文件，重跑 dav-3510 clean 构建与 dav-2201 单算子构建，观察 exit 是否为 0。

**观测**（tool_observed）：

- `NPU_ARCH=dav-2201` 全量构建返回 exit=2（compile_failure）。
- `NPU_ARCH=dav-3510` clean rebuild 返回 exit=0，.so 含 dequant arch_3510 layer object。
- `NPU_ARCH=dav-2201` 单算子 clean 构建（`-DOPERATOR_NAME=dequant_swiglu_quant`）返回 exit=0，.so 1.29MB，link 含 `arch_2201/dequant_swiglu_quant.cpp.o`。

**判读**（根因解读，agent 对被 redaction 占位的构建错误输出做的归因）：xpu_ops v2 CMake 的 `file(GLOB_RECURSE)` 把算子根目录 .cpp（排除 `arch_*` 子目录）作为"跨架构代码"对**所有**架构编译，仅当前架构对应的 `arch_<X>/*.cpp` 按架构编译。当 dav-3510 专属 API（`MicroAPI`/`RegTensor`/`DequantSwigluQuantAicpuTiling`/`get_aiv_num`）的代码留在根目录时，`NPU_ARCH=dav-2201` 下编译器找不到这些符号的定义，全量构建 exit=2；而目标算子的 `arch_2201/` 代码本身无错误（单算子构建 exit=0），失败来自兄弟算子（moe_gating_topk、moe_init_routing_dynamic_quant）根目录代码对 dav-3510 专属 API 的引用。修复方向=将 dav-3510 专属代码移入 `arch_3510/` 子目录、dav-2201 兼容版本移入 `arch_2201/` 子目录、根目录只留跨架构共享头文件，使 CMake 仅在 `NPU_ARCH=dav-3510` 时编译含专属 API 的代码。

## 验证信号

来源：dequant_swiglu_quant 算子从 operators 直调工程迁移至 xpu_ops v2 框架的构建环节，Ascend950PR（dav-3510）硬件。

- `NPU_ARCH=dav-2201` 全量构建返回 exit=2，编译失败（来源平台:950；证据等级:tool_observed）
- `NPU_ARCH=dav-3510` clean rebuild 返回 exit=0，.so 含 dequant arch_3510 layer object（来源平台:950；证据等级:tool_observed）
- `NPU_ARCH=dav-2201` 单算子 clean 构建返回 exit=0，.so 1.29MB，link 含 `arch_2201/dequant_swiglu_quant.cpp.o`（来源平台:950；证据等级:tool_observed）

<!-- cannbot:related:start -->
## 相关

- [asc_copy_l12l0a](../../apis/simd_api/c_api/cube_data_move/asc_copy_l12l0a/asc_copy_l12l0a_arch_3510.md)（`exemplifies`）：asc_copy_l12l0a 与《CMake arch 子目录隔离 dav-3510 专属 API》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [2201到3510架构变更](../../guides/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_arch_changes.md)（`related`）：CMake arch 子目录隔离 dav-3510 专属 API 与《2201到3510架构变更》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [CMake函数参考（附录）](../../guides/programming_guide/advanced_programming/aclnn_operator_development/appendix/cmake_function_reference.md)（`related`）：CMake arch 子目录隔离 dav-3510 专属 API 与《CMake函数参考（附录）》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [NPU架构版本2201](../../guides/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_2201.md)（`related`）：CMake arch 子目录隔离 dav-3510 专属 API 与《NPU架构版本2201》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [NPU架构版本3510](../../guides/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_3510.md)（`related`）：CMake arch 子目录隔离 dav-3510 专属 API 与《NPU架构版本3510》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [算子编译迁移指导](../../guides/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/op_compilation_migration.md)（`related`）：CMake arch 子目录隔离 dav-3510 专属 API 与《算子编译迁移指导》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [编译与部署基本流程](../../guides/programming_guide/advanced_programming/aclnn_operator_development/compilation_and_deployment/basic_process.md)（`related`）：CMake arch 子目录隔离 dav-3510 专属 API 与《编译与部署基本流程》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [高级编程编译加速](../../guides/programming_guide/advanced_programming/aclnn_operator_development/compilation_and_deployment/compilation_acceleration.md)（`related`）：CMake arch 子目录隔离 dav-3510 专属 API 与《高级编程编译加速》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa](arch_variant_lookup_chain_soc_ini_npuarch_dispatcher.md)（`same_topic`）：CMake arch 子目录隔离 dav-3510 专属 API 与《Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [C-API asc_simd.h 编译缺 include 根](c_api_asc_simd_h_include.md)（`same_topic`）：C-API asc_simd.h 编译缺 include 根 与《CMake arch 子目录隔离 dav-3510 专属 API》的实质衔接是：深层 impl 头实际存在，失败源于 CMake 只加 asc/include 而未加 asc/impl/c_api；C API 入口、官方编译/CMake材料和相邻 include 误用卡用于核对正确头链。
- [arch35 kernel 上板报 507035 实为 arch 不匹配](arch35_kernel_507035_arch.md)（`same_topic`）：CMake arch 子目录隔离 dav-3510 专属 API 与《arch35 kernel 上板报 507035 实为 arch 不匹配》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav](bisheng_npu_arch_requires_lowercase_dav_2201.md)（`same_topic`）：bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav 与《CMake arch 子目录隔离 dav-3510 专属 API》的实质衔接是：故障根因是把 DAV_2201 内部名误写成 bisheng 参数；架构查证链、GetCurNpuArch、dav-3510 同类 CMake 隔离、编译器/迁移文档和 CMake 参考共同确认 token 映射与全量重配。
<!-- cannbot:related:end -->
