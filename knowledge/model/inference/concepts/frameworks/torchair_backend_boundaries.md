---
type: Concept
title: TorchAir 两类图后端：GE 转换与 npugraph_ex 捕获边界
description: 按固定主线区分 GE Converter、npugraph_ex 捕获、Meta 与函数化职责，以及单进程单设备和旧 reduce-overhead
  配置边界。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/overview.md
  role: supporting
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/graph_supported_apis.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/graph_supported_apis.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/compilation_backend/npugraph_ex.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/compilation_backend/npugraph_ex.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/compilation_backend/torchair_ge_backend.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/compilation_backend/torchair_ge_backend.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/infer_cases.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/infer_cases.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchAir 图后端职责

## 两条执行路径

GE 后端将 FX 算子转换为 Ascend IR，由 GE 编译、优化并执行；npugraph_ex 采用图捕获和重放，提供下沉调度及多流表达。两者均需要 PyTorch 图前端能描述算子，GE 还需要对应的 Ascend Converter。

自定义算子的 Eager 计算实现、Schema、Meta/符号推导和 In-place 函数化是不同交付件。Eager 能运行只完成其中一部分。后端的配置也须分别选择，不能把 GE CompilerConfig 直接当作 npugraph_ex options。

## 当前主线的限制

来源整体约束为每个进程使用一张 NPU；多进程可形成分布式作业。npugraph_ex 主要面向在线推理，来源未支持反向流程及随机算子 Capture；不能据此否认底层 NPUGraph 在其他接口下的训练能力。

来源说明 7.3.0 之后旧 `config.mode=reduce-overhead` 路线不再演进，建议使用独立 npugraph_ex 后端。这个迁移边界不能替代当前运行版本的入口检查。

## 验证与适用性

先建立同一软件环境下的 Eager 输出，再检查整图捕获、算子支持、输入状态和真实后端。分别测首次编译、重编译与稳态时延。本文描述固定主线的职责和限制；主线软件组合仍待核对，未做设备或性能实验。

## 版本入口

- [软件栈来源与适用性](ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## PyTorch入图名单与产品脚注

PyTorch固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的原生API入图页将列表定义为已验证可用于torch.compile图的集合，未列出的API仍可能支持，不能把缺失当成绝对不支持。该列表也不替代当前后端的Converter、Meta、mutation/函数化、执行模式和具体参数约束。

该页特别限制：A2/A3训练系列在PyTorch 2.7.1时，torch.device与torch.nn.functional.cross_entropy不支持入图；950DT的torch.nn.functional.scaled_dot_product_attention在页中列出的2.7.1、2.9.0、2.10.0、2.11.0、2.12.0、2.13.0、2.14.0均不支持入图。不能从总表出现API就忽略这些产品/版本脚注，也不能据未列2.8推定它在950支持。

SDPA原生入口的限制不等于所有专用Attention算子都不可成图；反过来，专用FusionAttention或Meta注册也不能证明原生SDPA路径支持。torch.compile名单不是任意CANN组合、所有dtype/shape、GE与捕获后端均一致的证明；主线与发布软件栈仍按各自配套证据处理。

## 入图与DTensor的全名单分别消费

同提交中英文原生附录的全部名称已按[两份清单的交集和差集](../../guides/optimization/torch_npu/torch_npu_native_graph_dtensor_capabilities.md)整理；142个共同名称不证明DTensor和某编译后端的联合组合已经验证。继续按本卡后端、参数、原地函数化和训练/推理边界核对，不用名称交集消除产品脚注。

## TorchNPU用户指南的跨仓入口不替代配套

PyTorch固定主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf中英文页给两种入口：npugraph_ex使用字符串后端，TorchAir-GE使用CompilerConfig/get_npu_backend生成callable，并明确先import torch_npu再import torchair、先保证同环境Eager正确。GE的CompilerConfig不直接当作npugraph_ex options。

npugraph_ex页要求判断replay时参数是否需更新，必要时使用update机制；仅有编译缓存或FX优化不能自动满足动态参数更新。样例标题出现训练/推理但实际循环只有forward，Guard表列训练也不覆盖固定TorchAir快照不支持反向与随机算子capture的独立限制；optimizer通常不入图的描述也不是任意其他step绝对不可编译的定理。

这两页链接指向TorchAir master，没有固定配套哈希；本库已有两份固定TorchAir来源应分别消费，不能将PyTorch主线2.14与TorchAir主线2.13强行配对，或回推26.0发布版。代码片段、1000次调用和服务化能力介绍不代表具体服务框架接入、缓存命中、整图或性能已经验证。

## 历史推理案例入口与当前模型配套

发布附录infer_cases只介绍面向推理服务的DeepSeek-R1分布式样例，要求了解Transformer/注意力与分布式，产品范围只列A2；其链接仍指向cann-recipes-infer的旧models/deepseek-r1路径，描述固定KV Cache、小算子替换融合算子等方法。这里摄入的是该历史入口事实，不将动态链接目标的全部内容计为已摄取。

本库已有[固定Recipes的R1 A3部署](../../guides/models/deepseek_r1_deployment.md)，它采用另一固定快照、目录和软件配套。旧A2入口不能证明该A3方案支持A2，也不据本次仓库固定版本自动更新外部示例的硬件与方法。

## Evidence

- [docs/zh/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（primary）
- [docs/zh/custom_op_graph/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/overview.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/graph_supported_apis.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/graph_supported_apis.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/compilation_backend/npugraph_ex.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/compilation_backend/npugraph_ex.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/compilation_backend/torchair_ge_backend.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/compilation_backend/torchair_ge_backend.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/infer_cases.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/infer_cases.md)（constraint）

- [完整页复核来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）
