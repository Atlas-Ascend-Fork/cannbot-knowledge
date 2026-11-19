---
type: Guide
title: Inductor AscendC输入合同：布局检查与动态符号绑定
description: 完整核对布局错误/调试日志、空Tensor和stride例外，以及关闭size_asserts时的输入符号与子图复合表达式绑定。
tags:
- task.implementation
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/fused_layout_check.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/input_symbol_binding.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py
  role: implementation
created_at: '2026-11-11T05:37:17Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor AscendC输入合同：布局检查与动态符号绑定

本卡完整读取主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的fused_layout_check.py和input_symbol_binding.py，定向核对根入口及npu.py消费者。发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013没有这两个具体路径；不推导其其他包缺少一切布局或符号功能。产品未知，draft/空平台，没有patch全局类、运行检查或写日志。

## 布局检查的错误、例外与日志

check_fused_layout在config.check_layout_enabled或TORCH_COMPILE_DEBUG恰为1时进入。实际/期望size和stride转int；已有int（包括bool）直接返回，其他int(...)仅捕获TypeError/ValueError/OverflowError并改成FusedLayoutContractError。维数首先比较：严格配置抛错，仅debug时告警并返回；debug模式另外追加日志。

维数相同后，**空Tensor直接跳过余下全部检查，包括dtype和device**。非空才比较完整size、仅实际size>1轴的stride、dtype及device.type；不是检查device index、storage_offset或底层容量。期望stride列表长度没有在此独立与rank核对，不能将任意错误元数据都说成会统一转为自定义布局错误。

debug日志保存时间/RANK（缺省0）和level，锁内append；OSError按路径只告警一次，其他异常不在这段吞掉。没有log_path直接不写。flag_line把生成期的bool配置烘入_enable_layout_check并保留运行期DEBUG判断；实际检查函数仍读取模块配置，不能把一次生成开关当成任意以后配置切换的完整刷新协议。

中央_emit_fused_layout_checks跳过fx_wrapper，针对真实输入TensorArg按buffer去重；合成transpose slot和没有stride的buffer跳过，输出没有在该helper逐个检查。首次生成import/flag，随后按layout.size/stride/dtype/device.type及Kernel的log路径调用；tuple helper保留一维尾逗号。检查结果是输入合同探针，不证明Kernel数值或所有路径正确。

## 关闭size_asserts仍需要绑定符号

根模块导入后明确调用_patch_input_symbol_binding。PythonWrapperCodegen.codegen_inputs被marker保护避免重复patch；非NPU或size_asserts本来开启时直接走原方法。NPU关闭时只在调用原codegen_inputs期间临时patch(size_asserts=True)，来源注释说明为保留符号赋值，后续size/NaN断言调用位于上下文外。注释提到Torch2.14行为，但本helper没有另写torch版本数值门控。

这不是让整个NPU执行都恢复尺寸断言。被patch的是外部Torch类，具体Torch版本的方法实现和全局patch并发语义仍需分别核验；本地marker只防重复包装，不是跨所有包的协调协议。

## 子图复合表达式只捕获自由符号，不反解

对codegen_subgraph和codegen_subgraph_with_flattened_outputs仅在方法存在时分别包装。_capture_subgraph_compound_symbols在外层V.graph非NPU、cpp_wrapper或fx_wrapper时直接返回原outer_inputs；其余扫描子图graph_inputs：纯Symbol作为已显式绑定，非纯scalar表达式及Tensor size/stride复合表达式贡献free_symbols，取required-explicit后按名字排序。storage_offset不在该扫描集合，代码没有反解欠定表达式。

每个缺失符号以graph.name_npu_input_symbol_i命名，冲突不断加下划线，再同时扩graph_inputs和graph_input_names；按graph对象缓存符号tuple，签名仅扩一次。每次调用都用wrapper.codegen_sizevar取外层真实值并创建新outer_inputs列表，避免修改switch两分支共享的原列表。缓存并未按以后graph内容变化自动失效；“补齐当前选定集合”不等于任意符号或控制流都已解决。

这两项合同分别保护实际布局观察和符号可用性，不能互相替代。完整调度、转置和调用参数顺序继续见[中央生成链](torchair_inductor_ascendc_schedule_codegen_wrapper.md)，本卡的根入口/npu.py只是所列范围证据，不新增对它们整文件的覆盖资格。

## 本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/fused_layout_check.py)（primary）：1–144。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/input_symbol_binding.py)（implementation）：1–129。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/__init__.py)（implementation）：1–35, 135–160。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py)（implementation）：2757–2832。
