---
type: Guide
title: GE 推导不一致：dtype、AllGather shape 与输出内存不足
description: 从首个 Meta/GE 推导分歧定位 dtype、rank 和输出字节数，避免直接扩大输出缓冲区。
tags:
- task.debugging
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/graph_failed_cases.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/graph_failed_cases.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/feature/single_op_output_verification.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/feature/single_op_output_verification_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/feature/单算子入图后输出校验和精度对比指导.md
  role: constraint
created_at: '2026-11-09T03:19:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# GE 推导不一致：dtype、AllGather shape 与输出内存不足

## 版本与任务

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`，本卡限定 A2/A3 推理。该提交属于 ascend_26_0_pt28 的固定来源组合；其他版本须核对实际接口。


## 比较的是契约而不只是节点名

当出现 op dtype is not same、Check output size failed 或 Transpose 的 perm 越过输入 rank，保留 TorchAir 和 GE 两份 Dump，逐节点比较 shape、dtype、布局和输出存储需求。报错节点可能只是首次检查失败，偏差可能来自上游推导。

## dtype 先分清三种原因

可能是 Meta 错、Meta 正确但 GE 算子不支持对应 dtype，或 GE 推导与期望不同。来源 FloorDiv 案例中，下游两输入分别为 FLOAT 和 INT64，偏差来自上游 floor：PyTorch 期望整数而 GE 推导为 float。适配 Converter 时按真实 Meta 契约处理类型转换；不是遇到 dtype 报错就统一 cast 到某一种类型。

## 输出内存不足也可能源于 Meta

来源 Check output size failed 案例里，PyTorch 侧按 4096 个 BF16 元素申请输出，GE 实际要求 4096 个 FP32 元素，故 8192 字节不足以承接输出；错误中还包含运行时的对齐要求。最终定位为自定义 Meta 错误声明 BF16，需修复正确的 FP32 输出 dtype。

不要直接扩大 buffer 或照抄错误里的对齐常数来掩盖推导不一致。先核对每个返回值的 shape×元素大小、布局/对齐需求以及 Meta 与 GE 的一致性；来源 rms_norm_backward 示例的参数梯度为 FP32，不是所有同名输出一律继承输入 dtype。

## AllGather shape 偏差可在后续 Transpose 暴露

来源案例中 TorchAir 期望 [4,256,5120]，GE HcomAllGather 推导为 [1024,5120]，随后 perm 中的维度 2 对二维输入非法。Converter 依照真实 output_size 插入 Reshape，使输出符合 PyTorch 契约，而非改错下游 transpose 或盲加一维。

该例的张量元素数相同；变形前仍须验证 rank 顺序、元素排列与通信接口语义，不能将所有集合通信结果都套用此 Reshape。

## 修复验收

比较最小输入、目标动态 shape 和真实多 rank 输入的 Meta/GE 规格；再验证输出数值、返回结构、输入 mutation 和重复调用。若两层推导已一致但仍内存不足，再调查实际分配、布局、别名和执行器。

- [GE TensorSpec、Cast 和控制边](ge_converter_tensor_and_control_edges.md)
- [集合通信入图](collective_communication_graph_contract.md)
- [入图失败分阶段定位](torchair_graph_failure_triage.md)


## 验证边界

保留相同输入、rank、软件栈和变更前后的证据，先检查输出及存储语义，再关闭调试配置复测。来源案例是定位参考，不能把单条报错视作根因证明。本文仅静态审阅，未执行上游代码或 NPU 实验。

- [软件栈版本与来源身份](../../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线案例复核

TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 仍保留FloorDiv类型分歧、BF16/FP32输出存储不符与AllGather二维/三维推导偏差三个案例；总览支持范围包括A2/A3/950推理。它们用于检查Meta与GE契约的一致性，不能据此断言950已复现相同故障，或将日志中的对齐字节数当作固定修复值。

自定义Meta需按实际算子的输出dtype、shape和符号关系构造结果。返回普通CPU Tensor的示例修复为meta设备；这不要求所有FakeTensor兼容实现都硬编码同一构造方式。通信后Reshape也必须保持真实元素顺序及输出协议，不能只因numel相同就改形状。

## 自动规格检查与数值比对分开

两个固定快照的feature指导将GE最终NetOutput与FX输出的shape/dtype自动比较，与借助msit做逐算子数值比较分开。FX规格来自Meta，GE规格来自对应InferShape/InferDataType；检查器能报不一致不证明任一方必然正确。整网先找原图/编译图中首个分歧，不能只改最终输出buffer。

原始dynamo_optimized_graph*.pbtxt可看[o]输出属性，编译后ge_onnx_*_PreRunAfterBuild.pbtxt可看output_desc_shape:N/dtype:N。指导以DUMP_GE_GRAPH=2、DUMP_GRAPH_LEVEL=2描述不记const值、不dump子图的诊断选择；不是全部数据不落盘或所有图层均覆盖的保证。

msit的get_ge_dump_config与get_fx_dump_config分别采GE/FX，compare的my-path/golden-path必须与真实产物对应。进一步用fusion_switch.json分别设GraphFusion/UBFusion的ALL:off做差分，仍按[融合控制](torchair_fx_pass_and_fusion_controls.md)保留必需规则例外。msit为外部依赖，本仓只摄取其指导，不声称其外部实现已入库；没有dump、加载张量或执行比较。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/graph_failed_cases.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/graph_failed_cases.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/feature/single_op_output_verification.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/feature/single_op_output_verification_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/feature/单算子入图后输出校验和精度对比指导.md)（constraint）
