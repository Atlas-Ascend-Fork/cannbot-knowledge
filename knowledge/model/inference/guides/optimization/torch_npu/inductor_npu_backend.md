---
type: Guide
title: Inductor编译模式选择：值与首次编译时机
description: 记录TORCHINDUCTOR_NPU_BACKEND的三种文档模式、A2/A3及950DT范围和Ascend C版本门槛。
tags:
- task.lookup
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_NPU_BACKEND.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_NPU_BACKEND.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/compilation_backend/inductor.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/compilation_backend/inductor.md
  role: constraint
created_at: '2026-11-09T14:37:06Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# Inductor编译模式选择：值与首次编译时机

## 固定版本与接口

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的中英文TORCHINDUCTOR_NPU_BACKEND环境页，产品表列A2/A3训练系列和950DT，不扩展到其他产品或26.0/PyTorch2.8发布组合。它选择NPU上的Inductor编译模式，与TorchAir.get_npu_backend、GE CompilerConfig、npugraphs及GEMM候选实现名单分别处理。

| 环境值 | 文档模式 |
| --- | --- |
| 未配置或default | Triton |
| dvm | DVM |
| ascendc | Ascend C，要求PyTorch≥2.9.0 |

## 配置时机与边界

在首次torch.compile前设置即可，后端首次编译时惰性加载，所以import torch/import torch_npu之后配置也可生效；不能由此推断已加载后端能被任意同进程动态切换。其余调优变量可能需要导入前设置，不能共用一个读取时机。

页面仅承诺这三种模式，未给非法值的公开处理规则。源码注册的其他名字和回退分支不是此页额外支持声明，见[配置与加载源码草稿](torch_npu_inductor_config_parsing.md)。实际还需核对所需编译器、包与Kernel；设置字符串、注册后端或创建图不代表目标模型可编译或更快。

GEMM候选名单中的ATEN/TRITON/CATLASS是Kernel生成来源，不是此环境变量的三种模式；Catlass等950子能力见[矩阵乘调优指南](torch_npu_inductor_catlass_autotune.md)。本次只静态审阅，没有导入包、编译或设备实验。

## 用户指南的语言差异与生成结果身份

固定提交的用户指南两侧表都只列Triton、DVM和Ascend C三条路线，英文正文却称four；不能据此补出第四种公开模式。中文只说源码安装配套Triton-Ascend；英文还给旧安装说明，称仅PyTorch2.7.1/2.9.0，不能与主线2.14及内部安装页的其他范围拼为统一支持矩阵。包版本仍按各自固定来源配套核对。

用户页要求在import torch前配置环境，而专门环境页明确首次编译前惰性读取；提前设置是满足两者的使用方式，不能据此抹去读取时机差异或保证已加载后端可切换。options中的npu_backend只列dvm/ascendc，默认Triton，和公开环境值的层次按前文区分。

DVM的mlir_fusion复用Inductor-MLIR融合、graph_fusion走自定义图融合；这些是同一DVM模式内部路径，不是两个额外的TORCHINDUCTOR_NPU_BACKEND公开值。run_and_get_code与codes[0]显示生成代码，用于核对实际后端；示例的triton_poi/dvm_fused/autofused符号、设备0、固定stride和layout检查只是该样例产物，不能硬编码为稳定Kernel ABI或证明任意融合已命中。这里没有摄取DVM/Triton/Ascend C的Kernel生产实现。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_NPU_BACKEND.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_NPU_BACKEND.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/compilation_backend/inductor.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/compilation_backend/inductor.md)（constraint）
