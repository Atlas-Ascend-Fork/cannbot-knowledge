---
type: Guide
title: TorchAir SuperKernel：GE 发布契约与主线捕获优化
description: 区分 GE 静态 scope 与 npugraph_ex 捕获后融合、静态编译依赖和调试限制。
tags:
- task.optimization
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/super_kernel_scope.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/superkernel.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/super_kernel.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/super_kernel_scope.md
  role: constraint
created_at: '2026-11-09T02:14:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchAir SuperKernel：GE 发布契约与主线捕获优化

## 版本与范围

发布文档固定在 ascend_26_0_pt28 的 TorchAir 子模块提交 7c6c754bed00c86ffaaa2a45cb7ac2724f058013；主线补充固定在 92e1e967bd35ebc37a442b4a969730bf3cf77a3c。以下分开说明，未做 NPU 运行验证。 发布及主线GE分支限定A2/A3；主线npugraph_ex的950PR/950DT专用选项另列，模型具体scope选择见场景链接。

## GE 发布版

仅 GE 静态图使用 torchair.scope.super_kernel(scope,options)。scope 名标记范围，None 表示不融合；不支持融合的算子会截断融合段，因此一个 scope 不保证一个 Kernel。AllReduce、ReduceScatter、AllGather、AlltoAll 有融合支持，但仍需对应算子路径满足条件。

options 是冒号分隔的字符串。stream-fusion=1 允许 scope 内多流共用资源；micro-batch 中流与核绑定、资源独立，来源不推荐同时启用它。strict-scope-check 可选 bypass/abort 检查断裂，但不检查范围内集合通信算子。feed-sync-all=1 为小核数子算子的 SyncAll 补齐其余核，默认关闭时调用方须保证子算子与 SuperKernel 启动核数匹配。

debug-aic-num/debug-aiv-num 不得超过硬件、limit_core_num 或原本应启动的核数，比例仅 1:0、0:1、1:1、1:2。不要把缓存刷新选项作为可任意组合的通用加速开关。

## npugraph_ex 主线

捕获后识别连续 Task 并更新 Model；options 同时需要 static_kernel_compile=True 和 super_kernel_optimize=True。可用 super_kernel_scope_begin/end 标定，但标记仍不保证融合结果；scope 名≤255字节，不同名字总数≤1024。重叠 scope 按标记集分组，None 排除标记优先，不能简单按最外层范围解释。

开启后算子 Data Dump 失效。同进程多个 Model 的同 shape 算子若静态编译设置不同，可能复用前一个产物而影响融合结果，应保持相关配置一致，或只为需要的模型开启静态编译。debug_sync_all、执行轨迹和满核验证会改变调度及性能，不用其结果直接报告正常收益。950专用ubuf_lock_ignore_kernel不属于本节A2/A3通用路径。

## 验证

核对实际融合段、Block Dim/核数、同步、缓存一致性和输出，再测相同输入下的稳态耗时。编译成功和 scope 标记都不证明净收益。

- [模型范围、R1 与 LongCat 场景](../../../concepts/techniques/superkernel.md)
- [静态 Kernel 编译](../../../optimizations/rules/npugraph_ex_static_kernel_compile.md)

## 主线诊断与高级同步入口

下面的诊断和选项依据固定主线，不将相同产物、COND 布局或调试能力回推到本卡的发布版 GE。先核对实际运行版本，再选择：

- [确认真实融合、Scope 切分和资源不足](superkernel_fusion_diagnostics.md)
- [定位异常子算子、COND 与 ModelIdIdx](superkernel_exception_localization.md)
- [同范围性能比较及两后端 DCCI 差异](superkernel_performance_diagnosis.md)
- [npugraph_ex Early-Start 与 ValueWait 融合](npugraph_ex_superkernel_sync_controls.md)

## 主线GE scope的对应接口

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的GE super_kernel(scope, options="")接口页与发布接口相同，仍只用于GE静态图且scope内不允许断图。相同scope名表示同一用户范围，None排除融合；遇到不可融合算子会分段并跳过，不能以同名范围或给定options证明最终只有一个Kernel。接口列AllReduce/ReduceScatter/AllGather/AlltoAll也不免除各算子、CANN和资源约束。

GE功能页的A2/A3明确限制优先于主线总览的通用产品范围，不能由API页未列排除就扩为950。npugraph_ex的950专用选项见下节，图内scope和捕获后Task融合仍是两种机制。

## 功能页的产品限制优先于通用总览

主线GE功能页明确写“仅支持Atlas A2系列、Atlas A3系列”，发布页同样列A2/A3。主线总览虽列950PR/950DT，通用super_kernel API页也没有重新列产品表，均不足以覆盖功能页的明确限定。因此本卡GE分支只按A2/A3消费，撤回从总览扩出的950 GE支持表述；这也不是断言其他未确认组合绝对不可运行。

主线npugraph_ex功能页另列950PR/950DT专用ubuf_lock_ignore_kernel：默认空列表，按带前后缀的真实算子符号名以.*形式匹配，声明目标算子不依赖UB Buffer加/解锁保证访问顺序后才优化融合策略。它不适用于A2/A3，不能据此允许忽略真实UB依赖。该分支与GE scope选项分别核对。

主线GE stream-fusion=0的范围若实际跨多流会编译报错；=1允许多流融合但不增加原本并行度，内部同步仍可能串行化。npugraph_ex标记仅有None时，未被标记算子仍进入融合；同时存在具名标记时，未标记算子不进入融合。交叠/嵌套范围按完整标记集分组，None排除始终优先。图示分组不保证一个不连续集合最终只生成一个Kernel。

两版GE数值示例的算子组合不同，而且只比较部分返回值；npugraph_ex示例只打印Launch Success。它们均不是全部输出、输入回写、融合范围和性能均已验证的证据。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/super_kernel_scope.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/superkernel.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/super_kernel.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/super_kernel_scope.md)（constraint）
