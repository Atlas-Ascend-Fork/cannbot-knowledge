---
type: Guide
title: 原生ONNX：导出版本、Program子方法与CPU验证
description: 区分旧导出入口、2.9迁移说明、ONNXProgram类与方法支持、差异直方图在CPU执行的边界，以及ONNX Scatter 导出映射 npu_scatter（ACE ArgMaxGrad 命令复用）。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-onnx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-onnx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-onnx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-onnx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-onnx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-onnx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-onnx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-onnx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-onnx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-onnx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-onnx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-onnx.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-onnx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-onnx.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ScatterV1KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ScatterV1KernelNpu.cpp
  role: implementation
created_at: '2026-11-09T12:39:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生ONNX：导出版本、Program子方法与CPU验证

## 固定来源与适用范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14中英文支持页，逐项保留类、方法、函数与文档版本差异；不回推26.0/PyTorch2.8发布组合，也不从TorchNPU与TorchAir各自主线推定两者配套。产品按A2/A3训练系列与950DT条目区分，不扩展950PR。清单未收录不等于已证实不支持；未列出的参数与组合不自行补齐。本次仅静态审阅，未执行上游、导出、编译或设备实验。

## 导出和Program分层

中英文七版本对export、OnnxExporterError、register/unregister_custom_op_symbolic、select_model_mode_for_export、is_in_onnx_export列三类产品。ONNXProgram类中文仅列A2/A3，英文明确950DT不支持；而model_proto/save/initialize_inference_session/release/optimize等子方法又列三类产品，apply_weights在部分旧页单列同名类块。保存这些层级差异，不能据子方法表声称整个Program生命周期已在950支持。

2.9/2.10的主要类块没有apply_weights，另有独立apply_weights块；2.7.1主块列compute_values，2.11..2.13列apply_weights与compute_values，2.14主块未列compute_values。不同块/版本合起来不是一份任意安装包的统一方法集合，也不由未列项直接断言运行时删除。

## 版本迁移说明的来源

同提交2.9/2.10中英文导言说明旧Dynamo导出与ONNX Runtime后端接口自2.9移除，export默认dynamo=True。英文这两页及2.14的单接口说明还写register/unregister_custom_op_symbolic属于已弃用的旧TorchScript辅助入口，推荐新export流程；select_model_mode_for_export已弃用，导出前设置模型训练/推理模式。其他版本/中文对应位置未重复全部说明，不能把一页的默认值和弃用范围无条件回推所有版本。

仅2.7.1页列dynamo_export（input仅FP32）、ExportOptions、OnnxRegistry及get_op_functions/is_registered_op/opset_version/register_op，产品列三类；DiagnosticOptions中文仅列950DT、英文明确A2/A3不支持而950DT支持；is_onnxrt_backend_supported中文仅列A2/A3、英文明确950DT不支持。英文同版enable_fake_mode三类均不支持，中文未列。旧入口支持不证明新版本仍保留，后端探测入口支持也不证明实际安装了运行时。

2.7.1的JitScalarType及dtype/onnx_compatible/onnx_type/scalar_name/torch_name等列三类产品。from_dtype中英文只列input BOOL；英文from_value也列BOOL，中文from_value只列产品，中文另列from_onnx_type支持。保留方法和语言的粒度，不将BOOL限定推广成所有ONNX模型只能布尔输入。

## 验证工具与CPU执行

verify_onnx_program列三类产品；中文2.14等页另列VerificationInfo及from_tensors，并明确from_tensors通过.cpu()把输入复制到CPU再计算差异直方图，NPU输入不保证差异计算在NPU执行。这不是模型图本身必然回退CPU的证据。

2.7.1另列GraphInfo/GraphInfoPrettyPrinter/VerificationOptions、check_export_model_diff/find_mismatch/verify/verify_aten_graph的三类产品支持，新页未列这些旧条目，不将缺项拼成跨版本验证流程。清单未给opset、动态shape、自定义算子或ONNX Runtime执行提供程序的完整兼容矩阵。

## 验收

固定PyTorch/导出器/运行时、opset、模式、shape和实际设备，分别核对导出对象、图节点、验证中的拷贝及目标运行时结果，再测量端到端开销。文档列支持、产物生成与真实NPU执行要有独立证据；本次未导出或加载任何模型。

## 总览中的默认值与动态形状迁移

同提交2.9/2.10两语言总览再次列出被移除的旧导出器、选项、注册表及旧验证入口，给出export与verify_onnx_program替代路线；2.9起export默认dynamo=True，需要旧TorchScript行为时显式False。2.10两侧另明确dynamic_axes废弃，新导出流程使用dynamic_shapes。这是所指文档版本的迁移说明，不补齐未给出的动态维度、opset或NPU执行契约，也不回推2.7.1默认值。

## ONNX Scatter 导出映射 npu_scatter

torch_npu 两 pin 的 `onnx/wrapper_onnx_ops.py` 提供 `_wrapper_npu_scatter`，把 ONNX Scatter 导出映射到 `torch.ops.npu.npu_scatter(self, indices, updates, dim)`（相邻还有 `npu_scatter_nd_update` 映射）。op-plugin 侧实现 `ScatterV1KernelNpu.cpp`（30 行，两 pin 去空白等价，完整来源核对）：`apply_tensor(self)` 同形输出后发 ACE 命令 **`ArgMaxGrad`**（复用该 ACE 算子承载 scatter 语义，`dimension` 属性传 dim）——命令名与语义无关，ONNX 导出链路排障时不能按命令名推断行为。npu_scatter 本身非 exposed、无 op_api 登记、无文档页，仅由 ONNX wrapper 消费。设备侧 ArgMaxGrad 承载 scatter 的数值语义不在本卡范围；ONNX 符号版本覆盖面未展开。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-onnx.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-onnx.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-onnx.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-onnx.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-onnx.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-onnx.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-onnx.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-onnx.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-onnx.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-onnx.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-onnx.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-onnx.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-onnx.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-onnx.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/overview.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/overview.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/overview.md)（constraint）

- [ScatterV1KernelNpu.cpp 两 pin](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ScatterV1KernelNpu.cpp)（implementation）：全文 30 行（本轮）；发布去空白等价。
- torch_npu 两 pin `torch_npu/onnx/wrapper_onnx_ops.py` `_wrapper_npu_scatter`（560/571/1204 行附近，符号定位）。
