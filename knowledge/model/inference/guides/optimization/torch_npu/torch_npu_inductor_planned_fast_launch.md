---
type: Guide
title: Planned Fast Launch：计划生命周期与禁止重放的异常边界
description: 记录Python Wrapper加速条件、ABI、负缓存及回退；整套产品范围待确认。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/planned_fast_launch/planned_fast_launch.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/experimental/python_wrapper_fast_launch/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/experimental/python_wrapper_fast_launch/backend.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/experimental/python_wrapper_fast_launch/bind.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/experimental/python_wrapper_fast_launch/codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/experimental/python_wrapper_fast_launch/launcher.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/experimental/python_wrapper_fast_launch/types.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/experimental/python_wrapper_fast_launch/csrc/bindings.h
  role: implementation
created_at: '2026-11-09T15:23:53Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Planned Fast Launch：计划生命周期与禁止重放的异常边界

## 固定来源与草稿范围

依据TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的专门说明。页面要求包含该功能的torch_npu2.10系列构建、匹配的PyTorch/CANN/驱动，CANN至少8.5且运行时提供aclrtLaunchKernelWithHostArgs；没有独立正向产品矩阵，故整卡保留draft及空platforms，不从别的Inductor特性扩展设备支持。未动态加载接口、创建计划或执行kernel。

## 开关与作用范围

TORCHINDUCTOR_NPU_FAST_LAUNCH默认关闭，1在导入torch/torch_npu和compile前设置，0关闭；变化后重启并重新编译，已有Wrapper不会由改环境重写。目标是稳态Python Wrapper中NPU Triton callsite的Host固定开销，不覆盖Eager/ACLNN、CppWrapper、图分区子图或compile-time autotune。用户无需显式调用私有_npu_inductor_fast_launch_with_plan。

每callsite惰性绑定：launcher未稳定时先运行完整NPUCachingAutotuner.run，结束后再尝试建计划；已稳定且无完整入口条件时可直接建计划。必须唯一稳定、非fallback launcher，autotune、coordinate-descent以及启用的kernel binary保存均已完成。首调的编译、调优与计划成本不等于稳态收益。

## 完整入口、临时Hook与稳定负缓存

| 状态 | 文档路由 |
| --- | --- |
| grouped dynamic-shape autotuner | 不附Fast Launch元数据，直接绑定原run入口 |
| benchmark、runtime kwargs、TRITON_INTERPRET、profiler、FX/launch-params dump、精度检查 | 保留完整原入口语义，不创建/进入planned路径 |
| 空HookChain | 对象存在本身不阻止planned路径 |
| 有实际回调或旧非空single hook | 本次使用选定原launcher，保留enter/exit与metadata；不装负缓存，移除后下一次自动恢复计划 |
| CANN缺HostArgs接口、明确schema/ABI冲突、不支持资源或缺关键元数据、建plan失败 | 当前launcher安装负缓存；后续可直接调用选定原launcher，launcher变化后重判 |

缺HostArgs接口按需探测，不因此使torch/torch_npu导入失败，且在任务提交前回到原launcher。非零workspace、sync block lock、device-print缓冲不受此计划支持。schema不完整本身不拒绝，可在launcher稳定后按最终ABI补全；单次动态grid等可恢复错误不污染已有plan。

## ABI、设备与逐次校验

支持Tensor按data_ptr打包、i32/i64/u32/u64、f32/f64、按INT32打包的BOOL，以及最终ABI给出且类型受支持的runtime block参数。计划保存kernel/stub及owner、参数布局、SIMT/shared-memory配置和创建时查询的FFTS地址，不缓存每次Tensor地址、标量值、stream或grid。

每次解析非空NPU stream、当前三维grid及实参；grid先int转换，恰好三个正整数、每维≤INT32_MAX、乘积≤65535。创建时校验SIMT/shared-memory范围，每次校验参数数量/stream/grid，提交仍经OpCommand.Run。Plan不记录或检查device id，stream仅查非空、不查归属，所以同一plan不能据此安全跨设备复用。

## 异常后的重放边界

Python发现schema/backend/grid等可恢复问题时可回原launcher；**一旦调用C++ fast-launch入口，参数打包、Tensor/scalar转换、stream检查和提交阶段的异常都按可能已提交处理，不再重放原launcher**。这是避免相同kernel重复执行的边界，不能把它“修复”为捕获异常后自动重试。

只有部分callsite加速可能来自类型/资源/launcher限制；profiler或检查下不使用planned路径是预期行为。保存软件身份、路径和异常阶段，再在关闭调试后比较稳态Host与端到端耗时；文档机制不等于本模型已获益。

## 增补：主线实现面的实际边界

同一主线提交下补齐python_wrapper_fast_launch包实现（P2对账批次，静态阅读，未运行）。`types.py`定义FastLaunchError/FastLaunchPlanUnavailable异常类型；`backend.py`从ABI签名字符串解析参数种类：以`*`或`memref`开头或含`ptr`判为tensor，i1/bool、u32/u64、i32/int、i64/long、fp32/float、fp64/double分别归类，**不在支持集合（tensor/i32/i64/u32/u64/f32/f64/bool）的参数类型无法建计划**。grid归一化要求恰好三维、每维正整数且≤INT32_MAX、乘积≤65535，失败抛FastLaunchError并标记backend_submitted=False——与文档"单次动态grid可恢复"对应的实现侧错误分类。`bind.py`实现完整入口判定：`enable_fast_launch`未开、dump_fx_graph、check_accuracy、triton_interpret、dump_launch_params都会给出静态完整入口原因；grouped autotuner（inductor_meta.group_enabled或best_launcher_map）与cubin待保存（store_cubin且未cuda_kernel_saved）同样保持完整入口；launcher上的`_npu_fast_launch_enter/exit_hook_callbacks`非空时本次走选定原launcher且不装负缓存，回调移除后下一次自动恢复计划——与文档HookChain表的实现对应。`codegen.py`从triton_meta.signature剔除constants与constexpr得到运行时签名并构建callsite元数据（kernel名、调用参数、grid/launch参数）。`launcher.py`/`csrc/bindings.h`是C++ fast-launch入口的Python侧封装与nanobind绑定声明。实现面与文档一致，没有发现文档之外的放宽；本增补不新增verified，异常分类与开销差异仍待运行验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/planned_fast_launch/planned_fast_launch.md)（primary）
