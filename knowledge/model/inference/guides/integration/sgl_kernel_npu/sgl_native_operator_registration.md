---
type: Guide
title: SGLang 原生算子声明与架构变体替换规则
description: 说明 sgl_register_operator 的执行单元、源码角色、架构变体整字段替换、combined Host 与 codegen
  编译边界。
tags:
- task.implementation
- topic.compilation
- topic.programming_model
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/operators.cmake
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
created_at: '2026-11-08T11:03:52Z'
updated_at: '2026-11-08T11:03:52Z'
platforms:
- a2
- a3
- '950'
---

# SGLang 原生算子声明与架构变体替换规则

## 声明职责

REFACTOR 在 `csrc/<domain>/<operator>/CMakeLists.txt` 通过 `sgl_register_operator` 声明算子，先公共声明再注册 `sgl_register_operator_variant(ID ... ARCH ...)`。支持架构为 2201=A2/A3、3510=950；这仅描述构建准入，不能代替每个 Kernel 的验证结果。

| 执行单元 | 必要源码合同 |
| --- | --- |
| AICORE | `CANN_OP_TYPE`、非空 `SUPPORTED_ARCHS`、公共 `OPDEF_SOURCES`；最终配置非空 Tiling 源码且恰好一个 Kernel 入口。 |
| AICPU | CANN 类型、支持架构、非空 Kernel `.cpp` 列表；打包需 `AICPU_JSON`，不强制 AI Core OpDef/Tiling。显式 ACLNN 包装可声明 `ACLNN_SOURCES/ACLNN_HEADERS`。 |
| HOST | `CPP_SOURCES`、`TORCH_ADAPTER`、支持架构；拒绝 CANN 专用字段，domain 还须进入 `sgl_add_host_operator_domains()`。 |

wheel 中每个所选原生算子必须有 Torch adapter；CANN-only `.run` 可不需要。`--ops all` 排除架构不支持的算子，显式请求不支持算子报错，不能清空必需源码来伪装支持。

## 变体不是追加

同一可变字段省略时继承；显式列表替换整个公共列表；`FIELD ""` 清空允许为空的私有设置或 Infer 源；只有字段名没有值属于错误。Kernel 源、选项、宏、include、Tiling 源、Infer 源都按整字段规则解析，不做逐项合并。

例如公共 Kernel 宏 `MODE=1` 和 arch35 变体 `MODE=2` 合法，因为后者替换；同一最终列表同时出现这两个定义失败。需保留的公共选项或 helper 源必须在替换列表重新列全。清空 AI Core Tiling 或任一 CANN Kernel 必需字段仍失败。

重复字段关键字、公共 ID 或同一 ID/ARCH 变体声明均失败，即使值相同也不合并。最终源码/include/相同宏可去重；Kernel options 保留顺序及重复 token。源路径相对声明文件目录归一化，最终选择的文件与 include 目录必须存在；宏写 `NAME` 或 `NAME=value`，不加 `-D`。

## Host 文件与 codegen

源码字段表示职责，不强制一角色一文件。一个含 `OP_ADD` 和 `SetTiling` 的 combined Host 文件可同时列入 OpDef/Tiling；若也负责 shape/type inference，还须列入 Infer。codegen 编译整个 OpDef 输入文件，不会转发算子私有 Tiling include 与宏；只有普通 Tiling 编译成功不足以证明 codegen 可编译。

清空 Infer 只省略手写推导，不会移除存在的生成 `op_proto.cc`。只在目标调用路径确实不需手写推导时省略。生成 `sgl_operator_config.h` 同时可见于 TILING/GRAPH；OpDef 目录和 combined 文件选中 Kernel 目录内头文件进入依赖跟踪，外部头变化需显式 clean 重建。

## 复核方法

逐架构检查最终解析字段，再看生成配置、build manifest 和实际 wheel 绑定；不要把注册声明当作 Device 算法闭包。本次为构建系统 reference 分析，未编译、未运行数值或性能测试。
