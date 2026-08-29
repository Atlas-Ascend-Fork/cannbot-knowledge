---
type: "Runbook"
title: "__simd_vf__ if constexpr 致 hoisted 报错"
description: "dav-3510 上某 Reg __simd_vf__ 实现使用 if constexpr 与 constexpr trait 时，bisheng 后端报 Unsupported Inst must be hoisted 并退出 70；记录源码定位与编译边界，不提供未完成的 fallback 实现。"
tags: ["task.debugging", "topic.programming_model.execution_model.simd", "topic.compilation"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-28T06:56:32Z"
platforms: ["950"]
---

# __simd_vf__ if constexpr 致 hoisted 报错

## 现象

在 Ascend950 / dav-3510 上构建 rms_norm kernel 时，`__simd_vf__` 函数体使用 `if constexpr` 做 dtype 分发，并引用 `CastB32ToB16Trait<T>::value`。bisheng 在编译 kernel object 时进入后端失败：

```text
fatal error: error in backend: Unsupported Inst must be hoisted.
bisheng: error: clang frontend command failed with exit code 70
```

错误发生在 kernel object 构建阶段，不是运行期精度问题。

## 适用场景

- **工程形态**：dav-3510 kernel 直调构建。
- **API 路径**：`__simd_vf__` / `__simd_callee__`、`AscendC::Reg`、`asc_vf_call`。
- **验证平台**：Ascend950 / dav-3510。
- **适用粒度**：`exact_task`。其他函数体或其他 constexpr 表达式须独立复现。
- **路线优先级**：`banned`。只禁止本例已复现的 VF 内编译期分支形态；本卡不推荐替代实现。

## 判别方法

1. 确认构建日志包含 `Unsupported Inst must be hoisted` 和 exit code 70，且报错落在包含 VF 实现的 kernel object。
2. 检查 `__simd_vf__` 及其调用的 `__simd_callee__` 是否含 `if constexpr` 或参与分支判定的 `::value` trait。
3. 本 trace 中把相同分支移动到 `__simd_callee__` 后报错不变，因此仅移动到另一个 VF callee 不能规避问题。
4. trace 没有继续隔离到具体 IR 指令，不能把所有 constexpr 使用一概判为不支持。

## 验证信号

- rms_norm kernel object 构建报 `Unsupported Inst must be hoisted` / exit code 70（来源平台：950；证据等级：tool_observed）。

## 失效边界

- 只在 dav-3510 的这一 kernel 与编译器环境实测；dav-2201、dav-2203 未验证。
- 把分支移到 `__simd_callee__` 后错误仍出现只有 `agent_reported` 陈述，不作为独立验证信号。
- 后续另一实现可完成构建，但其源码未逐字恢复，且没有运行期精度或性能结果，不能作为本卡的解决方案。
- 后端失败的精确 IR/指令尚未隔离；结论限于出现同一报错时优先审查 VF 内编译期分支。
- 经典 AscendC compute、类级模板特化等替代路线未形成“构建 + 运行 + 精度”闭环，不纳入本卡。

## 坏实践

- 把 `if constexpr` 原样移入 `__simd_callee__` 后认为已经离开 VF lowering 上下文。
- 仅凭另一实现构建成功，就宣称其运行正确或性能可接受。
