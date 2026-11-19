---
type: Guide
title: TorchAir 精度与性能定界：分层对照和有效观测
description: 从 Eager、FX、GE 与捕获执行逐层定位，区分编译成本、稳态开销、融合和数据搬运。
tags:
- task.debugging
- topic.performance.analysis
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/accuracy_cases.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/performance_cases.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/accuracy_cases.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/performance_cases.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
created_at: '2026-11-09T02:14:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchAir 精度与性能定界：分层对照和有效观测

## 版本与范围

依据发布子模块 7c6c754bed00c86ffaaa2a45cb7ac2724f058013 的案例，选择 A2/A3 推理。msit 的安装和完整命令依赖其独立版本，不在本卡中从动态链接推定当前行为。本次仅静态核对。

## 精度对照

先验证相同输入下 CPU/NPU Eager 是否正确；再用 FX Eager 对照排查 Dynamo/Meta；将单算子独立成图，最后定位局部结构/整网 GE 变换。GE 可选择性关闭融合排查，但 ALL:off 不保证关闭所有规则。保存相同 token、rank、参数与输入的产物，再做逐节点比较，避免将错位的数据当作首个误差点。

## 性能分层

先区分首次成图/编译与稳态运行。对重复编译比较 FX 图和 Guards；对稳态 Host 空洞区分前端框架、Dynamo guard/cache、TorchAir 输入转换与 GE 执行。标量/List 转 Tensor、非连续输入 contiguous/clone 都可能增加 Host 开销。

Device 差异需先核对实际算子、数量、dtype/shape/属性和 Kernel 路线；相同 ATen 名称不保证 Eager 与 GE 使用同一 CANN 算子。不能直接把不同输入或不同映射的耗时作为图模式收益。

## 采集产物

torch_npu.profiler.profile 的 CPU activity 对应框架，NPU activity 对应 CANN/设备。trace_view.json 看关联时间线，kernel_details.csv 看 Kernel，api_statistic.csv 在 Level1/2 下看 CANN API，operator_details.csv 依赖 CPU activity 与 record_shapes。文件缺失先核对采集配置，不能直接判定相关开销为零。

## 验证闭环

保留同负载、同软件组合的 Eager 与图模式对照，先确认输出与别名，再按问题选择小范围采集；关闭 Dump 和高成本调试设置后复测稳态收益。来源示例包含占位模型与设备代码，不能直接复制当作已验证基准。

- [框架原生 Profiler 采集与调度](torch_npu_profiler_capture_schedule.md)
- [GE 图结构与 Eager 定界](torchair_graph_dump_and_run_eagerly.md)

## 编译失败与融合专门诊断

- [入图失败的阶段与交付件检查](../torchair/torchair_graph_failure_triage.md)
- [GE dtype、shape 和输出存储偏差](../torchair/ge_shape_dtype_failure_diagnosis.md)
- [SuperKernel 主线的融合与性能分析](../torchair/superkernel_performance_diagnosis.md)

这些入口分别保留发布子模块或主线来源，不因本卡引用而改变各自版本范围。

## 主线精度产物的对齐

TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的精度与性能案例保留上述分层方法，总览列A2/A3/950推理。这里摄入的是固定TorchAir页面中的诊断契约，没有审阅或安装外部msit；页面引用msit 26.0.0不构成本仓三组件组合的运行兼容证明。

页面示例分别用msit_llm.dump.torchair_dump.get_ge_dump_config(dump_path=...)与get_fx_dump_config()生成配置，再交给TorchAir后端编译。后者仍是经FX的对照路径，不能代替完全绕开Dynamo的原生NPU Eager对照。

|产物|案例中的路径/身份|比对时检查|
|--|--|--|
|GE图与数据|dump_path/dump_时间戳，含算子数据目录及original/optimized图文本|选定同一次执行、graph、rank与输入|
|FX数据|data_dump/token_id/gm_时间戳_dump，npy文件|案例FX token从1开始，GE从0开始；按对应token对齐，不能直接同编号比较|
|比对结果|案例命令msit llm compare的golden-path对应FX、my-path对应GE|不能将未对齐的prefill/decode或不同rank当作首个精度差异|

目录与命令属于该页面示例；工具版本变化后需核对实际产物。先找首个真实偏差节点，再核对输入、dtype、融合及局部结构；关闭某条融合后恢复只能缩小范围，不证明所有融合都已关闭。

## 主线性能案例的归因边界

案例以npu_fx_compiler_inference、TorchNpuGraphBase::Run和ExecuteGraph等事件辅助区分前端guard/cache、TorchAir输入转换和GE下发。事件名和嵌套关系应以实际trace为准，不能把包含子事件的区间耗时相加，或把Host异步下发结束当作Device执行结束。

Eager的select可能映射StridedSlice，而GE图映射GatherV2；动态场景也可能把一个前端算子展开成多个设备算子。因此先比映射、数量、shape/dtype/属性，再比较对应Kernel和完整区间。重复编译先比多次FX图及guard，首次编译过慢再按编译阶段日志定位。

页面采集代码的设备选择仍是cuda/CPU分支，且插图明确是与代码不完全匹配的示意；不能原样当作NPU性能基准。关闭高成本采集后另测稳态耗时，本卡未得到NPU性能结果。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/accuracy_cases.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/performance_cases.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/accuracy_cases.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/performance_cases.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
