---
type: Guide
title: Dynamo Guards 与后端：版本门槛和过滤失效边界
description: 区分前端重编译、Inductor 代码生成与 AOT Eager，明确过滤 Guard 不等于语义安全。
tags:
- task.debugging
- topic.compilation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/dynamo_frontend/guard_filter.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/compilation_backend/inductor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/compilation_backend/aot_eager.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/compilation_backend/aot_eager.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/dynamo_frontend/guard_filter.md
  role: constraint
created_at: '2026-11-09T02:15:26Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Dynamo Guards 与后端：版本门槛和过滤失效边界

## 证据与版本

依据 PyTorch 固定主线 ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，guard_filter_fn 的文档门槛是 PyTorch≥2.10.0 且 TorchNPU 配套，因此不适用于本仓 PyTorch2.8 发布组合。来源没有给 Inductor 各生成器的完整硬件矩阵，本卡为 draft、platforms 为空；不据主线示例承诺任意设备可用。

## 前端与后端分别判断

Dynamo Guards 决定是否复用编译产物，guard_filter_fn 属前端。Inductor 后端进行优化和代码生成；来源列出 Triton 默认、npu_backend="dvm" 和 "ascendc" 路线，依赖各自编译器及配套。aot_eager 保留捕获/AOT 自动微分流程、以 Eager 执行，不生成这些融合内核，适合帮助区分前端和优化后端问题。

Inductor 的 mode="reduce-overhead" 对应其 NPUGraph Tree 路线，不能与旧 TorchAir config.mode="reduce-overhead" 或独立 npugraph_ex 后端当作同一配置。前端文档表中列出某后端不意味着该后端已支持反向捕获；具体限制仍以对应后端为准。

## 过滤的正确性条件

过滤只是停止检查，不会自动生成兼容状态变化的新图。返回的布尔列表 True 保留、False 过滤；callback 对象字段和后端 options 的接入需以安装版本接口为准。先用 TORCH_LOGS=guards,recompiles 确定实际失效条件，不照抄按类型大范围过滤的示例。

若 None↔Tensor 改变 Python 分支、dtype/device/grad mode 改变语义，省掉对应 Guard 可能静默复用错误图。不能仅验证“没有重编译”就认为优化正确，也不能用一次输入相同的 parity 证明状态变化后安全。

## 验证

逐种相关状态比较相同状态下的 Eager 与编译结果，包含数值、dtype、device、requires_grad 和需要时的梯度；再统计 Guards/重编译。set_stance("fail_on_recompile") 只验证重编译行为，不验证输出。本次没有执行 PyTorch 编译或 NPU 测试。

- [TorchAir 后端边界](../../../concepts/frameworks/torchair_backend_boundaries.md)
- [捕获层的重捕获判断](../torchair/npugraph_ex_capture_controls.md)


## 用户指南的入口合同与未闭合示例

中英文总览把Dynamo、AOT Autograd、执行后端分层，给出fullgraph=False、dynamic=None、backend="inductor"、mode/options=None、disable=False的入口默认；总览称TorchNPU自7.3.0支持compile，不表示同版本已经支持本页所有现代选项。mode只列None/reduce-overhead且后者限Inductor。五种后端是Inductor、npugraphs、npugraph_ex、aot_eager和TorchAir-GE callable；字符串后端与Callable配置不混用。

aot_eager仍经过图捕获和AOT自动微分，以Eager执行而不做Triton/DVM/Ascend C融合生成，适合比较前端与优化后端。来源“性能相近”不等于严格零开销，也不保证通过它就排除所有算子/状态错误。示例缺少完整NPU适配初始化时应按真实环境补齐，不作为独立可运行脚本。

Guard回调文档列guard_type/name/is_global及可选value，返回与entries等长bool列表；字段和可选属性不能仅凭示例就当作所有PyTorch版本稳定ABI。英文后端表写npugraph，中文与后端专页写npugraphs；保留差异，不自行注册一个新别名。

示例按字典类、运行状态类、组合类型、变量名、全局项及内置helper六种方式过滤。覆盖面越广越需要证明状态不改变语义：例子在no_grad/enable_grad间切换却过滤GRAD_MODE，或在y=None/Tensor分支间过滤，均不能因不重编译就判正确。示例直接访问可选value也需要核对真实entry对象；不发布成通用回调配方。

三种unsafe helper分别面向内置Module、全部Module和全局guard，文档仅给名称与意图，不提供跨版本实现合同。fail_on_recompile、TORCH_LOGS=guards,recompiles和同状态Eager的数值/dtype/device/requires_grad/梯度检查分别验证不同事实。不能用单一atol=1e-5覆盖所有精度、状态和模型。该卡产品与实现缺口未消除，继续draft；引用的外部PyTorch章节未入库。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/dynamo_frontend/guard_filter.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/compilation_backend/inductor.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/compilation_backend/aot_eager.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/overview.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/compilation_backend/aot_eager.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/dynamo_frontend/guard_filter.md)（constraint）
