---
type: Guide
title: 发布快照图接口：compile、FX、JIT、ONNX与export
description: 保留torch.compile与torch.compiler不同状态，区分图工具可用、设备编译和模型导出。
tags:
- task.lookup
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/api/torch_npu_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md
  role: constraint
created_at: '2026-11-09T17:27:10Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 发布快照图接口：compile、FX、JIT、ONNX与export

## 来源与版本缺口

依据PyTorch/TorchNPU发布快照f3ecfe4a7ef7395754da7ca2e35661a7132b519b内docs/api/torch_npu_apis.md。它位于锁定发布源码内，但页面没有逐项的PyTorch小版本、CANN/包post、产品或参数支持矩阵，不能仅由父提交推为26.0/PT2.8所有组合的运行保证；本卡保留draft、platforms为空，待独立版本/硬件证据消解。

原表Y表示该文件声称兼容，仍须看限制；兼容性留空明确表示尚未验证。空白不是显式不支持，Y也不是本知识库新增verified或完整模型验收。类、方法、原地形式和同名函数逐行消费，不按父类、别名、相邻项或主线其他版本补全；这里没有执行/导入上游、编译、启动进程或设备实验。

## 编译入口与工具不是同一支持层

torch顶层表将torch.compile标Y，但torch.compiler表6项、torch.export表15项和torch.func表13项均留空。不能由顶层入口推定allow_in_graph、disable、dynamic_dim、save/load、导出约束或func变换链均已验证，更不能据此选择TorchAir/Inductor/NPUGraphs后端或推断训练/动态shape支持。

FX的symbolic_trace、GraphModule/Graph/Node/Tracer/Proxy/Interpreter/Transformer及大量已列方法有Y，GraphModule.code/graph、Graph.nodes、Node.args/kwargs/stack_trace等属性与boxed_run留空。工具能构图、lint或生成Python不证明NPU编译/融合后端支持全部节点。torch.library的Library/define/impl为Y，fallthrough_kernel留空；注册前端不替代算子实现与autograd验收。

## TorchScript与ONNX保留各阶段

JIT trace/trace_module、script_if_tracing、freeze、optimize_for_inference、save/load及许多ScriptModule/ScriptFunction方法有Y，torch.jit.script本身、fork/wait、图/代码属性、compile与部分方法留空。不能从trace的Y推断script编译已验证，也不能把save/load表当任意包、跨设备或新后端产物兼容保证。

ONNX dynamo_export/export、ExportOptions/ExportOutput的部分转换/保存、符号注册、部分verification/JitScalarType/GraphInfo入口有Y；enable_fake_mode、OnnxRegistry及相关诊断/context/model_proto属性、is_onnxrt_backend_supported等留空。导出、导出结果验证、ONNX Runtime后端支持与NPU部署是不同环节；没有执行图生成、导出或加载。

[当前主线原生图支持](torch_npu_native_graph_support_scope.md)和[主线编译/导出](torch_npu_native_compiler_export_scope.md)来自另一提交/逐版本清单，不能与本表拼成发布版完整接口集。

## 所属表的证据范围

| 表 | Y条目 | 留空条目 | 有限制条目 |
| --- | --- | --- | --- |
| torch.library | 3 | 1 | 0 |
| torch.fx | 76 | 10 | 0 |
| torch.jit | 61 | 20 | 0 |
| torch.onnx | 38 | 13 | 0 |
| torch.compiler | 0 | 6 | 0 |
| torch.export | 0 | 15 | 0 |
| torch.func | 0 | 13 | 0 |

计数是该页目录记录数量，不是运行通过率；未给局部参数/默认值/组合条件时保持未知。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/api/torch_npu_apis.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md)（constraint）
