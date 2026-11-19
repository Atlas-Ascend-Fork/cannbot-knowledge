---
type: Guide
title: Dynamo NPU流上下文：FX set_stream节点与handler安装
description: 沿主线NpuStreamContextVariable闭合current_stream代理、enter/exit的set_stream节点与退出恢复，核对NpuInterface流接口、current_stream handler的条件alias与发布版安装差异。
tags:
- task.implementation
- topic.compilation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo_device.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/dynamo/trace_rule.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/dynamo/trace_rule.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_dynamo.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_dynamo_device.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py
  role: implementation
created_at: '2026-11-12T03:31:07Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Dynamo NPU流上下文：FX set_stream节点与handler安装

## 固定版本与安装链

核对PyTorch/TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf与发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b的torch_npu Dynamo流集成。主线不在import torch_npu时直接安装：add_dynamo_methods把各patch登记为按步安装，_DynamoPostImportFinder在torch._dynamo首次导入后触发_lazy_dynamo_setup，torch.compile的Inductor包装器构造（patch_inductor_wrapper的new_init）也会触发一次。步骤依次为device_interface（NpuInterface注册加current_stream handler）、user_defined_class_variable、stream_event_variable、npu_stream_context、builtin_variable，随后注册backends、trace_rules与graphsafe_rng；每步成功一次后幂等。发布版在torch_npu/__init__.py里import时直接调用_dynamo_register_interface_for_device()与_patch_npu_trace_rules()，add_dynamo_methods挂在_apply_class_patches内，其步骤表没有npu_stream_context与current_stream handler两项。[AscendC等级Guard](torch_npu_ascendc_dynamo_deterministic_level_guard.md)与[Dynamo Guards边界](dynamo_guards_and_backend_boundaries.md)已闭合初始化入口与Guard本身，本卡不重做。

## NpuStreamContextVariable在FX图里插什么节点

主线patch_npu_stream_context定义StreamContextVariable子类，并把Dynamo的TorchInGraphFunctionVariable handler表中get_interface_for_device("npu").stream（即torch_npu.npu.stream入口）指到它。追踪到with语句时先执行create：用tx.output.create_proxy("call_function", device_interface.current_stream, ...)在图中插一个current_stream()节点，包装成StreamVariable保存为current_stream；enter()在有流时插set_stream(self.stream)节点再委托super().enter；exit()先插set_stream(保存的current_stream)恢复节点再super().exit。因此FX图中的次序是current_stream → set_stream(目标流) → 图内其他节点 → set_stream(保存的流)，进出对称恢复；同文件还把Stream/Event变量的python_type改为真实运行时子类，并让id(event)可用，供这些NPU方法被内联追踪。

上游StreamContextVariable基类的enter/exit、AOTAutograd与Inductor对stream节点的消费不在本仓固定树内；本卡不据此推导运行时流恢复或并发正确性。

## NpuInterface的流接口与真实落点

NpuInterface把stream/current_stream/set_stream直接指向torch_npu.npu同名函数，注册覆盖"npu"与npu:0..31。stream返回StreamContext：eager下enter保存当前流、目标流在其他设备时先在该设备上下文里另存一份，再set_stream；exit按相反顺序恢复，两版token一致。set_stream是torch_npu._C._npu_setStream(stream_id, device_index, device_type)的薄包装，None直接返回；current_stream经_npu_getCurrentStream取三元组构造Stream对象。_set_stream_by_id显式为None（NPU不支持），get_raw_stream为_npu_getCurrentRawStream；maybe_exchange_device只返回原值不做设备交换。[设备与流迁移](torch_npu_native_device_stream_scope.md)另有产品级边界。

## current_stream handler是条件alias，没有本地fallback

主线register_npu_current_stream_handler只在torch.accelerator.current_stream已存在Dynamo handler时，把torch.npu.current_stream别名到同一handler；查不到就静默返回，不补本地实现。源码注释给出动机：自PyTorch 2.12起流操作成为一等编译原语，AOTAutograd不再从FX图剥离stream算子，未注册handler的StreamVariable会把None当SymInt传给C++并报"Expected 'int' but found 'NoneType'"。注释是来源内的说明，不构成本次运行验证；该函数与安装调用只在主线存在，发布版完全没有这一步。

## trace_rule表项与常量折叠

两版都把torch.npu.current_stream/default_stream/stream/set_stream、torch_npu.npu.utils.synchronize与torch_npu._C._npu_setStream/_npu_getCurrentStream等名字登记为TorchInGraphFunctionVariable，torch.npu.set_device登记为SkipFunctionVariable；先clear_lru_cache再把这些映射追加进torch_name_rule_map。current_device/get_device_properties/is_available登记常量折叠（current_device另加need_guards），_NPUDeviceProperties加入common_constant_types。主线额外登记torch_npu.npu.stream与torch_npu.npu.utils.stream两个名字及任务队列开关两个C绑定，发布没有。表项只声明这些名字在Dynamo中按对应Variable类型追踪，不能由表项推导无graph break、常量折叠必然发生或运行时流被正确恢复；SkipFunctionVariable也不是设备切换被跳过执行的证明。

## 采集与核验

排查多流模型编译问题时分别记录：上游torch版本（决定accelerator handler是否存在与stream算子是否一等化）、进入的接口名、FX图中current_stream/set_stream节点次序、handler alias是否命中、后端对流节点的实际消费。两仓主线配套未知，保持draft与空平台；未运行compile、capture或任何NPU流实验，不提供性能或verified记录。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py)（primary）：1–1177。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo_device.py)（implementation）：1–110。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/dynamo/trace_rule.py)（implementation）：1–103。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/dynamo/trace_rule.py)（implementation）：1–100。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_dynamo.py)（implementation）：307–346，另全文符号检索确认无NpuStreamContextVariable与register_npu_current_stream_handler。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_dynamo_device.py)（implementation）：1–90。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py)（implementation）：70–80、165–185、300–322。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py)（implementation）：179–290。
