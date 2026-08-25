---
type: "Runbook"
title: "aclnn_exclude 头文件自动生成覆盖源码致签名不符"
description: "自定义算子走 aclnn_exclude 路径时，源码实现与 vendors 安装头的接口签名可能不一致，导致 ST 编译失败；通过对比源码声明、实现、安装头和 CMake 命中路径定位生成物错配。"
tags: ["task.debugging", "topic.compilation", "topic.implementation.api_layer.c_api"]
status: stable
sources: []
created_at: "2026-08-18T05:31:13Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# aclnn_exclude 头文件自动生成覆盖源码致签名不符

## 现象

ReduceStdV2Update 算子 ST 测试编译报 `aclnnReduceStdV2UpdateGetWorkspaceSize` 签名不符：测试代码按 8 参数调用，但编译器报参数个数不匹配。核查发现源码 `op_api/aclnn_reduce_std_v2_update.h` 是手写 8 参数版本（与 `op_api/aclnn_reduce_std_v2_update.cpp` 实现一致），而安装到 vendors 下的同名头文件是 10 参数版本（多了 `ifStd` 和 `correction`）。ST CMakeLists 的 `find_path` 命中 vendors 下的错误版本，导致按 10 参数签名编译与 8 参数调用不匹配。

## 适用场景

- **工程形态**：算子构建系统（build.sh + CPack 打包）+ ST 测试 CMake 编译。
- **API 路径**：`op_host/*_def.cpp` 的 `OP_ATTR` 声明 → 构建系统自动生成 aclnn 头文件 → CPack 打包到 vendors → ST CMakeLists `find_path` 引用 vendors 头文件。
- **验证过的平台与 CANN 版本**：Ascend950（dav-3510 / arch35），CANN 9.2.0。
- **适用粒度**：`platform_wide`（CANN 自定义算子 aclnn_exclude 构建机制跨平台通用）。
- **路线优先级**：`diagnostic_only`。本卡只定位源码接口、安装头和搜索路径之间的不一致，不提供临时覆盖或未经验证的构建系统修复。
- **明确不适用或未验证场景**：A3/A2 未验证；非 aclnn_exclude 路径（L2 接口暴露全部属性）的算子，自动生成版本与源码一致，不触发本问题。

## 判别方法

1. **触发信号**：ST 编译报 `aclnnReduceStdV2UpdateGetWorkspaceSize` 签名不符——测试代码按 8 参数调用，编译器报参数个数不匹配；同时可能伴随 `ACL_BFLOAT16` 等常量名报错。属系统性签名错配，非单 case 问题。
2. **可执行探针**：`diff` 源码 `operators/<op>/op_api/aclnn_*.h` 与 vendors 安装版 `${ASCEND_HOME_PATH}/opp/vendors/<op>_custom/op_api/include/aclnn_*.h` 的 `GetWorkspaceSize` 签名；核查 `op_host/*_def.cpp` 的 `OP_ATTR` 声明数量；核查 ST CMakeLists `find_path` 的搜索路径顺序。
3. **原始观测**：源码头文件为 8 参数（verbatim 取自 trace reasoning 对源码 `op_api/aclnn_reduce_std_v2_update.h` 的引用）：
   ```c
   aclnnStatus aclnnReduceStdV2UpdateGetWorkspaceSize(
       const aclTensor* self,
       const aclTensor* mean,
       const aclIntArray* dim,
       bool unbiased,
       bool keepdim,
       aclTensor* output,
       uint64_t* workspaceSize,
       aclOpExecutor** executor);
   ```
   vendors 安装版为 10 参数（自动生成，verbatim 取自 trace reasoning 对 vendors 头文件的引用）：
   ```c
   aclnnStatus aclnnReduceStdV2UpdateGetWorkspaceSize(
       const aclTensor *x,
       const aclTensor *mean,
       const aclIntArray *dim,
       bool ifStd,           // 多了 ifStd
       bool unbiased,
       bool keepdim,
       int64_t correction,   // 多了 correction
       const aclTensor *out,
       uint64_t *workspaceSize,
       aclOpExecutor **executor);
   ```
   `op_host/reduce_std_v2_update_def.cpp` 声明 5 个 `OP_ATTR`（dim/if_std/unbiased/keepdim/correction）。ST CMakeLists `find_path` 查找 `aclnn_reduce_std_v2_update.h` 命中 vendors 下错误版本。
4. **解释**：本例中源码声明与实现采用 8 参数接口，vendors 安装头采用由 op_def 属性展开出的 10 参数接口，而 ST 实际命中后者。由此可确认编译失败来自接口生成物与实现契约不一致；应以源码声明、实现和实际导出符号的联合核对为准，不能仅凭任一份头文件推断通用生成机制。

## 验证信号

- 源码 `op_api/aclnn_reduce_std_v2_update.h` 的 `aclnnReduceStdV2UpdateGetWorkspaceSize` 为 8 参数（无 ifStd/correction）（来源平台:950；证据等级: tool_observed）。
- vendors 安装版 `aclnn_reduce_std_v2_update.h` 为 10 参数（多 ifStd、correction），与源码不一致（来源平台:950；证据等级: tool_observed）。
- `op_host/reduce_std_v2_update_def.cpp` 声明 5 个 `OP_ATTR`（dim/if_std/unbiased/keepdim/correction），是自动生成 10 参数头文件的属性来源（来源平台:950；证据等级: tool_observed）。
- ST CMakeLists `find_path` 查找 `aclnn_reduce_std_v2_update.h` 命中 vendors 下的错误版本（来源平台:950；证据等级: tool_observed）。

## 失效边界

- Ascend950/CANN 9.2.0 实测；A3/A2 未验证，推断可迁移（aclnn_exclude 构建机制跨平台一致）。
- 本卡诊断的是 aclnn_exclude 路径特有的头文件生成错配；非 aclnn_exclude 路径（L2 接口暴露全部属性）的算子，自动生成版本与源码一致，不触发。

## 预防

- 自定义算子走 aclnn_exclude 路径时，在打包验收中同时核对源码声明、实现签名、vendors 安装头和最终导出符号，确保四者一致。
- 联调阶段遇到"aclnn 接口签名不符"且测试代码与源码实现一致时，优先怀疑 vendors 头文件是自动生成版本，diff 源码与 vendors 即可定位。

## 坏实践

- 手工覆盖 vendors 头文件后把一次编译通过当成生成链已修复；重新打包仍可能产生不一致头文件。

<!-- cannbot:related:start -->
## 相关

- [OpDef](../../apis/utils_api/prototype_register_management/op_def/op_def.md)（`exemplifies`）：OpDef 属性列表是 autogen 头文件签名的源契约。
- [561103 同名算子签名冲突链接绑内置版](561103.md)（`related`）：561103 同名算子签名冲突链接绑内置版 与《aclnn_exclude 头文件自动生成覆盖源码致签名不符》的实质衔接是：同名签名冲突的核心是运行时绑定到错误或被自动生成覆盖的符号；符号探测、opType 碰撞、pytest 绕过和 exclude 覆盖案例给出可执行鉴别，其他 561103 卡用于排除属性与 tiling 路由根因。
- [ACLNN 507035 — opType 与内置 ops_legacy 同名碰](aclnn_optype_collision_built_in_ops_legacy_507035.md)（`related`）：生成签名正确后仍需确认运行时未绑定内置同名 binary。
- [ACLNNTYPE aclnn autogen 与手写同名符号冲突](aclnntype_aclnn_autogen.md)（`related`）：两卡围绕 ACLNNTYPE 的相反路径：aclnn 生成同名实现可与手写文件重复定义，aclnn_exclude 则可能生成安装头并与手写签名错配，能据构建开关分流诊断。
- [ACLNN GetWorkspaceSize 缺 L0 调用致输出全零](aclnn_l2_get_workspace_size_requires_l0_launcher_list.md)（`same_topic`）：aclnn_exclude 生成链仍需 L0 launcher list，二者共同决定头文件/符号是否生成。
<!-- cannbot:related:end -->
