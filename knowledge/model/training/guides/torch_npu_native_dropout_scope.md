---
type: Guide
title: 原生Dropout的NPU范围：类函数差异与950复数限制
description: 区分Dropout各入口dtype与950DT的complex例外，不从随机算子注册推定训练、捕获或零拷贝支持。并含 native_dropout_backward 的scale合同、p==0/p==1分支与主线950 aclnnDropoutV3Grad原始scale直发路及打包位掩码协议。
tags:
- task.implementation
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-functional.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-_npu_dropout.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-_npu_dropout.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-_npu_dropout.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NativeDropoutKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NativeDropoutKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_native_dropout_backward.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_native_dropout_backward.py
  role: example
created_at: '2026-11-09T10:19:09Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# 原生Dropout的NPU范围：类函数差异与950复数限制

## 固定版本与范围

依据TorchNPU固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 中PyTorch2.7.1、2.9至2.14的完整条目，产品为A2/A3训练系列与950DT，具体例外另列，不扩展950PR或发布组合。它们是同一提交中的分版本文档，不将差异直接当作已验证的发行历史。本卡只读审阅，没有执行上游、设备或性能实验。

使用Dropout时保留实际训练/推理状态、概率、随机性与反向需求，不能只按“模型在NPU”或某个父类名判断整组入口等价。以下是七版本条目一致的限制，不推导全部未列类型。

## 类与functional的不同清单

| 入口 | input清单 |
| --- | --- |
| nn.Dropout | BF16/FP16/FP32 |
| F.dropout | BF16、FP16/32/64、UINT8、INT8/16/32/64、BOOL、complex64/128 |
| nn.AlphaDropout、FeatureAlphaDropout | FP16/FP32 |
| F.alpha_dropout、feature_alpha_dropout | BF16、FP16/FP32、UINT8、INT8/16/32/64、BOOL、complex64/128；未列FP64 |
| nn.Dropout2d | FP16/FP32、INT64、BOOL |
| F.dropout2d | 一般表与F.dropout相同，950DT的复数例外见下文 |

类的窄表与functional的宽表保持分开，不因为实现可能相似就将父子、forward、原地与非原地参数全部合并。整数/BOOL被列出不代表输入能反向求导，某次推理调用成功也不证明训练随机分支有效。

## 950DT的复数例外

F.dropout1d明确950DT不支持complex；F.dropout2d一般dtype列表含complex64/128，但950DT专门段明确不支持它们。应先按具体产品求交集，不能只读取通用列表。Dropout1d类、Dropout3d类及F.dropout3d条目只列产品而无完整dtype细表，不能从没有重复复数限制推定全部复数路径已验证。

## 验证边界

核对实际入口、dtype、状态和选中Kernel，比较输出分布、梯度及模型整体效果；图捕获/重放还需匹配相应RNG协议，原生支持标记不独自证明捕获后会按预期更新随机数。

先区分CPU控制、已纳管fallback和真正数值Kernel，再比较数据转移、峰值及稳态时间。没有给出本地性能数字，不由名称、原地参数或dtype推断零分配/零拷贝。

- [激活函数数值边界](torch_npu_native_activation_precision.md)
- [RNN中的dropout参数限制](torch_npu_native_recurrent_constraints.md)

## 低层掩码与端点不能混用

[_npu_dropout API](../apis/torch_npu/legacy_dropout.md)的UINT8压缩掩码和默认Philox seed/offset是低层协议，无显式seed不表示不消费RNG。普通dropout端点可返回self；native_dropout端点clone及mask dtype在固定发布/主线不同，不把这些分支归纳为统一别名或BOOL掩码。底层图捕获与TorchAir产品图模式支持分别核验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md)（primary）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn-functional.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn-functional.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn-functional.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn-functional.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn-functional.md)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-functional.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-functional.md)（primary）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-_npu_dropout.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-_npu_dropout.md)（primary）

- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-_npu_dropout.md)（constraint）

- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NativeDropoutKernelNpuOpApi.cpp)（implementation）

- [固定来源 19](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NativeDropoutKernelNpuOpApi.cpp)（implementation）

## native_dropout_backward 的 scale 合同与主线 950 直发路

上文端点差异只覆盖前向native_dropout的clone/mask dtype。本节补齐`native_dropout_backward(grad_output, mask, scale)`（包装文件已列于本卡来源）的反向合同；主线与发布两版本差异按原文记录：

| 分支 | 主线d84e9b1（NativeDropoutKernelNpuOpApi.cpp 166–210） | 发布dedc3167（同文件154–171） |
| --- | --- | --- |
| scale合同 | TORCH_CHECK `scale==0 或 scale>=1`，原文"native_dropout_backward scale has to be 0 or greater than or equal to 1, but got "（主线与发布两版本同） | 同 |
| p==0（scale==1，无dropout） | 返回`grad_output.clone()`（主线与发布两版本同） | 同 |
| p==1（scale==0，全drop） | 返回`zeros(grad_output.sizes())`（主线与发布两版本同） | 同 |
| 空mask（主线） | 无命令，直接按mask.sizes()申请空输出 | —（发布无此段） |
| 950直发路（主线） | `GetSocVersion()>=Ascend950`（static一次性判定）且`aclnnDropoutV3Grad`符号可用时，**直发原始scale**；源码注释：为对齐GPU(H20)反向精度，内核以纯乘链`gradX = gradY * mask * scale`计算，避免算子内恢复`p = 1 - 1/scale`的额外浮点 | **无950分支**：DO_COMPATIBILITY(aclnnDropoutDoMask)→acl_op回退，其余走`op_api::npu_dropout_backward(grad,mask,p)`（传p非scale） |
| 符号缺失回退 | DO_COMPATIBILITY(aclnnDropoutDoMask, acl_op::native_dropout_backward) | 同 |

测试合同（`test/test_base_ops/test_native_dropout_backward.py`）：950用例断言scale==0→全零、scale==1→grad原值、以及**每字节8位的打包位掩码输入**（0xAA/0x55图案，CPU参考先展开为bool再对照）——即950路`aclnnDropoutV3Grad`消费打包位掩码而非逐元素bool张量，掩码布局协议与前向端点不同；910A/B fp32/fp16用例（`SupportedDevices(['Ascend910A','Ascend910B'])`）走展开bool掩码对照。发布版本测试文件为简版（无SupportedDevices/950分支用例，diff核实）。

边界：V3Grad设备侧未核对；测试未在本卡执行，分布与数值等价未验证；"对齐H20精度"是源码注释意图按原文记录，非实测结论；掩码打包协议不外推到其他dropout入口（上文低层掩码与端点不能混用小节边界保持）。

### native_dropout_backward 补充证据

- [test_native_dropout_backward.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_native_dropout_backward.py)（example）：全文124行；910A/B fp32/fp16用例、950 scale==0/==1/打包位掩码用例逐条读。
- [test_native_dropout_backward.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_native_dropout_backward.py)（constraint）：发布简版；diff确认无950分支用例。
- [NativeDropoutKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NativeDropoutKernelNpuOpApi.cpp)（implementation）：166–210；950分支+V3Grad直发+回退链（该文件已列本卡frontmatter来源，本节为其补行为小节）。
- [NativeDropoutKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NativeDropoutKernelNpuOpApi.cpp)（implementation）：154–171；发布侧完整backward函数体。
