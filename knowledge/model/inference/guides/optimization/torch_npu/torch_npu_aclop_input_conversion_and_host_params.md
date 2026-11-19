---
type: Guide
title: TorchNPU aclop 输入转换与 host 传参：aclTensorDesc/aclDataBuffer 构造面
description: 固定主线源级核对 OpCmdHelper 六条转换路径：NPU 输入用 storage 维度与 npu_format_、host 输入用逻辑
  sizes 加 placement、标量走 CopyScalarToDevice、输出同时携带 origin/当前格式。
tags:
- task.implementation
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCmdHelper.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCmdHelper.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCmdHelper.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCmdHelper.h
  role: implementation
created_at: '2026-11-13T05:22:15Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU aclop 输入转换与 host 传参：aclTensorDesc/aclDataBuffer 构造面

## 固定版本与范围

固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，整读 `torch_npu/csrc/framework/OpCmdHelper.cpp`（117 行）与 `.h`。静态阅读，未执行 aclop 下发。本卡只闭合 OpCmdHelper 自身的转换语义；其调用方（各算子的 aclop 执行路径）与 `CalcuOpUtil`/`AclTensorDescMaker`/`AclTensorBufferMaker` 的内部实现另行核对，不从本卡推导。

## 六条转换路径的分工

| 入口 | 输入形态 | desc 形状/格式来源 | 缓冲 |
| --- | --- | --- | --- |
| CovertTensorToAclInput | NPU 设备 tensor | `NpuStorageImplDesc.storage_sizes_` + `npu_format_`（NPUBridge 取存储描述） | 按 storage 元素数 × 元素大小 |
| CovertTensorWithZeroDimToAclInput | host 侧 0 维 tensor | 逻辑类型（wrapped number 保留传入 type），ACL_FORMAT_ND | `ConvertTensorToScalar` → `CopyScalarToDevice` 重新设备拷贝 |
| CovertNPUTensorWithZeroDimToAclInput | NPU 侧 0 维 tensor | tensor.scalar_type()，ACL_FORMAT_ND，可命名 | 原 tensor 直取 |
| CovertScalarToAclInput | 已拷到设备的标量 tensor | 传入 type，ACL_FORMAT_ND | 原 tensor 直取 |
| CovertHostTensorToAclInput | host tensor | 逻辑 `sizes()`，ACL_FORMAT_ND，placement 由 CompileType 映射 aclMemType | 按逻辑元素数 |
| CovertToAclOutput | 输出 tensor | `Create(aclDataType, dims, origin_format_)` + `SetFormat(npu_format_)` + `SetShape(storageDims)` | 按 storage 元素数 |

## 关键语义与排障点

**NPU 输入描述用 storage 维度而非逻辑形状**：desc 的 shape 取 `storage_sizes_`，buffer 大小按 storage 元素数计算；host 路径才用逻辑 `sizes()`。排障「下发的形状与 tensor.shape 不一致」时先核对存储描述（含格式带来的存储膨胀），不要按逻辑形状推断 acl desc。**输出描述同时携带两种格式**：`origin_format_` 作为 desc 创建格式、`npu_format_` 为 SetFormat 当前格式、shape 仍用 storage 维度——5 维格式类转换（如 NC1HWC0）的输出即依赖这组三元组合。**ACL_STRING 特例**：字符串 tensor 的 storageDims 置空，缓冲大小改按 `storage_sizes_` 推导（源注释：STRING size=1、storageDims=0 不能用于计算大小），该分支是唯一不走「desc shape == buffer 计数来源」一致性的路径。**0 维 host 标量每次重新设备拷贝**：`CopyScalarToDevice` 意味着 host 标量入参在下发前有真实 H2D 拷贝，不是引用原内存；wrapped number 按传入 type，普通 host 0 维 tensor 按自身 scalar_type。**forceDataType 覆盖链**：NPU 输入与 host 输入的 aclDataType 都经 `ConvertToAclDataType(scalarType, forceDataType)`，调用方可用 forceDataType 强制覆盖声明类型（例如以更高精度类型下发），覆盖只改 desc 声明，不改 buffer 内容与大小计算方式。

## 验证与失效边界

定向验证：5 维格式 tensor 输入/输出时打印 desc 的 shape/format 与 buffer 字节数、host 标量路径确认拷贝发生、forceDataType 下发后数值精度一致。本卡未执行上述实验；`CompileType → aclMemType` 的具体枚举对应、desc/buffer maker 的字段填充细节未逐行展开，需要时按 AclTensorDescMaker/AclTensorBufferMaker 源核对。本卡不承诺任何算子在这些路径上的正确性或性能收益。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCmdHelper.cpp)（primary），读取范围 1–117 全文。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCmdHelper.h)（implementation），读取范围 1–48 全文。

## 发布 pin 对照（f3ecfe4a）

本节结论来自发布 pin 孪生文件的逐文件比对（比对口径：sha256 → 去空白 → 全空白折叠 token → 注释剥离 token）。

### 等价绑定（结论对发布 pin 直接适用，行号锚不同）

- `torch_npu/csrc/framework/OpCmdHelper.cpp`：两 pin 逐字节一致。
- `torch_npu/csrc/framework/OpCmdHelper.h`（48 → 42 行）：acl 头 include 改 third_party 相对路径并整体重排版，成员函数签名集合一致；另发布版注释拼写 `covert`（主线 `convert`，与 OpCmdHelper.cpp 主线源注释拼写情况互为镜像，不影响代码语义）。

### Evidence（发布 pin 补绑）

- [发布孪生 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCmdHelper.cpp)（release-twin-binding）：两 pin 逐字节一致。
- [发布孪生 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCmdHelper.h)（release-twin-binding）：diff 级全文对照（include 路径+重排版）。


（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
