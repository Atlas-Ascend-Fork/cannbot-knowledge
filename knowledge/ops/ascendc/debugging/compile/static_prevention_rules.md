---
type: Guide
title: Ascend C 工程编译配置的静态预防规则（CMake/头文件/Host 特性/跨文件契约）
description: 上板前可静态检查的编译配置规则：CMake 规则仅适用于明确采用 ASC 语言工具链的工程（ascendc.cmake/ascendc_library legacy 形态合法，不判错）、ASC 语言启用含 npu_op_package 宏间接形态、头文件按实际 API 与编程模型判定（SIMT 示例用 asc_simt.h 可不含 kernel_operator.h）、Kernel 侧禁用 host-only C++ 特性、TilingData 等符号跨 host/kernel 文件须有定义（跨文件契约）、include/driver 头文件 CANN 9.1.0 起废弃并迁移 pkg_inc/driver（计划 2027-06-30 后删除；命中先查环境文件与 include 路径再迁移，9.0 域仍合法勿改）。
tags: [task.debugging, topic.compilation, topic.implementation]
status: stable
sources:
  - resource: https://gitcode.com/yeswecann/all_in_one/blob/35fffec73cf110d097f1a8a6624b60fd20357bbe/skills/tool-compile-debug/scripts/engine/configs/static_rules.yaml
    role: primary
created_at: "2026-11-05T05:20:00Z"
updated_at: "2026-11-10T03:15:00Z"
platforms: [a2, a3, "950"]
---

# Ascend C 工程编译配置的静态预防规则（CMake/头文件/Host 特性/跨文件契约）

可静态检查的编译配置与源码模式规则——不需要真实编译就能发现的错误（诊断流程总纲见[编译失败诊断流程](failure_diagnosis_flow.md)）。

## CMake 配置规则

| 规则 | 检查 | 修复 |
| --- | --- | --- |
| `cmake_missing_find_package_asc` | CMakeLists.txt 无 `find_package(ASC`（**仅适用于已明确采用 ASC 语言工具链的工程**） | 在声明 Ascend C target 前加 `find_package(ASC REQUIRED)`。**注意**：合法的 Kernel Launch 工程也可采用 `ascendc.cmake` + `ascendc_library` 的 legacy 构建方式（如 vllm-ascend 的 CMakeLists），不含 `find_package(ASC)` 不构成配置错误——识别到该形态时跳过本规则，不诱导构建改造 |
| `cmake_missing_language_asc` | project 未启用 ASC 语言 | `project(<name> LANGUAGES ASC CXX)` 或 `enable_language(ASC)`；**注意**经 msopgen 包宏（`npu_op_package` / `npu_op_kernel_library`）间接启用的工程合法——只查第一种形态会误报宏工程 |
| `cmake_missing_compile_commands` | 未显式请求 compile_commands.json | `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON`（便于诊断，warning 级） |

## 头文件与源码规则

- `kernel_operator_header_missing`：使用 Ascend C kernel API 的文件须 include `kernel_operator.h`——**按实际使用的 API 与编程模型判定**（如官方 Ascend 950 SIMT 示例使用 `simt_api/asc_simt.h`，可不含 `kernel_operator.h`；合法的间接包含同样满足），只查字面 include 会误报合法代码缺头文件；
- `suspicious_host_only_feature_in_kernel`：Kernel 侧源码（`__aicore__` 代码）出现 host-only C++ 特性（`throw` / `try` / `catch` / `new` / `delete` / `std::vector` / `std::map` / `typeid` / `dynamic_cast`）——Ascend C 编译器可能不支持，host-only 构造移出 kernel 代码（warning 级：字符串误报需人工核对）；
- `kernel_code_size_risk`：大型 switch/展开模式可能触发编译器代码量上限——拆分大 kernel 或减少分支展开（warning 级）。

## 跨文件契约规则

`crossfile_define_use`：符号在 host/kernel 文件间被引用但项目内无定义（如 TilingData 类型、共享常量、kernel 入口符号）→ 跨文件契约断裂；修复为对齐 tiling.h / kernel / host 的定义与使用点，或重新生成工程。外部符号前缀白名单（`ACL_`、`ASCEND`、`AICORE`、`GM_`、`DT_`、`OP_`、`FORMAT_`、`VECIN`、`VECOUT`、`VECCALC`、`DOUBLE_BUFFER` 等）不触发。

## 版本敏感的头文件路径迁移

`include/driver/*` 头文件 **CANN 9.1.0 起迁移到 `pkg_inc/driver/*`**（9.1.0 标记废弃；官方计划 2027-06-30 之后的版本删除）：

- ≥9.1.0 工具链上引用旧路径报 `fatal error: No such file or directory`——旧路径在 CANN 9.1.0 标记**废弃**（计划 2027-06-30 之后的版本删除），命中时**先检查当前环境实际文件与编译器 include 路径**（排除 SDK 安装不全或 include 路径配置错误等真实原因），确认旧路径文件确已迁移后再改 include 路径，而非直接断定缺依赖；
- **9.0 目标工程命中旧路径属预期（旧路径在 9.0 域仍合法，勿改）**——本规则带版本条件，不能无差别重写。

## 适用边界

- 规则命中是「预防性线索」不是结论：`violated` 需区分合法全局改名与删除使用点；white-list 形态覆盖不完全，判断以实际声明与调用关系为准；
- 规则引擎（regex/版本域过滤）留技能仓，本卡保存规则语义；CMake 宏工程的间接启用形态等规则细节随引擎版本演进，以来源提交为准。
