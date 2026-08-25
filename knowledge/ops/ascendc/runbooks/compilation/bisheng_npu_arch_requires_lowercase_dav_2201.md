---
type: "Runbook"
title: "bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav"
description: "CMakeLists.txt 的 ASC 编译选项 --npu-arch 必须传小写带连字符的 NpuArch 规范名 dav-2201，传 SoC 名 DAV2201 或全大写会被 bisheng 以 \"Unsupported NPU architecture\" 拒绝。"
tags: ["task.debugging", "topic.compilation", "topic.implementation"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["a2"]
---

# bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav

## 现象

在 Ascend 910B3 / CANN 9.0.0 上用 ops-direct-invoke 工作流重建 ReLU 算子工程时，执行 `make -j4` 编译 ASC 源（`op_kernel/relu_kernel.asc` 与 `op_host/relu.asc`）立即失败，bisheng 报：

```
bisheng: error: Unsupported NPU architecture or soc: NPU arch is not supported!!!
bisheng: error: Unsupported NPU architecture or soc: NPU arch is not supported!!!
LLVM ERROR: PlugIn Error: no aicore arch specified.
```

栈转储里 bisheng 命令行可见 `-npu-arch=DAV2201`。CMakeLists.txt 中两处 `target_compile_options` 的 ASC 段都写成 `$<$<COMPILE_LANGUAGE:ASC>:--npu-arch=DAV2201>`（全大写、无连字符，直接抄了 SoC/NpuArch 名 `DAV_2201` 去下划线的形式）。设计文档 DESIGN.md 的一行注释曾写"DAV_2201 编译时使用 `--npu-arch=DAV2201`"，正是这条误导性注释让开发者写错。

## 适用场景

- **工程形态**：ops-direct-invoke Kernel 直调工程（CMakeLists.txt 双 target：`add_executable` 可执行 + `add_library ... TORCH_LIBRARY` 扩展），用 bisheng 编译 `.asc` 源。
- **API 路径**：CMakeLists.txt 的 `target_compile_options(<target> PRIVATE $<$<COMPILE_LANGUAGE:ASC>:--npu-arch=...>)`；bisheng `--npu-arch` 旗标。
- **验证过的平台与 CANN 版本**：Ascend 910B3（SocVersion `ASCEND910B`，NpuArch `DAV_2201`），CANN 9.0.0。对应注册平台 token `a2`。
- **适用粒度**：`platform_wide`——所有 DAV_2201 共享架构（A2/A3）上 `--npu-arch` 旗标格式一致。
- **路线优先级**：`recommended_fastpath`——直接写正确的小写 `dav-2201`。
- **不适用或未验证场景**：非 DAV_2201 架构（如 DAV_1001/DAV_3510）的 `--npu-arch` 取值需按各自 NpuArch 规范名另行确认；本卡只验证过 910B3/DAV_2201。

## 根因

bisheng 的 `--npu-arch` 旗标要求传**NpuArch 规范名的小写带连字符形式**（`dav-2201`），不是 SoC 枚举名 `ASCEND910B`、也不是 NpuArch 内部名 `DAV_2201` 去下划线全大写后的 `DAV2201`。传 `DAV2201` 时 bisheng 无法匹配任何已知 aicore 架构，于是既报 "Unsupported NPU architecture or soc"，又在后端触发 "no aicore arch specified"（LLVM 插件因没拿到 arch 直接停摆）。三条信息（产品 910B3、SocVersion `ASCEND910B`、NpuArch `DAV_2201`）都不能直接塞给 `--npu-arch`，必须经过"NpuArch → 小写带连字符"这一步映射：`DAV_2201` → `dav-2201`。

## 解决配方

修复 CMakeLists.txt 中两处 ASC 编译选项，把 `--npu-arch=DAV2201` 改为 `--npu-arch=dav-2201`（一处给可执行 target `relu`，一处给库 target `relu_ops`）。

before（CMakeLists.txt，可执行 target 段）：

```cmake
target_compile_options(relu PRIVATE
    $<$<COMPILE_LANGUAGE:ASC>:--npu-arch=DAV2201>
)
```

after（CMakeLists.txt，可执行 target 段）：

```cmake
target_compile_options(relu PRIVATE
    $<$<COMPILE_LANGUAGE:ASC>:--npu-arch=dav-2201>
)
```

before（CMakeLists.txt，库 target 段）：

```cmake
target_compile_options(relu_ops PRIVATE
    ${TORCH_CXX_FLAGS}
    $<$<COMPILE_LANGUAGE:ASC>:--npu-arch=DAV2201>
)
```

after（CMakeLists.txt，库 target 段）：

```cmake
target_compile_options(relu_ops PRIVATE
    ${TORCH_CXX_FLAGS}
    $<$<COMPILE_LANGUAGE:ASC>:--npu-arch=dav-2201>
)
```

改完必须 `rm -rf build/* && cmake .. && make -j4` 全量重建——CMake 缓存了旧的 `--npu-arch` 参数，增量 make 不会重读 CMakeLists.txt。本 trace 里开发者第一次只跑 `make` 仍失败，正是 CMake 缓存所致。

## 预防

- DESIGN.md / 注释里写 `--npu-arch` 取值时，**一律用 NpuArch 规范名的小写带连字符形式**（`dav-2201`），不要写 SoC 名或全大写形式，以免误导后续开发者。
- 平台判型时区分四层：产品平台（A2/A3/950）→ 芯片型号（Ascend910B3）→ SocVersion（ASCEND910B）→ NpuArch（DAV_2201）。只有 NpuArch 经"小写+连字符"后才是 `--npu-arch` 的合法值。`ASCEND910B` 与 `DAV_2201` 都不是 `--npu-arch` 的合法取值。

## 验证信号

本次重建在改 `dav-2201` 并全量 `cmake .. && make -j4` 后，ASC 与 CXX 全部链接通过并跑通端到端精度验证（来源平台：a2；证据等级: tool_observed）：

- `[100%] Built target relu` / `[100%] Built target relu_ops`（来源平台：a2；证据等级: tool_observed）
- `Verification PASSED! Shape: (32768,)` / `Max diff: 0.0`（来源平台：a2；证据等级: tool_observed）
## 失效边界

- 本卡验证平台为 910B3（a2）。DAV_2201 为 A2/A3 共享架构，`--npu-arch=dav-2201` 在 A3 上同理应可用，但本 trace 未在 A3 实测——A3 未验证，推断可迁移。
- 非 DAV_2201 架构（DAV_1001/DAV_3510/DAV_2002 等）的 `--npu-arch` 取值需按各自 NpuArch 规范名小写带连字符另行确认，不得套用 `dav-2201`。

## 坏实践

- 抄 SoC 名 `ASCEND910B` 或 NpuArch 内部名 `DAV_2201` 去下划线当 `--npu-arch` 值。
- DESIGN.md 注释写"编译时使用 `--npu-arch=DAV2201`"——这条注释本身是错的，会持续误导。

<!-- cannbot:related:start -->
## 相关

- [GetCurNpuArch](../../apis/utils_api/platform_info/platform_ascend_c/get_cur_npu_arch.md)（`exemplifies`）：bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav 与《GetCurNpuArch》的实质衔接是：故障根因是把 DAV_2201 内部名误写成 bisheng 参数；架构查证链、GetCurNpuArch、dav-3510 同类 CMake 隔离、编译器/迁移文档和 CMake 参考共同确认 token 映射与全量重配。
- [CMake函数参考（附录）](../../guides/programming_guide/advanced_programming/aclnn_operator_development/appendix/cmake_function_reference.md)（`related`）：bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav 与《CMake函数参考（附录）》的实质衔接是：故障根因是把 DAV_2201 内部名误写成 bisheng 参数；架构查证链、GetCurNpuArch、dav-3510 同类 CMake 隔离、编译器/迁移文档和 CMake 参考共同确认 token 映射与全量重配。
- [NPU架构版本2201](../../guides/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_2201.md)（`related`）：bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav说明CMakeLists.txt 的 ASC 编译选项 --npu-arch 必须传小写带连字符的 NpuArch 规范名 dav-2201，传 SoC 名 DAV2201 或全大写会被 bisheng 以 "Unsupported NPU architecture" 拒绝。
- [arch35 kernel 上板报 507035 实为 arch 不匹配](arch35_kernel_507035_arch.md)（`related`）：改为 arch22 路线时，BiSheng 的 --npu-arch 需要规范小写 dav-2201；该卡避免把 SoC/大写别名继续误传给编译器。
- [毕昇编译器简介](../../guides/programming_guide/compilation_and_execution/operator_compilation/bisheng_compiler.md)（`related`）：bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav 与《毕昇编译器简介》的实质衔接是：故障根因是把 DAV_2201 内部名误写成 bisheng 参数；架构查证链、GetCurNpuArch、dav-3510 同类 CMake 隔离、编译器/迁移文档和 CMake 参考共同确认 token 映射与全量重配。
- [算子编译迁移指导](../../guides/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/op_compilation_migration.md)（`related`）：bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav 与《算子编译迁移指导》的实质衔接是：故障根因是把 DAV_2201 内部名误写成 bisheng 参数；架构查证链、GetCurNpuArch、dav-3510 同类 CMake 隔离、编译器/迁移文档和 CMake 参考共同确认 token 映射与全量重配。
- [Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa](arch_variant_lookup_chain_soc_ini_npuarch_dispatcher.md)（`same_topic`）：bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav 与《Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa》的实质衔接是：故障根因是把 DAV_2201 内部名误写成 bisheng 参数；架构查证链、GetCurNpuArch、dav-3510 同类 CMake 隔离、编译器/迁移文档和 CMake 参考共同确认 token 映射与全量重配。
- [CMake arch 子目录隔离 dav-3510 专属 API](cmake_arch_dav_3510_api.md)（`same_topic`）：bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav 与《CMake arch 子目录隔离 dav-3510 专属 API》的实质衔接是：故障根因是把 DAV_2201 内部名误写成 bisheng 参数；架构查证链、GetCurNpuArch、dav-3510 同类 CMake 隔离、编译器/迁移文档和 CMake 参考共同确认 token 映射与全量重配。
<!-- cannbot:related:end -->
