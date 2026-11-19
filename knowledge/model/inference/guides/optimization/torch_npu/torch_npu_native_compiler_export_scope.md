---
type: Guide
title: 原生编译与Export：入口清单和导出对象差异
description: 区分compiler控制入口、export/signature辅助类和英文ExportedProgram不支持标记，避免推定完整后端兼容。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-compiler.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-export.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-export.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-export.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-export.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-export.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-export.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-export.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-export.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-export.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-export.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-export.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-export.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-export.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-export.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/overview/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/overview/overview_arch.png
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/overview/inductor_arch.png
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/getting_started/getting_started.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/installation/installation.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/profiling/profiling_performance.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/profiling/trace.drawio.svg
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/troubleshooting/reporting_issues.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/aoti/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/megacache/overview.md
  role: primary
created_at: '2026-11-09T12:39:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生编译与Export：入口清单和导出对象差异

## 固定来源与适用范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14中英文支持页，逐项保留类、方法、函数与文档版本差异；不回推26.0/PyTorch2.8发布组合，也不从TorchNPU与TorchAir各自主线推定两者配套。产品按A2/A3训练系列与950DT条目区分，不扩展950PR。清单未收录不等于已证实不支持；未列出的参数与组合不自行补齐。本次仅静态审阅，未执行上游、导出、编译或设备实验。

## 编译控制入口不是完整后端矩阵

中英文七版本compiler页对compile、reset、allow_in_graph、assume_constant_result、list_backends、disable、set_stance列三类产品。中文还列cudagraph_mark_step_begin、is_compiling、is_dynamo_compiling；is_exporting只在同提交2.7.1、2.11..2.13中英文页收录，列三类产品。

这些是入口支持证据，不是任意backend/mode/fullgraph/dynamic、缓存和图捕获的完整合同；allow_in_graph、常量结果假设、禁用和重置会影响不同阶段，清单没有给出可安全删除guard或重用缓存的证明。Module.compile在原生NN页对950DT有独立不支持标记，不能由此处compile入口覆盖，见[Module方法范围](../../../../training/guides/torch_npu_native_module_and_container_scope.md)。

## Export公开入口与返回对象分开

两种语言七版本export页对export/save/load、register_dataclass，unflatten的FlatArgsAdapter及adapt、InterpreterModule/InterpreterModuleDispatcher/unflatten，decomp_utils.CustomDecompTable及copy/items/keys/materialize/pop/update，passes.move_to_device_pass列三类产品。graph_signature的InputKind/InputSpec/OutputKind/OutputSpec、SymBool/Float/IntArgument也列三类产品；这些元数据支持不证明任意动态约束或模型均能导出。

英文页却另把ExportedProgram及其module()在三类产品均标为不支持；中文未列该类。保留export入口和对象表之间的范围差异，不能因export可调用就宣传完整“导出→module→执行”流程已验证，也不自行猜测一侧表格错误。

2.7.1、2.9、2.10页以torch.export.ModuleCallEntry/ModuleCallSignature列条目，2.11..2.14移到exported_program命名空间，均列三类产品；这是文档路径差异，不直接证明运行时别名增删。英文旧三版本另列ExportGraphSignature/ExportBackwardSignature三类产品均不支持；Constraint仅英文2.7.1收录，三类产品均不支持。新版未列这些旧条目，不由缺项推定支持状态改变。

## 验收边界

固定实际包、入口、输入签名、约束、训练/推理和目标后端，分别检查捕获、序列化、恢复、对象方法及执行结果。支持清单、文件生成和实际设备执行是不同证据；不加载未知导出产物，也不把保存成功当作跨版本或跨产品可恢复。

- [TorchAir FX Pass的实际接入契约](../torchair/torchair_fx_pass_and_fusion_controls.md)
- [原生FX与符号形状的范围](torch_npu_native_fx_constraints.md)
- [原生ONNX导出与版本差异](torch_npu_native_onnx_scope.md)

## 内置Inductor组件和后端回退的限定流程

同提交内置总览约束950DT：Dynamo取得FX图后，由Inductor-Ascend完成图优化、lowering、scheduling融合及codegen，生成Triton/Catlass DSL，再经Triton-Ascend、AscendNPU-IR形成设备二进制。不能参与融合的ATen算子可回AclNN或手写Ascend C，这里的fallback不是CPU fallback的同义词。CPU路径可生成C++/OpenMP代码，不据此推定整个NPU模型全在Host。

两张已查看架构图补充Pass注册、NPUCombined/NPUTritonScheduling、索引线性化/cat重构/split_tiling_axis、多流、动态shape、CppWrapper/AOTI与MegaCache等层次；图上TorchRec、vLLM、模型名和A2/A3/A5/A6等生态标签只是架构背景，不覆盖正文950DT使用约束或证明这些模型/产品全已验证。具体四Pass改写及访存条件见[图改写](torch_npu_inductor_fx_rewrite_conditions.md)与[访存Lowering](torch_npu_inductor_memory_lowering.md)。完整外部库/Kernel没有因图中出现而全部摄取。

## 编译性能采证和问题材料

内部性能页用ModelWithBreaks的四段MLP和三处显式graph_break演示：先编译并热身一次，再用torch_npu.profiler.profile采若干迭代、step划步，导出Chrome trace。查看的轨迹中可见Torch-Compiled Region、CompiledFunction及设备流事件；它只是历史示意，不能从单张图给出本模型各段耗时或证明一次热身足以进入稳态。社区torch.profiler示例需按TorchNPU接口适配，不能与前述Autograd Profiler参数直接混用。

反馈定位材料包括TorchNPU、Triton-Ascend、CANN版本、最小源码和错误堆栈/截图，来源要求在Ascend/pytorch issue标题标[Inductor]；这里记录反馈格式，未发送issue或运行示例。依赖/版本与API参数分别按[软件栈](../../../concepts/frameworks/ascend_software_stack_baselines.md)和[Inductor参数页](../../../apis/torch_npu/torch_compile_inductor.md)核对，不据入口列支持推定所有模式与捕获缓存组合可用。

## AOTI和多级缓存各有产物限制

内部AOTI页明确950DT、通过export再aoti_compile_and_package生成pt2，Python/C++加载及libtorch_npu依赖见[AOTI部署](torch_npu_inductor_aoti_deployment.md)；这份能力说明与原生支持表中ExportedProgram对象的产品标记分层保留，不能由流程例子抹去后者的显式限制。

950DT MegaCache的save/load_cache_artifacts归档多级编译缓存，仍需正常compile查询命中，且暂不打包CppWrapper二进制；[接口及兼容条件](../../../apis/torch_npu/megacache_artifacts.md)与AOTI可在C++运行、分组调优可落盘不是同一承诺。[FlexAttention](torch_npu_inductor_flex_attention.md)和[并行调度](torch_npu_inductor_parallel_schedule.md)也各保留自己的版本/产品/梯度条件，不由架构图并列名称推导任意组合已支持。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-compiler.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-compiler.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-compiler.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-compiler.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-compiler.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-compiler.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-compiler.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-compiler.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-compiler.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-compiler.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-compiler.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-compiler.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-compiler.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-compiler.md)（constraint）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-export.md)（constraint）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-export.md)（constraint）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-export.md)（constraint）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-export.md)（constraint）
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-export.md)（constraint）
- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-export.md)（constraint）
- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-export.md)（constraint）
- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-export.md)（constraint）
- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-export.md)（constraint）
- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-export.md)（constraint）
- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-export.md)（constraint）
- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-export.md)（primary）
- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-export.md)（constraint）
- [固定来源 28](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-export.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/overview/overview.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/overview/overview_arch.png)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/overview/inductor_arch.png)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/getting_started/getting_started.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/installation/installation.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/profiling/profiling_performance.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/profiling/trace.drawio.svg)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/troubleshooting/reporting_issues.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/aoti/overview.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/megacache/overview.md)（primary）
